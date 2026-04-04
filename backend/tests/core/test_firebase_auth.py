# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownLambdaType=false

from __future__ import annotations

from typing import cast

import pytest
from fastapi import HTTPException
from pytest import MonkeyPatch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.firebase import FirebaseAuthInterface, MockFirebaseAuth
from app.models.user import User


def test_firebase_auth_interface_protocol() -> None:
    assert getattr(FirebaseAuthInterface, "_is_protocol", False) is True


@pytest.mark.asyncio
async def test_mock_firebase_verifies_token() -> None:
    firebase_auth = MockFirebaseAuth()

    decoded = await firebase_auth.verify_token("valid-token")

    assert decoded == {"uid": "firebase-test-uid", "email": "test@fridgefriend.app"}


@pytest.mark.asyncio
async def test_mock_firebase_rejects_expired() -> None:
    firebase_auth = MockFirebaseAuth()

    with pytest.raises(ValueError, match="Token expired"):
        await firebase_auth.verify_token("expired")


@pytest.mark.asyncio
async def test_firebase_auth_creates_user_from_token(
    monkeypatch: MonkeyPatch,
    db_session: AsyncSession,
) -> None:
    monkeypatch.setattr(settings, "AUTH_MOCK", False)

    class FirebaseAuthWithoutEmail:
        async def verify_token(self, token: str) -> dict[str, str]:
            assert token == "firebase-token"
            return {"uid": "firebase-user-123"}

    service = cast(FirebaseAuthInterface, FirebaseAuthWithoutEmail())
    monkeypatch.setattr("app.core.auth.get_firebase_auth_service", lambda: service)

    user = await get_current_user("Bearer firebase-token", db=db_session)

    stored_user = await db_session.execute(
        select(User).where(User.email == "firebase-user-123@firebase.local")
    )

    assert user.email == "firebase-user-123@firebase.local"
    assert stored_user.scalars().first() is not None


@pytest.mark.asyncio
async def test_firebase_auth_rejects_missing_token(
    monkeypatch: MonkeyPatch,
    db_session: AsyncSession,
) -> None:
    monkeypatch.setattr(settings, "AUTH_MOCK", False)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(None, db=db_session)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing authorization"
