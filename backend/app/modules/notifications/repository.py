# pyright: reportAny=false

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import DeviceToken, NotificationPreference

from .schemas import DeviceTokenCreate, NotificationPreferenceUpdate


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def get_preferences(self, user_id: uuid.UUID) -> NotificationPreference | None:
        result = await self._session.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id),
        )
        return result.scalar_one_or_none()

    async def create_default_preferences(self, user_id: uuid.UUID) -> NotificationPreference:
        preference = NotificationPreference(user_id=user_id)
        self._session.add(preference)
        await self._session.commit()
        await self._session.refresh(preference)
        return preference

    async def update_preferences(
        self,
        preference: NotificationPreference,
        payload: NotificationPreferenceUpdate,
    ) -> NotificationPreference:
        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(preference, field, value)

        await self._session.commit()
        await self._session.refresh(preference)
        return preference

    async def get_device_token(self, user_id: uuid.UUID, token_id: uuid.UUID) -> DeviceToken | None:
        result = await self._session.execute(
            select(DeviceToken).where(DeviceToken.id == token_id, DeviceToken.user_id == user_id),
        )
        return result.scalar_one_or_none()

    async def get_device_token_by_value(self, token: str) -> DeviceToken | None:
        result = await self._session.execute(select(DeviceToken).where(DeviceToken.token == token))
        return result.scalar_one_or_none()

    async def upsert_device_token(self, user_id: uuid.UUID, payload: DeviceTokenCreate) -> DeviceToken:
        statement = sqlite_insert(DeviceToken).values(
            user_id=user_id,
            token=payload.token,
            platform=payload.platform,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[DeviceToken.token],
            set_={
                "user_id": user_id,
                "platform": payload.platform,
            },
        )
        _ = await self._session.execute(statement)
        await self._session.commit()
        result = await self._session.execute(select(DeviceToken).where(DeviceToken.token == payload.token))
        device_token = result.scalar_one()
        await self._session.refresh(device_token)
        return device_token

    async def update_device_token(self, device_token: DeviceToken, *, user_id: uuid.UUID, platform: str) -> DeviceToken:
        device_token.user_id = user_id
        device_token.platform = platform
        await self._session.commit()
        await self._session.refresh(device_token)
        return device_token

    async def delete_device_token(self, device_token: DeviceToken) -> None:
        await self._session.delete(device_token)
        await self._session.commit()
