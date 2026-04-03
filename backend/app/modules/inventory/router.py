# pyright: reportUnknownArgumentType=false, reportUnknownVariableType=false

from __future__ import annotations

from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.models.user import User

from .dependencies import get_current_user, get_inventory_service
from .schemas import ItemCreate, ItemResponse, ItemStatusUpdate, ItemUpdate
from .service import InventoryItemNotFoundError, InventoryService

router = APIRouter(prefix="/v1/items", tags=["inventory"])


def _raise_not_found() -> NoReturn:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: ItemCreate,
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ItemResponse:
    item = await inventory_service.create_item(current_user, payload)
    return ItemResponse.model_validate(item)


@router.get("", response_model=list[ItemResponse])
async def list_items(
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ItemResponse]:
    items = await inventory_service.list_active_items(current_user)
    return [ItemResponse.model_validate(item) for item in items]


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: UUID,
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ItemResponse:
    try:
        return ItemResponse.model_validate(await inventory_service.get_item(item_id, current_user))
    except InventoryItemNotFoundError:
        _raise_not_found()


@router.patch("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: UUID,
    payload: ItemUpdate,
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ItemResponse:
    try:
        return ItemResponse.model_validate(
            await inventory_service.update_item(item_id, current_user, payload),
        )
    except InventoryItemNotFoundError:
        _raise_not_found()


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: UUID,
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    try:
        await inventory_service.delete_item(item_id, current_user)
    except InventoryItemNotFoundError:
        _raise_not_found()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{item_id}/status", response_model=ItemResponse)
async def update_item_status(
    item_id: UUID,
    payload: ItemStatusUpdate,
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ItemResponse:
    try:
        return ItemResponse.model_validate(
            await inventory_service.update_status(item_id, current_user, payload.status),
        )
    except InventoryItemNotFoundError:
        _raise_not_found()
