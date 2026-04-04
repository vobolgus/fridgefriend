# pyright: reportAttributeAccessIssue=false, reportUnknownMemberType=false, reportUntypedFunctionDecorator=false, reportExplicitAny=false

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.household import HouseholdMember
from app.models.inventory_item import InventoryItem, InventoryStatus
from app.models.notification import DeviceToken, NotificationPreference
from app.models.user import User

from .push import FCMPushService, MockPushService, PushServiceInterface


def _is_within_quiet_hours(current: time, start: time | None, end: time | None) -> bool:
    if start is None or end is None:
        return False
    if start == end:
        return True
    if start < end:
        return start <= current < end
    return current >= start or current < end


async def _collect_due_items(
    session: AsyncSession,
    user: User,
    reminder_days_before: int,
    current_date: date,
) -> list[InventoryItem]:
    membership_result = await session.execute(
        select(HouseholdMember.household_id).where(HouseholdMember.user_id == user.id),
    )
    household_ids = list(membership_result.scalars().all())
    if not household_ids:
        return []

    threshold_date = current_date + timedelta(days=reminder_days_before)
    result = await session.execute(
        select(InventoryItem)
        .where(
            InventoryItem.household_id.in_(household_ids),
            InventoryItem.status.notin_([InventoryStatus.USED, InventoryStatus.DISCARDED]),
            InventoryItem.estimated_expiry_date >= current_date,
            InventoryItem.estimated_expiry_date <= threshold_date,
        )
        .order_by(InventoryItem.estimated_expiry_date.asc(), InventoryItem.display_name.asc()),
    )
    return list(result.scalars().all())


async def send_expiry_reminders(
    *,
    session: AsyncSession | None = None,
    push_service: PushServiceInterface | None = None,
    now: datetime | None = None,
) -> int:
    owns_session = session is None
    active_session = session or AsyncSessionLocal()
    service = push_service or (FCMPushService() if settings.FCM_ENABLED else MockPushService())
    current_time = now or datetime.now(UTC)
    notifications_sent = 0

    try:
        result = await active_session.execute(select(User).order_by(User.created_at.asc()))
        users = list(result.scalars().all())

        for user in users:
            preference_result = await active_session.execute(
                select(NotificationPreference).where(NotificationPreference.user_id == user.id),
            )
            preference = preference_result.scalar_one_or_none() or NotificationPreference(user_id=user.id)
            if not preference.expiry_reminder_enabled:
                continue
            if _is_within_quiet_hours(
                current_time.timetz().replace(tzinfo=None),
                preference.quiet_hours_start,
                preference.quiet_hours_end,
            ):
                continue

            token_result = await active_session.execute(
                select(DeviceToken).where(DeviceToken.user_id == user.id).order_by(DeviceToken.created_at.asc()),
            )
            device_tokens = list(token_result.scalars().all())
            if not device_tokens:
                continue

            due_items = await _collect_due_items(
                active_session,
                user,
                preference.reminder_days_before,
                current_time.date(),
            )
            if not due_items:
                continue

            item_count = len(due_items)
            first_item = due_items[0].display_name
            title = "Items expiring soon"
            body = f"{item_count} item(s) need attention. Next up: {first_item}."
            for device_token in device_tokens:
                if await service.send(device_token.token, title, body):
                    notifications_sent += 1
    finally:
        if owns_session:
            await active_session.close()

    return notifications_sent


if celery_app is not None:

    @celery_app.task(name="app.modules.notifications.tasks.send_expiry_reminders_task")
    def send_expiry_reminders_task() -> int:
        return asyncio.run(send_expiry_reminders())
