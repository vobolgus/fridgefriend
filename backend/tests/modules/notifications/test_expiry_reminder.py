from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.household import Household, HouseholdMember, HouseholdRole
from app.models.inventory_item import InventoryItem, InventorySource, InventoryStatus
from app.models.notification import DeviceToken, NotificationPreference
from app.models.user import User
from app.modules.notifications.tasks import send_expiry_reminders


class RecordingPushService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    async def send(self, token: str, title: str, body: str) -> bool:
        self.calls.append((token, title, body))
        return True


async def _seed_user_with_due_item(
    db_session: AsyncSession,
    *,
    email: str,
    reminder_enabled: bool = True,
    quiet_hours_start: time | None = None,
    quiet_hours_end: time | None = None,
    expiry_offset_days: int = 1,
) -> tuple[User, DeviceToken]:
    user = User(email=email)
    db_session.add(user)
    await db_session.flush()

    household = Household(name=f"{email} household", invite_code=email.replace("@", "-")[:20])
    db_session.add(household)
    await db_session.flush()
    db_session.add(HouseholdMember(household_id=household.id, user_id=user.id, role=HouseholdRole.OWNER))
    db_session.add(
        NotificationPreference(
            user_id=user.id,
            expiry_reminder_enabled=reminder_enabled,
            reminder_days_before=1,
            quiet_hours_start=quiet_hours_start,
            quiet_hours_end=quiet_hours_end,
        ),
    )
    token = DeviceToken(user_id=user.id, token=f"token-{email}", platform="ios")
    db_session.add(token)
    db_session.add(
        InventoryItem(
            user_id=user.id,
            household_id=household.id,
            display_name="Milk",
            quantity=1.0,
            unit="liter",
            storage_location="fridge",
            estimated_expiry_date=(datetime.now(UTC) + timedelta(days=expiry_offset_days)).date(),
            confidence=0.9,
            status=InventoryStatus.ACTIVE,
            source=InventorySource.MANUAL,
            canonical_name="milk",
        ),
    )
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(token)
    return user, token


@pytest.mark.asyncio
async def test_reminder_task_finds_items_expiring_within_threshold(db_session: AsyncSession) -> None:
    _, token = await _seed_user_with_due_item(db_session, email="reminder-threshold@example.com")
    push_service = RecordingPushService()

    sent_count = await send_expiry_reminders(
        session=db_session,
        push_service=push_service,
        now=datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0),
    )

    assert sent_count == 1
    assert push_service.calls[0][0] == token.token


@pytest.mark.asyncio
async def test_reminder_respects_quiet_hours(db_session: AsyncSession) -> None:
    await _seed_user_with_due_item(
        db_session,
        email="quiet-hours@example.com",
        quiet_hours_start=time(22, 0),
        quiet_hours_end=time(7, 0),
    )
    push_service = RecordingPushService()

    sent_count = await send_expiry_reminders(
        session=db_session,
        push_service=push_service,
        now=datetime.now(UTC).replace(hour=23, minute=0, second=0, microsecond=0),
    )

    assert sent_count == 0
    assert push_service.calls == []


@pytest.mark.asyncio
async def test_reminder_skips_users_with_disabled_notifications(db_session: AsyncSession) -> None:
    await _seed_user_with_due_item(
        db_session,
        email="disabled-reminder@example.com",
        reminder_enabled=False,
    )
    push_service = RecordingPushService()

    sent_count = await send_expiry_reminders(
        session=db_session,
        push_service=push_service,
        now=datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0),
    )

    assert sent_count == 0
    assert push_service.calls == []
