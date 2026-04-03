from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory_item import InventoryItem, InventoryStatus
from .schemas import ItemCreate, ItemUpdate


class InventoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    async def create(self, user_id: UUID, data: ItemCreate) -> InventoryItem:
        item = InventoryItem(user_id=user_id, **data.model_dump())
        self._session.add(item)
        await self._session.commit()
        await self._session.refresh(item)
        return item

    async def get_by_id(self, item_id: UUID, user_id: UUID) -> InventoryItem | None:
        statement = select(InventoryItem).where(
            InventoryItem.id == item_id,
            InventoryItem.user_id == user_id,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_active(self, user_id: UUID) -> list[InventoryItem]:
        statement = (
            select(InventoryItem)
            .where(
                InventoryItem.user_id == user_id,
                InventoryItem.status == InventoryStatus.ACTIVE,
            )
            .order_by(InventoryItem.created_at.desc())
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def update(self, item_id: UUID, user_id: UUID, data: ItemUpdate) -> InventoryItem | None:
        item = await self.get_by_id(item_id, user_id)
        if item is None:
            return None

        updates: dict[str, object] = data.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(item, field_name, value)

        await self._session.commit()
        await self._session.refresh(item)
        return item

    async def update_status(
        self,
        item_id: UUID,
        user_id: UUID,
        status: InventoryStatus,
    ) -> InventoryItem | None:
        item = await self.get_by_id(item_id, user_id)
        if item is None:
            return None

        item.status = status
        await self._session.commit()
        await self._session.refresh(item)
        return item

    async def delete(self, item_id: UUID, user_id: UUID) -> bool:
        item = await self.get_by_id(item_id, user_id)
        if item is None:
            return False

        await self._session.delete(item)
        await self._session.commit()
        return True
