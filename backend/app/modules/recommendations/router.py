# pyright: reportAny=false

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.idempotency import get_cached, store_cached
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
    request: Request,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> RecommendationResponse:
    if idempotency_key:
        cached = get_cached(str(current_user.id), request.url.path, idempotency_key)
        if cached:
            return RecommendationResponse(**cached)

    recipes = await recommendation_service.get_recommendations(current_user.id, payload)
    response = RecommendationResponse(recipes=recipes)

    if idempotency_key:
        store_cached(str(current_user.id), request.url.path, idempotency_key, response.model_dump(mode="json"))

    return response
