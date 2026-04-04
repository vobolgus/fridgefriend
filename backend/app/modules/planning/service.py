# pyright: reportAny=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.inventory_item import InventoryItem, InventoryStatus
from app.models.meal_plan import MealPlan, MealPlanDay
from app.models.recipe import Recipe
from app.models.user import User

from .planner import MealPlanner
from .reservation import ReservationService
from .schemas import PlanDay, PlanRequest, PlanResult, RecipeIngredient, ShoppingListResponse
from .shopping_list import derive_shopping_list


class MealPlanNotFoundError(Exception):
    pass


class PlanningService:
    def __init__(self, session: AsyncSession, planner: MealPlanner | None = None) -> None:
        self._session: AsyncSession = session
        self._planner: MealPlanner = planner or MealPlanner()
        self._reservation_service: ReservationService = ReservationService(session)

    async def generate_plan(self, user: User, household_id: UUID, request: PlanRequest) -> PlanResult:
        inventory_items = await self._list_active_inventory(user.id, household_id)
        recipes = await self._list_recipes()
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
            dietary_tags=request.dietary_tags,
            max_prep_minutes=request.max_prep_minutes,
            recipes_db=planner_input,
        )

        meal_plan = MealPlan(
            user_id=user.id,
            household_id=household_id,
            start_date=planned.days[0].date,
            end_date=planned.days[-1].date,
            days=[
                MealPlanDay(
                    date=day.date,
                    recipe_id=UUID(day.recipe_id),
                    servings=request.servings,
                )
                for day in planned.days
            ],
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
            plan_id=str(meal_plan.id),
            days=[
                PlanDay(
                    date=day.date,
                    recipe_id=day.recipe_id,
                    recipe_title=day.recipe_title,
                    servings=request.servings,
                    reserved_items=day.reserved_items,
                    recipe_ingredients=day.recipe_ingredients,
                )
                for day in planned.days
            ],
            shopping_list=derive_shopping_list(planned, inventory_items, reserved_quantities=reserved_by_others),
        )

    async def get_shopping_list(self, user: User, household_id: UUID) -> ShoppingListResponse:
        meal_plan = await self._get_latest_meal_plan(user.id, household_id)
        inventory_items = await self._list_active_inventory(user.id, household_id)
        plan = PlanResult(
            plan_id=str(meal_plan.id),
            days=[
                PlanDay(
                    date=day.date,
                    recipe_id=str(day.recipe_id),
                    recipe_title=day.recipe.title if day.recipe else "Unknown Recipe",
                    servings=day.servings,
                    reserved_items=[
                        self._get_recipe_ingredient_name(ingredient)
                        for ingredient in (day.recipe.ingredients if day.recipe else [])
                    ],
                    recipe_ingredients=[
                        RecipeIngredient.model_validate(ingredient)
                        for ingredient in (day.recipe.ingredients if day.recipe else [])
                    ],
                )
                for day in meal_plan.days
            ],
            shopping_list=[],
        )
        reserved_by_others = await self._reservation_service.reserved_quantities_by_ingredient(
            household_id=household_id,
            exclude_plan_id=meal_plan.id,
        )
        return ShoppingListResponse(items=derive_shopping_list(plan, inventory_items, reserved_quantities=reserved_by_others))

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

    async def _list_active_inventory(self, user_id: UUID, household_id: UUID | None = None) -> list[InventoryItem]:
        statement = (
            select(InventoryItem)
            .where(
                InventoryItem.user_id == user_id,
                InventoryItem.status == InventoryStatus.ACTIVE,
            )
            .order_by(InventoryItem.estimated_expiry_date.asc(), InventoryItem.created_at.asc())
        )
        if household_id is not None:
            statement = statement.where(InventoryItem.household_id == household_id)
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def _list_recipes(self) -> list[Recipe]:
        statement = select(Recipe).order_by(Recipe.created_at.asc())
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def _get_latest_meal_plan(self, user_id: UUID, household_id: UUID | None = None) -> MealPlan:
        statement = (
            select(MealPlan)
            .options(selectinload(MealPlan.days).selectinload(MealPlanDay.recipe))
            .where(MealPlan.user_id == user_id)
            .order_by(MealPlan.created_at.desc())
        )
        if household_id is not None:
            statement = statement.where(MealPlan.household_id == household_id)
        result = await self._session.execute(statement)
        meal_plan = result.scalars().first()
        if meal_plan is None:
            raise MealPlanNotFoundError
        return meal_plan
