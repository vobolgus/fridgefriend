# pyright: reportAny=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownParameterType=false, reportMissingImports=false

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.inventory_item import InventoryItem, InventoryStatus
from app.models.meal_plan import MealPlan, MealPlanDay
from app.models.recipe import Recipe
from app.models.shopping_list_item import ShoppingListItem
from app.models.user import User

from .planner import MealPlanner, NoMatchingRecipesError
from .reservation import ReservationService
from .schemas import (
    PlanDay,
    PlanRequest,
    PlanResult,
    RecipeIngredient,
    ShoppingItem,
    ShoppingListItemCreate,
    ShoppingListResponse,
)
from .shopping_list import derive_shopping_list, merge_shopping_list_items


class MealPlanNotFoundError(Exception):
    pass


class PlanningService:
    def __init__(self, session: AsyncSession, planner: MealPlanner | None = None) -> None:
        self._session: AsyncSession = session
        self._planner: MealPlanner = planner or MealPlanner()
        self._reservation_service: ReservationService = ReservationService(session)

    async def generate_plan(self, user: User, household_id: UUID, request: PlanRequest) -> PlanResult:
        inventory_items = await self._list_active_inventory(household_id, for_update=True)
        recipes = await self._list_recipes()
        recipes_by_id = {str(recipe.id): recipe for recipe in recipes}
        planner_input: list[dict[str, object]] = [
            {
                "id": str(recipe.id),
                "title": recipe.title,
                "prep_minutes": recipe.prep_minutes,
                "dietary_tags": recipe.dietary_tags,
                "ingredients": [
                    {
                        "canonical_name": ingredient.get("canonical_name") or ingredient.get("name"),
                        "quantity": ingredient.get("quantity", 0.0),
                        "unit": ingredient.get("unit", "unit"),
                    }
                    for ingredient in recipe.ingredients
                ],
            }
            for recipe in recipes
        ]
        planned = self._planner.generate_plan(
            inventory_items,
            days=request.days,
            servings=request.servings,
            dietary_tags=request.dietary_tags,
            max_prep_minutes=request.max_prep_minutes,
            recipes_db=planner_input,
        )

        try:
            plan_days = [
                MealPlanDay(
                    date=day.date,
                    recipe_id=UUID(day.recipe_id),
                    servings=request.servings,
                )
                for day in planned.days
            ]
        except ValueError as exc:
            raise NoMatchingRecipesError(
                "Planner returned invalid recipe id",
            ) from exc

        meal_plan = MealPlan(
            user_id=user.id,
            household_id=household_id,
            start_date=planned.days[0].date,
            end_date=planned.days[-1].date,
            days=plan_days,
        )
        try:
            self._session.add(meal_plan)
            await self._session.flush()
            await self._session.refresh(meal_plan, attribute_names=["days"])
            await self._reservation_service.reserve_plan(meal_plan, planned, inventory_items)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

        reserved_by_others = await self._reservation_service.reserved_quantities_by_ingredient(
            household_id=household_id,
            exclude_plan_id=meal_plan.id,
        )

        return PlanResult(
            planId=str(meal_plan.id),
            days=[
                self._build_plan_day(
                    date=day.date,
                    recipe_id=day.recipe_id,
                    recipe_title=day.recipe_title,
                    servings=request.servings,
                    reserved_items=day.reserved_items,
                    recipe_ingredients=day.recipe_ingredients,
                    recipe=recipes_by_id.get(day.recipe_id),
                )
                for day in planned.days
            ],
            shoppingList=derive_shopping_list(planned, inventory_items, reserved_quantities=reserved_by_others),
        )

    async def get_latest_plan(self, user: User, household_id: UUID) -> PlanResult:
        _ = user
        meal_plan = await self._get_latest_meal_plan(household_id)
        return PlanResult(
            planId=str(meal_plan.id),
            days=[
                self._build_plan_day(
                    date=day.date,
                    recipe_id=str(day.recipe_id),
                    recipe_title=day.recipe.title if day.recipe else "Unknown Recipe",
                    servings=day.servings,
                    reserved_items=[
                        self._get_recipe_ingredient_name(ingredient)
                        for ingredient in (day.recipe.ingredients if day.recipe else [])
                    ],
                    recipe_ingredients=[],
                    recipe=day.recipe,
                )
                for day in meal_plan.days
            ],
            shoppingList=[],
        )

    async def get_shopping_list(self, user: User, household_id: UUID) -> ShoppingListResponse:
        _ = user
        inventory_items = await self._list_active_inventory(household_id)
        manual_items = await self._list_manual_shopping_items(household_id)
        manual_as_shopping_items = [
            ShoppingItem.model_validate(
                {
                    "ingredientName": item.name,
                    "quantity": item.quantity if item.quantity is not None else 0.0,
                    "unit": item.unit if item.unit is not None else "",
                    "reason": "manual item",
                }
            )
            for item in manual_items
        ]

        try:
            meal_plan = await self._get_latest_meal_plan(household_id)
        except MealPlanNotFoundError:
            return ShoppingListResponse(items=manual_as_shopping_items)

        plan = PlanResult(
            planId=str(meal_plan.id),
            days=[
                self._build_plan_day(
                    date=day.date,
                    recipe_id=str(day.recipe_id),
                    recipe_title=day.recipe.title if day.recipe else "Unknown Recipe",
                    servings=day.servings,
                    reserved_items=[
                        self._get_recipe_ingredient_name(ingredient)
                        for ingredient in (day.recipe.ingredients if day.recipe else [])
                    ],
                    recipe_ingredients=[
                        RecipeIngredient.model_validate(
                            {
                                **ingredient,
                                "quantity": float(ingredient.get("quantity", 0.0))
                                * (day.servings / MealPlanner.DEFAULT_BASE_SERVINGS),
                            }
                        )
                        for ingredient in (day.recipe.ingredients if day.recipe else [])
                    ],
                    recipe=day.recipe,
                )
                for day in meal_plan.days
            ],
            shoppingList=[],
        )
        reserved_by_others = await self._reservation_service.reserved_quantities_by_ingredient(
            household_id=household_id,
            exclude_plan_id=meal_plan.id,
        )
        derived_items = derive_shopping_list(plan, inventory_items, reserved_quantities=reserved_by_others)
        return ShoppingListResponse(items=merge_shopping_list_items(derived_items, manual_as_shopping_items))

    async def add_manual_shopping_list_items(
        self,
        *,
        items: list[ShoppingListItemCreate],
        household_id: UUID,
        user_id: UUID,
        idempotency_key: str,
    ) -> list[ShoppingListItem]:
        existing_items = await self._list_manual_items_by_idempotency(household_id, idempotency_key)
        if existing_items:
            return existing_items

        recipe_ids = {item.recipe_id for item in items if item.recipe_id is not None}
        if recipe_ids:
            result = await self._session.execute(select(Recipe.id).where(Recipe.id.in_(recipe_ids)))
            found_ids = set(result.scalars().all())
            missing_ids = recipe_ids - found_ids
            if missing_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Recipe(s) not found: {sorted(str(recipe_id) for recipe_id in missing_ids)}",
                )

        created: list[ShoppingListItem] = []
        for index, item in enumerate(items):
            manual_item = ShoppingListItem(
                household_id=household_id,
                name=item.name,
                quantity=item.quantity,
                unit=item.unit,
                recipe_id=item.recipe_id,
                created_by_user_id=user_id,
                idempotency_key=f"{idempotency_key}:{index}",
            )
            self._session.add(manual_item)
            created.append(manual_item)

        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            replayed_items = await self._list_manual_items_by_idempotency(household_id, idempotency_key)
            if replayed_items:
                return replayed_items
            raise

        for item in created:
            await self._session.refresh(item)
        return created

    async def delete_plan(self, plan_id: UUID, user: User, household_id: UUID) -> None:
        statement = select(MealPlan).where(
            MealPlan.id == plan_id,
            MealPlan.user_id == user.id,
            MealPlan.household_id == household_id,
        )
        meal_plan = (await self._session.execute(statement)).scalar_one_or_none()
        if meal_plan is None:
            raise MealPlanNotFoundError

        await self._session.delete(meal_plan)
        await self._session.commit()

    @staticmethod
    def _get_recipe_ingredient_name(ingredient: Mapping[str, object]) -> str:
        return str(ingredient.get("canonical_name") or ingredient.get("name") or "")

    @staticmethod
    def _build_plan_day(
        *,
        date: date,
        recipe_id: str,
        recipe_title: str,
        servings: int,
        reserved_items: list[str],
        recipe_ingredients: list[RecipeIngredient],
        recipe: Recipe | None,
    ) -> PlanDay:
        return PlanDay(
            date=date,
            recipeId=recipe_id,
            recipeTitle=recipe_title,
            prepMinutes=recipe.prep_minutes if recipe else None,
            imageUrl=recipe.image_url if recipe else None,
            servings=servings,
            reservedItems=reserved_items,
            recipeIngredients=recipe_ingredients,
        )

    async def _list_active_inventory(
        self,
        household_id: UUID | None = None,
        *,
        for_update: bool = False,
    ) -> list[InventoryItem]:
        statement = select(InventoryItem).where(
            InventoryItem.status.notin_([InventoryStatus.USED, InventoryStatus.DISCARDED]),
        )
        if for_update:
            statement = statement.with_for_update()
        statement = statement.order_by(InventoryItem.estimated_expiry_date.asc(), InventoryItem.created_at.asc())
        if household_id is not None:
            statement = statement.where(InventoryItem.household_id == household_id)
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def _list_recipes(self) -> list[Recipe]:
        statement = select(Recipe).order_by(Recipe.created_at.asc())
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def _list_manual_shopping_items(self, household_id: UUID) -> list[ShoppingListItem]:
        statement = (
            select(ShoppingListItem)
            .where(
                ShoppingListItem.household_id == household_id,
                ShoppingListItem.is_purchased.is_(False),
            )
            .order_by(ShoppingListItem.created_at.asc(), ShoppingListItem.id.asc())
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def _list_manual_items_by_idempotency(
        self,
        household_id: UUID,
        idempotency_key: str,
    ) -> list[ShoppingListItem]:
        statement = (
            select(ShoppingListItem)
            .where(
                ShoppingListItem.household_id == household_id,
                or_(
                    ShoppingListItem.idempotency_key == idempotency_key,
                    ShoppingListItem.idempotency_key.startswith(f"{idempotency_key}:"),
                ),
            )
            .order_by(ShoppingListItem.created_at.asc(), ShoppingListItem.id.asc())
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def _get_latest_meal_plan(self, household_id: UUID | None = None) -> MealPlan:
        statement = (
            select(MealPlan)
            .options(selectinload(MealPlan.days).selectinload(MealPlanDay.recipe))
            .order_by(MealPlan.created_at.desc())
        )
        if household_id is not None:
            statement = statement.where(MealPlan.household_id == household_id)
        result = await self._session.execute(statement)
        meal_plan = result.scalars().first()
        if meal_plan is None:
            raise MealPlanNotFoundError
        return meal_plan
