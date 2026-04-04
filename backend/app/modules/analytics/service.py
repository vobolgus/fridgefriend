from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.analytics_client import AnalyticsInterface, NoopAnalytics
from app.models.events import AnalyticsEvent
from app.models.user import User

from .schemas import AnalyticsEventCreate


class AnalyticsService:
    def __init__(self, session: AsyncSession, client: AnalyticsInterface | None = None) -> None:
        self._session: AsyncSession = session
        self._client: AnalyticsInterface = client or NoopAnalytics()

    async def collect_event(self, user: User, payload: AnalyticsEventCreate) -> AnalyticsEvent:
        event = AnalyticsEvent(user_id=user.id, event_type=payload.event_type, payload=payload.payload)
        self._session.add(event)
        await self._session.commit()
        await self._session.refresh(event)
        await self._client.track(
            user_id=str(user.id),
            event_type=payload.event_type,
            payload=payload.payload,
        )
        return event
