from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
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
) -> AnalyticsEventAccepted:
    event = await AnalyticsService(db).collect_event(current_user, payload)
    return AnalyticsEventAccepted(event_id=event.id, created_at=event.created_at)
