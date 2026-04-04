# pyright: reportUnknownArgumentType=false, reportUnknownVariableType=false, reportAny=false

from __future__ import annotations

from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header, Request, Response, status

from app.core.idempotency import get_cached, store_cached
from app.models.user import User

from .dependencies import get_active_household_id, get_current_user, get_inventory_service
from .exceptions import InventoryItemNotFoundError, StaleDataError
from .schemas import ItemCreate, ItemResponse, ItemStatusUpdate, ItemUpdate
from .service import InventoryService

router = APIRouter(prefix="/v1/items", tags=["inventory"])


def _raise_not_found() -> NoReturn:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")


def _raise_version_conflict() -> NoReturn:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Item version conflict")


@router.post("", response_model=ItemResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: ItemCreate,
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    household_id: Annotated[UUID, Depends(get_active_household_id)],
    request: Request,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> ItemResponse:
    if idempotency_key:
        cached = get_cached(str(current_user.id), request.url.path, idempotency_key)
        if cached:
            return ItemResponse(**cached)

    item = await inventory_service.create_item(current_user, household_id, payload)
    response = ItemResponse.model_validate(item)

    if idempotency_key:
        store_cached(str(current_user.id), request.url.path, idempotency_key, response.model_dump(mode="json"))

    return response


@router.get("", response_model=list[ItemResponse], response_model_by_alias=True)
async def list_items(
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    household_id: Annotated[UUID, Depends(get_active_household_id)],
) -> list[ItemResponse]:
    items = await inventory_service.list_active_items(current_user, household_id)
    return [ItemResponse.model_validate(item) for item in items]


@router.get("/{item_id}", response_model=ItemResponse, response_model_by_alias=True)
async def get_item(
    item_id: UUID,
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    household_id: Annotated[UUID, Depends(get_active_household_id)],
) -> ItemResponse:
    try:
        return ItemResponse.model_validate(await inventory_service.get_item(item_id, current_user, household_id))
    except InventoryItemNotFoundError:
        _raise_not_found()


@router.patch("/{item_id}", response_model=ItemResponse, response_model_by_alias=True)
async def update_item(
    item_id: UUID,
    payload: ItemUpdate,
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    household_id: Annotated[UUID, Depends(get_active_household_id)],
    request: Request,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> ItemResponse:
    if idempotency_key:
        cached = get_cached(str(current_user.id), request.url.path, idempotency_key)
        if cached:
            return ItemResponse(**cached)

    try:
        response = ItemResponse.model_validate(
            await inventory_service.update_item(item_id, current_user, household_id, payload),
        )
    except InventoryItemNotFoundError:
        _raise_not_found()
    except StaleDataError:
        _raise_version_conflict()

    if idempotency_key:
        store_cached(str(current_user.id), request.url.path, idempotency_key, response.model_dump(mode="json"))

    return response


@router.put("/{item_id}", response_model=ItemResponse, response_model_by_alias=True)
async def replace_item(
    item_id: UUID,
    payload: ItemUpdate,
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    household_id: Annotated[UUID, Depends(get_active_household_id)],
    request: Request,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> ItemResponse:
    return await update_item(item_id, payload, inventory_service, current_user, household_id, request, idempotency_key)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: UUID,
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    household_id: Annotated[UUID, Depends(get_active_household_id)],
    request: Request,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> Response:
    if idempotency_key:
        cached = get_cached(str(current_user.id), request.url.path, idempotency_key)
        if cached is not None:
            return Response(status_code=status.HTTP_204_NO_CONTENT)

    try:
        await inventory_service.delete_item(item_id, current_user, household_id)
    except InventoryItemNotFoundError:
        _raise_not_found()

    if idempotency_key:
        store_cached(str(current_user.id), request.url.path, idempotency_key, {})

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{item_id}/status", response_model=ItemResponse, response_model_by_alias=True)
async def update_item_status(
    item_id: UUID,
    payload: ItemStatusUpdate,
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    household_id: Annotated[UUID, Depends(get_active_household_id)],
    request: Request,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> ItemResponse:
    if idempotency_key:
        cached = get_cached(str(current_user.id), request.url.path, idempotency_key)
        if cached:
            return ItemResponse(**cached)

    try:
        response = ItemResponse.model_validate(
            await inventory_service.update_status(item_id, current_user, household_id, payload.status),
        )
    except InventoryItemNotFoundError:
        _raise_not_found()

    if idempotency_key:
        store_cached(str(current_user.id), request.url.path, idempotency_key, response.model_dump(mode="json"))

    return response


@router.post("/{item_id}/undo", response_model=ItemResponse, response_model_by_alias=True)
async def undo_item_event(
    item_id: UUID,
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    household_id: Annotated[UUID, Depends(get_active_household_id)],
) -> ItemResponse:
    _ = household_id
    try:
        return ItemResponse.model_validate(await inventory_service.undo_last_event(item_id, current_user))
    except InventoryItemNotFoundError:
        _raise_not_found()
