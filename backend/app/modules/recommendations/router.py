from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.modules.inventory.dependencies import get_current_user

from .schemas import RecommendationRequest, RecommendationResponse
from .service import RecommendationService

router = APIRouter(prefix="/v1/recommendations", tags=["recommendations"])


async def get_recommendation_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecommendationService:
    return RecommendationService(db)


@router.post("", response_model=RecommendationResponse)
async def get_recommendations(
    payload: RecommendationRequest,
    recommendation_service: Annotated[RecommendationService, Depends(get_recommendation_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RecommendationResponse:
    recipes = await recommendation_service.get_recommendations(current_user.id, payload)
    return RecommendationResponse(recipes=recipes)
