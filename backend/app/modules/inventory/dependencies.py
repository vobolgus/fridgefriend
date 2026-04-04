# pyright: reportMissingImports=false, reportUnknownVariableType=false

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.modules.catalog.service import CatalogService
from app.modules.households.dependencies import get_active_household

from .repository import InventoryRepository
from .service import InventoryService

__all__ = ["get_current_user", "get_inventory_service", "get_active_household_id"]


async def get_inventory_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InventoryService:
    repository = InventoryRepository(db)
    return InventoryService(repository, catalog_service=CatalogService(db_session=db))


async def get_active_household_id(
    current_user: Annotated[User, Depends(get_current_user)],
    household_id: Annotated[UUID, Depends(get_active_household)],
) -> UUID:
    _ = current_user
    return household_id
