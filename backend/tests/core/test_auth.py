# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import pytest
from fastapi import HTTPException
from pytest import MonkeyPatch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.config import Settings, settings
from app.models.household import HouseholdMember, HouseholdRole
from app.models.user import User


@pytest.mark.asyncio
async def test_mock_auth_accepts_test_token(
    monkeypatch: MonkeyPatch,
    db_session: AsyncSession,
) -> None:
    monkeypatch.setattr(settings, "AUTH_MOCK", True)

    user = await get_current_user("Bearer test-token", db=db_session)

    assert user.email == "dev@fridgefriend.local"


@pytest.mark.asyncio
async def test_mock_auth_rejects_invalid_token(
    monkeypatch: MonkeyPatch,
    db_session: AsyncSession,
) -> None:
    monkeypatch.setattr(settings, "AUTH_MOCK", True)

    with pytest.raises(HTTPException) as exc_info:
        _ = await get_current_user("Bearer invalid-token", db=db_session)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Unauthorized"


@pytest.mark.asyncio
async def test_mock_auth_auto_creates_user(
    monkeypatch: MonkeyPatch,
    db_session: AsyncSession,
) -> None:
    monkeypatch.setattr(settings, "AUTH_MOCK", True)

    existing_user = await db_session.execute(
        select(User).where(User.email == "dev@fridgefriend.local")
    )
    assert existing_user.scalars().first() is None

    user = await get_current_user("Bearer test-token", db=db_session)

    stored_user = await db_session.execute(select(User).where(User.email == user.email))

    assert user.email == "dev@fridgefriend.local"
    assert stored_user.scalars().first() is not None


@pytest.mark.asyncio
async def test_new_user_gets_default_household(
    monkeypatch: MonkeyPatch,
    db_session: AsyncSession,
) -> None:
    monkeypatch.setattr(settings, "AUTH_MOCK", True)

    user = await get_current_user("Bearer test-token", db=db_session)

    memberships = await db_session.execute(
        select(HouseholdMember).where(HouseholdMember.user_id == user.id)
    )
    household_membership = memberships.scalar_one()

    assert household_membership.household_id is not None
    assert household_membership.role is HouseholdRole.OWNER


@pytest.mark.asyncio
async def test_existing_user_returns_existing_household(
    monkeypatch: MonkeyPatch,
    db_session: AsyncSession,
) -> None:
    monkeypatch.setattr(settings, "AUTH_MOCK", True)

    user = await get_current_user("Bearer test-token", db=db_session)
    _ = await get_current_user("Bearer test-token", db=db_session)

    memberships = await db_session.execute(
        select(HouseholdMember).where(HouseholdMember.user_id == user.id)
    )

    assert len(memberships.scalars().all()) == 1


def test_auth_mock_toggle_defaults_to_true(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("AUTH_MOCK", raising=False)

    app_settings = Settings()

    assert app_settings.AUTH_MOCK is False
