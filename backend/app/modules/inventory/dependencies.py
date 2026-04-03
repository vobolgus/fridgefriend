from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User

from .repository import InventoryRepository
from .service import InventoryService


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if authorization != "Bearer test-token":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    result = await db.execute(select(User).where(User.email == "dev@fridgefriend.local"))
    user = result.scalars().first()
    if user is None:
        user = User(email="dev@fridgefriend.local")
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def get_inventory_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InventoryService:
    repository = InventoryRepository(db)
    return InventoryService(repository)
