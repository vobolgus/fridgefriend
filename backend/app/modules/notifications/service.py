from __future__ import annotations

import uuid

from app.models.notification import DeviceToken, NotificationPreference
from app.models.user import User

from .repository import NotificationRepository
from .schemas import DeviceTokenCreate, NotificationPreferenceUpdate


class DeviceTokenNotFoundError(Exception):
    pass


class NotificationService:
    def __init__(self, repository: NotificationRepository) -> None:
        self._repository: NotificationRepository = repository

    async def get_preferences(self, user: User) -> NotificationPreference:
        preference = await self._repository.get_preferences(user.id)
        if preference is not None:
            return preference
        return await self._repository.create_default_preferences(user.id)

    async def update_preferences(
        self,
        user: User,
        payload: NotificationPreferenceUpdate,
    ) -> NotificationPreference:
        preference = await self.get_preferences(user)
        return await self._repository.update_preferences(preference, payload)

    async def register_device_token(self, user: User, payload: DeviceTokenCreate) -> DeviceToken:
        return await self._repository.upsert_device_token(user.id, payload)

    async def unregister_device_token(self, user: User, token_id: uuid.UUID) -> None:
        device_token = await self._repository.get_device_token(user.id, token_id)
        if device_token is None:
            raise DeviceTokenNotFoundError
        await self._repository.delete_device_token(device_token)
