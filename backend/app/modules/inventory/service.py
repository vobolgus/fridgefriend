# pyright: reportUnknownMemberType=false

from __future__ import annotations

from datetime import date
from uuid import UUID

from app.core.units import normalize_unit
from app.models.inventory_item import InventoryItem, InventorySource, InventoryStatus
from app.models.user import User
from app.modules.catalog.service import CatalogService
from app.modules.expiry.service import ExpiryService

from .exceptions import InventoryItemNotFoundError
from .event_service import InventoryEventService, snapshot_item
from .repository import InventoryRepository
from .schemas import ItemCreate, ItemUpdate


class InventoryService:
    def __init__(
        self,
        repository: InventoryRepository,
        event_service: InventoryEventService | None = None,
        catalog_service: CatalogService | None = None,
        expiry_service: ExpiryService | None = None,
    ) -> None:
        self._repository: InventoryRepository = repository
        self._event_service: InventoryEventService = event_service or InventoryEventService()
        self._catalog_service: CatalogService | None = catalog_service
        self._expiry_service: ExpiryService = expiry_service or ExpiryService()

    async def create_item(self, user: User, household_id: UUID, data: ItemCreate) -> InventoryItem:
        canonical = None
        if self._catalog_service is not None:
            canonical = await self._catalog_service.resolve_canonical(data.canonical_name or data.display_name)
        canonical_name = canonical.name if canonical is not None else (data.canonical_name or data.display_name)

        if data.estimated_expiry_date is None:
            estimated_expiry_date, expiry_confidence = self._expiry_service.calculate_expiry(
                canonical_name,
                data.storage_location,
                date.today(),
            )
            if data.source in {InventorySource.BARCODE, InventorySource.PHOTO}:
                confidence = data.confidence
            else:
                confidence = expiry_confidence
        else:
            estimated_expiry_date = data.estimated_expiry_date
            confidence = data.confidence

        normalized_unit = normalize_unit(data.unit)
        normalized_quantity = max(0.0, round(data.quantity, 3))

        payload = data.model_copy(
            update={
                "estimated_expiry_date": estimated_expiry_date,
                "confidence": confidence,
                "canonical_name": canonical_name,
                "unit": normalized_unit,
                "quantity": normalized_quantity,
                "canonical_ingredient_id": (
                    canonical.id if canonical is not None else data.canonical_ingredient_id
                ),
            },
        )
        item = await self._repository.create(user.id, household_id, payload)
        _ = await self._event_service.log_event(
            household_id,
            user.id,
            item.id,
            "added",
            {},
            snapshot_item(item),
            self._repository.session,
        )
        return item

    async def list_active_items(self, user: User, household_id: UUID) -> list[InventoryItem]:
        _ = user
        return await self._repository.list_active(household_id)

    async def get_item(self, item_id: UUID, user: User, household_id: UUID) -> InventoryItem:
        _ = user
        item = await self._repository.get_by_id(item_id, household_id)
        if item is None:
            raise InventoryItemNotFoundError
        return item

    async def update_item(self, item_id: UUID, user: User, household_id: UUID, data: ItemUpdate) -> InventoryItem:
        existing = await self._repository.get_by_id(item_id, household_id)
        if existing is None:
            raise InventoryItemNotFoundError
        previous_state = snapshot_item(existing)
        if data.display_name is not None:
            canonical = None
            if self._catalog_service is not None:
                canonical = await self._catalog_service.resolve_canonical(data.canonical_name or data.display_name)
            canonical_name = canonical.name if canonical is not None else (data.canonical_name or data.display_name)
            canonical_ingredient_id = canonical.id if canonical is not None else None
            data = data.model_copy(
                update={
                    "canonical_name": canonical_name,
                    "canonical_ingredient_id": canonical_ingredient_id,
                }
            )
        if data.unit is not None:
            data = data.model_copy(update={"unit": normalize_unit(data.unit)})
        if data.quantity is not None:
            data = data.model_copy(update={"quantity": max(0.0, round(data.quantity, 3))})
        item = await self._repository.update(item_id, household_id, data)
        if item is None:
            raise InventoryItemNotFoundError
        _ = await self._event_service.log_event(
            household_id,
            user.id,
            item.id,
            "updated",
            previous_state,
            snapshot_item(item),
            self._repository.session,
        )
        return item

    async def update_status(
        self,
        item_id: UUID,
        user: User,
        household_id: UUID,
        status: InventoryStatus,
    ) -> InventoryItem:
        existing = await self._repository.get_by_id(item_id, household_id)
        if existing is None:
            raise InventoryItemNotFoundError
        previous_state = snapshot_item(existing)
        item = await self._repository.update_status(item_id, household_id, status)
        if item is None:
            raise InventoryItemNotFoundError
        _ = await self._event_service.log_event(
            household_id,
            user.id,
            item.id,
            "status_updated",
            previous_state,
            snapshot_item(item),
            self._repository.session,
        )
        return item

    async def delete_item(self, item_id: UUID, user: User, household_id: UUID) -> None:
        existing = await self._repository.get_by_id(item_id, household_id)
        if existing is None:
            raise InventoryItemNotFoundError
        previous_state = snapshot_item(existing)
        _ = await self._event_service.log_event(
            household_id,
            user.id,
            item_id,
            "removed",
            previous_state,
            {},
            self._repository.session,
        )
        deleted = await self._repository.delete(item_id, household_id)
        if deleted is None:
            raise InventoryItemNotFoundError

    async def undo_last_event(self, item_id: UUID, user: User, household_id: UUID) -> InventoryItem:
        item = await self._event_service.undo_last(item_id, user.id, household_id, self._repository.session)
        if item is None:
            raise InventoryItemNotFoundError
        return item
