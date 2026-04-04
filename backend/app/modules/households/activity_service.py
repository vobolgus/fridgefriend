from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.events import InventoryEvent


class ActivityService:
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    async def list_household_activity(
        self,
        household_id: UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[InventoryEvent]:
        result = await self._session.execute(
            select(InventoryEvent)
            .where(InventoryEvent.household_id == household_id)
            .order_by(InventoryEvent.created_at.desc())
            .limit(limit)
            .offset(offset),
        )
        return list(result.scalars().all())
