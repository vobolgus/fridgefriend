# pyright: reportAny=false, reportExplicitAny=false

from __future__ import annotations

from datetime import date, datetime
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.events import InventoryEvent
from app.models.inventory_item import InventoryItem, InventorySource, InventoryStatus
from app.modules.households.event_bus import household_event_bus


def _serialize_value(value: Any) -> Any:
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, date | datetime):
        return value.isoformat()
    if isinstance(value, InventoryStatus | InventorySource):
        return value.value
    return value


def snapshot_item(item: InventoryItem) -> dict[str, Any]:
    return {
        "id": str(item.id),
        "user_id": str(item.user_id),
        "household_id": str(item.household_id) if item.household_id is not None else None,
        "display_name": item.display_name,
        "quantity": item.quantity,
        "unit": item.unit,
        "storage_location": item.storage_location,
        "estimated_expiry_date": _serialize_value(item.estimated_expiry_date),
        "confidence": item.confidence,
        "status": _serialize_value(item.status),
        "source": _serialize_value(item.source),
        "canonical_name": item.canonical_name,
        "version": item.version,
    }


class InventoryEventService:
    async def log_event(
        self,
        household_id: uuid.UUID,
        user_id: uuid.UUID,
        item_id: uuid.UUID | None,
        action: str,
        previous_state: dict[str, Any],
        new_state: dict[str, Any],
        db: AsyncSession,
    ) -> InventoryEvent:
        event = InventoryEvent(
            household_id=household_id,
            user_id=user_id,
            item_id=item_id,
            action=action,
            previous_state=previous_state,
            new_state=new_state,
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        await household_event_bus.publish(
            household_id,
            {
                "id": str(event.id),
                "household_id": str(event.household_id),
                "user_id": str(event.user_id),
                "item_id": str(event.item_id) if event.item_id is not None else None,
                "action": event.action,
                "previous_state": event.previous_state,
                "new_state": event.new_state,
                "created_at": event.created_at.isoformat(),
            },
        )
        return event

    async def undo_last(
        self, item_id: uuid.UUID, user_id: uuid.UUID, household_id: uuid.UUID, db: AsyncSession,
    ) -> InventoryItem | None:
        result = await db.execute(
            select(InventoryEvent)
            .where(
                InventoryEvent.user_id == user_id,
                InventoryEvent.household_id == household_id,
            )
            .order_by(InventoryEvent.created_at.desc()),
        )
        event = next(
            (
                candidate
                for candidate in result.scalars()
                if candidate.item_id == item_id
                or candidate.previous_state.get("id") == str(item_id)
                or candidate.new_state.get("id") == str(item_id)
            ),
            None,
        )
        if event is None:
            return None

        previous_state = event.previous_state or {}
        item_result = await db.execute(
            select(InventoryItem).where(
                InventoryItem.id == item_id,
                InventoryItem.household_id == household_id,
            )
        )
        item = item_result.scalar_one_or_none()

        if event.action == "removed":
            if not previous_state:
                return None
            restored_item = InventoryItem(
                id=item_id,
                user_id=user_id,
                household_id=uuid.UUID(previous_state["household_id"]) if previous_state.get("household_id") else None,
                display_name=str(previous_state["display_name"]),
                quantity=float(previous_state["quantity"]),
                unit=str(previous_state["unit"]),
                storage_location=str(previous_state["storage_location"]),
                estimated_expiry_date=date.fromisoformat(str(previous_state["estimated_expiry_date"])),
                confidence=float(previous_state["confidence"]),
                status=InventoryStatus(str(previous_state["status"])),
                source=InventorySource(str(previous_state["source"])),
                canonical_name=str(previous_state["canonical_name"]),
                version=int(previous_state.get("version", 1)),
            )
            db.add(restored_item)
            await db.commit()
            await db.refresh(restored_item)
            _ = await self.log_event(
                household_id,
                user_id,
                item_id,
                "undone",
                event.new_state or {},
                snapshot_item(restored_item),
                db,
            )
            return restored_item

        if item is None or not previous_state:
            return item

        item.household_id = uuid.UUID(previous_state["household_id"]) if previous_state.get("household_id") else None
        item.display_name = str(previous_state["display_name"])
        item.quantity = float(previous_state["quantity"])
        item.unit = str(previous_state["unit"])
        item.storage_location = str(previous_state["storage_location"])
        item.estimated_expiry_date = date.fromisoformat(str(previous_state["estimated_expiry_date"]))
        item.confidence = float(previous_state["confidence"])
        item.status = InventoryStatus(str(previous_state["status"]))
        item.source = InventorySource(str(previous_state["source"]))
        item.canonical_name = str(previous_state["canonical_name"])
        item.version = int(previous_state.get("version", item.version))
        await db.commit()
        await db.refresh(item)
        _ = await self.log_event(
            household_id,
            user_id,
            item_id,
            "undone",
            event.new_state or {},
            snapshot_item(item),
            db,
        )
        return item
