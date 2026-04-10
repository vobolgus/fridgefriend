# pyright: reportAny=false

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.idempotency import get_cached, require_idempotency_key, store_cached
from app.models.user import User
from app.modules.inventory.dependencies import get_active_household_id, get_current_user

from .schemas import RecommendationRequest, RecommendationResponse, RecipeRecommendation
from .service import RecommendationService

router = APIRouter(tags=["recommendations"])


async def get_recommendation_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecommendationService:
    from app.core.config import settings

    if settings.RECIPE_SOURCE == "opensearch":
        from .opensearch_client import OpenSearchRecipeSource

        recipe_source = OpenSearchRecipeSource()
    elif settings.RECIPE_SOURCE == "spoonacular":
        from .spoonacular import SpoonacularClient

        recipe_source = SpoonacularClient(api_key=settings.SPOONACULAR_API_KEY)
    else:
        from .mock_recipe_source import MockRecipeSource

        recipe_source = MockRecipeSource()
    return RecommendationService(session=db, recipe_source=recipe_source)


@router.post("/v1/recommendations", response_model=RecommendationResponse, response_model_by_alias=True)
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

    recipes, source = await recommendation_service.get_recommendations_with_source(
        current_user.id,
        payload,
        household_id=household_id,
    )
    response = RecommendationResponse(recipes=recipes, source=source)

    store_cached(str(current_user.id), request.url.path, idempotency_key, response.model_dump(mode="json"))

    return response


@router.get("/v1/recipes/{recipe_id}", response_model=RecipeRecommendation, response_model_by_alias=True)
async def get_recipe_detail(
    recipe_id: UUID,
    recommendation_service: Annotated[RecommendationService, Depends(get_recommendation_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RecipeRecommendation:
    _ = current_user
    recipe = await recommendation_service.get_recipe_detail(recipe_id)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return recipe
