from __future__ import annotations

from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.core.idempotency import get_cached, require_idempotency_key, store_cached
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
    request: Request,
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
) -> NotificationPreferenceResponse:
    cached = get_cached(str(current_user.id), request.url.path, idempotency_key)
    if cached:
        return NotificationPreferenceResponse.model_validate(cached)

    preference = await notification_service.update_preferences(current_user, payload)
    response = NotificationPreferenceResponse.model_validate(preference)

    store_cached(str(current_user.id), request.url.path, idempotency_key, response.model_dump(mode="json"))

    return response


@router.post("/devices", response_model=DeviceTokenResponse, status_code=status.HTTP_201_CREATED)
async def register_device_token(
    payload: DeviceTokenCreate,
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
) -> DeviceTokenResponse:
    cached = get_cached(str(current_user.id), request.url.path, idempotency_key)
    if cached:
        return DeviceTokenResponse.model_validate(cached)

    token = await notification_service.register_device_token(current_user, payload)
    response = DeviceTokenResponse.model_validate(token)

    store_cached(str(current_user.id), request.url.path, idempotency_key, response.model_dump(mode="json"))

    return response


@router.delete("/devices/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_device_token(
    token_id: UUID,
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
) -> Response:
    cached = get_cached(str(current_user.id), request.url.path, idempotency_key)
    if cached is not None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    try:
        await notification_service.unregister_device_token(current_user, token_id)
    except DeviceTokenNotFoundError:
        _raise_device_token_not_found()

    store_cached(str(current_user.id), request.url.path, idempotency_key, {})

    return Response(status_code=status.HTTP_204_NO_CONTENT)
