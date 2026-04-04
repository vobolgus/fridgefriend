from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.idempotency import get_cached, require_idempotency_key, store_cached
from app.models.user import User
from app.modules.inventory.dependencies import get_current_user

from .schemas import AnalyticsEventAccepted, AnalyticsEventCreate
from .service import AnalyticsService

router = APIRouter(prefix="/v1/analytics", tags=["analytics"])


@router.post("/events", response_model=AnalyticsEventAccepted, status_code=status.HTTP_202_ACCEPTED)
async def collect_event(
    payload: AnalyticsEventCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
) -> AnalyticsEventAccepted:
    cached = get_cached(str(current_user.id), request.url.path, idempotency_key)
    if cached:
        return AnalyticsEventAccepted.model_validate(cached)

    event = await AnalyticsService(db).collect_event(current_user, payload)
    response = AnalyticsEventAccepted(event_id=event.id, created_at=event.created_at)

    store_cached(str(current_user.id), request.url.path, idempotency_key, response.model_dump(mode="json"))

    return response
