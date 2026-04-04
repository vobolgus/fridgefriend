# pyright: reportAny=false, reportExplicitAny=false

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse

from app.core.idempotency import get_cached, require_idempotency_key, store_cached
from app.models.events import InventoryEvent
from app.models.household import Household
from app.models.user import User
from app.modules.inventory.dependencies import get_current_user

from .activity_service import ActivityService
from .dependencies import get_activity_service, get_household_service
from .event_bus import household_event_bus
from .schemas import HouseholdCreate, HouseholdMemberResponse, HouseholdResponse, HouseholdUpdate, JoinRequest
from .sse import household_event_stream
from .service import (
    HouseholdAccessError,
    HouseholdInviteCodeError,
    HouseholdNotFoundError,
    HouseholdService,
)

router = APIRouter(prefix="/v1/households", tags=["households"])


def _serialize_household(household: Household, current_user_id: UUID) -> HouseholdResponse:
    members = sorted(household.members, key=lambda member: member.created_at)
    current_membership = next((member for member in members if member.user_id == current_user_id), None)
    return HouseholdResponse(
        id=household.id,
        name=household.name,
        invite_code=household.invite_code,
        is_active=current_membership.is_active if current_membership is not None else False,
        members=[
            HouseholdMemberResponse(
                id=member.id,
                user_id=member.user_id,
                email=member.user.email if member.user is not None else "",
                role=member.role,
            )
            for member in members
        ],
        created_at=household.created_at,
        updated_at=household.updated_at,
    )


def _raise_not_found() -> NoReturn:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")


def _raise_forbidden() -> NoReturn:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def _raise_invalid_invite_code() -> NoReturn:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite code not found")


def _serialize_activity_event(event: InventoryEvent) -> dict[str, object]:
    return {
        "id": str(event.id),
        "household_id": str(event.household_id),
        "user_id": str(event.user_id),
        "item_id": str(event.item_id) if event.item_id is not None else None,
        "action": event.action,
        "previous_state": event.previous_state,
        "new_state": event.new_state,
        "created_at": event.created_at.isoformat(),
    }


@router.get("", response_model=list[HouseholdResponse])
async def list_households(
    household_service: Annotated[HouseholdService, Depends(get_household_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[HouseholdResponse]:
    households = await household_service.list_households(current_user)
    return [_serialize_household(household, current_user.id) for household in households]


@router.post("", response_model=HouseholdResponse, status_code=status.HTTP_201_CREATED)
async def create_household(
    payload: HouseholdCreate,
    household_service: Annotated[HouseholdService, Depends(get_household_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
) -> HouseholdResponse:
    cache_scope = str(current_user.id)
    cached = get_cached(cache_scope, request.url.path, idempotency_key)
    if cached:
        return HouseholdResponse(**cached)

    household = await household_service.create_household(current_user, payload)
    response = _serialize_household(household, current_user.id)

    store_cached(cache_scope, request.url.path, idempotency_key, response.model_dump(mode="json"))

    return response


@router.get("/{household_id}", response_model=HouseholdResponse)
async def get_household_detail(
    household_id: UUID,
    household_service: Annotated[HouseholdService, Depends(get_household_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> HouseholdResponse:
    try:
        household = await household_service.get_household(current_user, household_id)
    except HouseholdNotFoundError:
        _raise_not_found()
    return _serialize_household(household, current_user.id)


@router.patch("/{household_id}", response_model=HouseholdResponse)
async def update_household(
    household_id: UUID,
    payload: HouseholdUpdate,
    household_service: Annotated[HouseholdService, Depends(get_household_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
) -> HouseholdResponse:
    cache_scope = str(current_user.id)
    cached = get_cached(cache_scope, request.url.path, idempotency_key)
    if cached:
        return HouseholdResponse(**cached)

    try:
        household = await household_service.update_household(current_user, household_id, payload)
    except HouseholdNotFoundError:
        _raise_not_found()

    response = _serialize_household(household, current_user.id)
    store_cached(cache_scope, request.url.path, idempotency_key, response.model_dump(mode="json"))
    return response


@router.post("/join", response_model=HouseholdResponse)
async def join_household(
    payload: JoinRequest,
    household_service: Annotated[HouseholdService, Depends(get_household_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
) -> HouseholdResponse:
    cache_scope = str(current_user.id)
    cached = get_cached(cache_scope, request.url.path, idempotency_key)
    if cached:
        return HouseholdResponse(**cached)

    try:
        household = await household_service.join_household(current_user, payload.invite_code)
    except HouseholdInviteCodeError:
        _raise_invalid_invite_code()

    response = _serialize_household(household, current_user.id)
    store_cached(cache_scope, request.url.path, idempotency_key, response.model_dump(mode="json"))
    return response


@router.post("/{household_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_household(
    household_id: UUID,
    household_service: Annotated[HouseholdService, Depends(get_household_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
) -> Response:
    cache_scope = str(current_user.id)
    cached = get_cached(cache_scope, request.url.path, idempotency_key)
    if cached is not None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    try:
        await household_service.leave_household(current_user, household_id)
    except HouseholdNotFoundError:
        _raise_not_found()

    store_cached(cache_scope, request.url.path, idempotency_key, {})
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{household_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_household_member(
    household_id: UUID,
    user_id: UUID,
    household_service: Annotated[HouseholdService, Depends(get_household_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
) -> Response:
    cache_scope = str(current_user.id)
    cached = get_cached(cache_scope, request.url.path, idempotency_key)
    if cached is not None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    try:
        await household_service.remove_member(current_user, household_id, user_id)
    except HouseholdNotFoundError:
        _raise_not_found()
    except HouseholdAccessError:
        _raise_forbidden()

    store_cached(cache_scope, request.url.path, idempotency_key, {})
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{household_id}/events")
async def stream_household_events(
    household_id: UUID,
    request: Request,
    household_service: Annotated[HouseholdService, Depends(get_household_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    try:
        _ = await household_service.get_household(current_user, household_id)
    except HouseholdNotFoundError:
        _raise_not_found()

    last_event_id = request.headers.get("Last-Event-ID")

    async def stream() -> AsyncIterator[str]:
        async with household_event_bus.subscribe(household_id) as queue:
            async for chunk in household_event_stream(
                request,
                household_event_bus,
                household_id,
                queue,
                last_event_id,
            ):
                yield chunk

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.get("/{household_id}/activity")
async def get_household_activity(
    household_id: UUID,
    household_service: Annotated[HouseholdService, Depends(get_household_service)],
    activity_service: Annotated[ActivityService, Depends(get_activity_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 20,
    offset: int = 0,
 ) -> list[dict[str, object]]:
    try:
        household = await household_service.get_household(current_user, household_id)
    except HouseholdNotFoundError:
        _raise_not_found()

    events = await activity_service.list_household_activity(household.id, limit=limit, offset=offset)
    return [_serialize_activity_event(event) for event in events]
