from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User

from .repository import HouseholdRepository
from .activity_service import ActivityService
from .service import HouseholdService


async def get_household_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HouseholdService:
    return HouseholdService(HouseholdRepository(db))


async def get_activity_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ActivityService:
    return ActivityService(db)


async def get_active_household(
    current_user: Annotated[User, Depends(get_current_user)],
    household_service: Annotated[HouseholdService, Depends(get_household_service)],
) -> UUID:
    return await household_service.get_active_household_id(current_user)
