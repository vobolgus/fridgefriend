from __future__ import annotations

from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.models.user import User
from app.modules.inventory.dependencies import get_current_user

from .dependencies import get_notification_service
from .schemas import (
    DeviceTokenCreate,
    DeviceTokenResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)
from .service import DeviceTokenNotFoundError, NotificationService

router = APIRouter(prefix="/v1/notifications", tags=["notifications"])


def _raise_device_token_not_found() -> NoReturn:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device token not found")


@router.get("", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> NotificationPreferenceResponse:
    preference = await notification_service.get_preferences(current_user)
    return NotificationPreferenceResponse.model_validate(preference)


@router.patch("", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    payload: NotificationPreferenceUpdate,
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> NotificationPreferenceResponse:
    preference = await notification_service.update_preferences(current_user, payload)
    return NotificationPreferenceResponse.model_validate(preference)


@router.post("/devices", response_model=DeviceTokenResponse, status_code=status.HTTP_201_CREATED)
async def register_device_token(
    payload: DeviceTokenCreate,
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DeviceTokenResponse:
    token = await notification_service.register_device_token(current_user, payload)
    return DeviceTokenResponse.model_validate(token)


@router.delete("/devices/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_device_token(
    token_id: UUID,
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    try:
        await notification_service.unregister_device_token(current_user, token_id)
    except DeviceTokenNotFoundError:
        _raise_device_token_not_found()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
