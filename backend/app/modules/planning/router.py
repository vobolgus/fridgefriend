from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.modules.inventory.dependencies import get_current_user

from .schemas import PlanRequest, PlanResult, ShoppingListResponse
from .service import MealPlanNotFoundError, PlanningService

router = APIRouter(tags=["planning"])


async def get_planning_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlanningService:
    return PlanningService(db)


@router.post("/v1/plans", response_model=PlanResult)
async def create_plan(
    payload: PlanRequest,
    planning_service: Annotated[PlanningService, Depends(get_planning_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PlanResult:
    return await planning_service.generate_plan(current_user, payload)


@router.get("/v1/shopping-list", response_model=ShoppingListResponse)
async def get_shopping_list(
    planning_service: Annotated[PlanningService, Depends(get_planning_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ShoppingListResponse:
    try:
        return await planning_service.get_shopping_list(current_user)
    except MealPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal plan not found") from exc
