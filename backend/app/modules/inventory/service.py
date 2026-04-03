# pyright: reportUnknownMemberType=false

from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from app.models.inventory_item import InventoryItem, InventoryStatus
from app.models.user import User

from .repository import InventoryRepository
from .schemas import ItemCreate, ItemUpdate


DEFAULT_EXPIRY_DAYS = 7
DEFAULT_CONFIDENCE = 0.5


class InventoryItemNotFoundError(Exception):
    pass


class InventoryService:
    def __init__(self, repository: InventoryRepository) -> None:
        self._repository: InventoryRepository = repository

    async def create_item(self, user: User, data: ItemCreate) -> InventoryItem:
        default_expiry_date = date.today() + timedelta(days=DEFAULT_EXPIRY_DAYS)
        payload = data.model_copy(
            update={
                "estimated_expiry_date": data.estimated_expiry_date or default_expiry_date,
                "confidence": data.confidence if data.estimated_expiry_date is not None else DEFAULT_CONFIDENCE,
                "canonical_name": data.canonical_name or data.display_name,
            },
        )
        return await self._repository.create(user.id, payload)

    async def list_active_items(self, user: User) -> list[InventoryItem]:
        return await self._repository.list_active(user.id)

    async def get_item(self, item_id: UUID, user: User) -> InventoryItem:
        item = await self._repository.get_by_id(item_id, user.id)
        if item is None:
            raise InventoryItemNotFoundError
        return item

    async def update_item(self, item_id: UUID, user: User, data: ItemUpdate) -> InventoryItem:
        item = await self._repository.update(item_id, user.id, data)
        if item is None:
            raise InventoryItemNotFoundError
        return item

    async def update_status(
        self,
        item_id: UUID,
        user: User,
        status: InventoryStatus,
    ) -> InventoryItem:
        item = await self._repository.update_status(item_id, user.id, status)
        if item is None:
            raise InventoryItemNotFoundError
        return item

    async def delete_item(self, item_id: UUID, user: User) -> None:
        deleted = await self._repository.delete(item_id, user.id)
        if not deleted:
            raise InventoryItemNotFoundError
