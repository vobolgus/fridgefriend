# pyright: reportAny=false

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.idempotency import get_cached, require_idempotency_key, store_cached
from app.models.user import User
from app.modules.inventory.dependencies import get_active_household_id, get_current_user

from .mock_recipe_source import MockRecipeSource
from .opensearch_client import OpenSearchRecipeSource
from .schemas import RecommendationRequest, RecommendationResponse
from .spoonacular import SpoonacularClient
from .service import RecommendationService

router = APIRouter(prefix="/v1/recommendations", tags=["recommendations"])


async def get_recommendation_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecommendationService:
    if settings.RECIPE_SOURCE == "spoonacular" and settings.SPOONACULAR_API_KEY:
        recipe_source = SpoonacularClient(settings.SPOONACULAR_API_KEY)
    elif settings.RECIPE_SOURCE == "opensearch":
        recipe_source = OpenSearchRecipeSource()
    else:
        recipe_source = MockRecipeSource()
    return RecommendationService(db, recipe_source=recipe_source)


@router.post("", response_model=RecommendationResponse, response_model_by_alias=True)
async def get_recommendations(
    payload: RecommendationRequest,
    recommendation_service: Annotated[RecommendationService, Depends(get_recommendation_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    household_id: Annotated[UUID, Depends(get_active_household_id)],
    request: Request,
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
) -> RecommendationResponse:
    cached = get_cached(str(current_user.id), request.url.path, idempotency_key)
    if cached:
        return RecommendationResponse(**cached)

    recipes = await recommendation_service.get_recommendations(current_user.id, payload, household_id=household_id)
    response = RecommendationResponse(recipes=recipes)

    store_cached(str(current_user.id), request.url.path, idempotency_key, response.model_dump(mode="json"))

    return response
