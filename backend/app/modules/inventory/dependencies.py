from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User

from .repository import InventoryRepository
from .service import InventoryService


async def get_current_user(authorization: Annotated[str | None, Header()] = None) -> User:
    if authorization != "Bearer test-token":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Authentication dependency must be overridden",
    )


async def get_inventory_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InventoryService:
    repository = InventoryRepository(db)
    return InventoryService(repository)
