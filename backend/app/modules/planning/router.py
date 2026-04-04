# pyright: reportAny=false

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.idempotency import get_cached, store_cached
from app.models.user import User
from app.modules.inventory.dependencies import get_active_household_id, get_current_user

from .schemas import PlanRequest, PlanResult, ShoppingListResponse
from .service import MealPlanNotFoundError, PlanningService

router = APIRouter(tags=["planning"])


async def get_planning_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlanningService:
    return PlanningService(db)


@router.post("/v1/plans", response_model=PlanResult, response_model_by_alias=True)
async def create_plan(
    payload: PlanRequest,
    planning_service: Annotated[PlanningService, Depends(get_planning_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    household_id: Annotated[UUID, Depends(get_active_household_id)],
    request: Request,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> PlanResult:
    if idempotency_key:
        cached = get_cached(str(current_user.id), request.url.path, idempotency_key)
        if cached:
            return PlanResult(**cached)

    response = await planning_service.generate_plan(current_user, household_id, payload)

    if idempotency_key:
        store_cached(str(current_user.id), request.url.path, idempotency_key, response.model_dump(mode="json"))

    return response


@router.get("/v1/shopping-list", response_model=ShoppingListResponse)
async def get_shopping_list(
    planning_service: Annotated[PlanningService, Depends(get_planning_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    household_id: Annotated[UUID, Depends(get_active_household_id)],
) -> ShoppingListResponse:
    try:
        return await planning_service.get_shopping_list(current_user, household_id)
    except MealPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal plan not found") from exc


@router.delete("/v1/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: UUID,
    planning_service: Annotated[PlanningService, Depends(get_planning_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    household_id: Annotated[UUID, Depends(get_active_household_id)],
    request: Request,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> None:
    if idempotency_key:
        cached = get_cached(str(current_user.id), request.url.path, idempotency_key)
        if cached is not None:
            return None

    try:
        await planning_service.delete_plan(plan_id, current_user, household_id)
    except MealPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal plan not found") from exc

    if idempotency_key:
        store_cached(str(current_user.id), request.url.path, idempotency_key, {})
