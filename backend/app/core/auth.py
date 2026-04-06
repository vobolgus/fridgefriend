# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportArgumentType=false, reportInvalidCast=false, reportCallInDefaultInitializer=false, reportUnnecessaryComparison=false

from __future__ import annotations

import secrets
from typing import Annotated, cast

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.firebase import FirebaseAuthInterface, FirebaseAuthService, MockFirebaseAuth
from app.models.household import Household, HouseholdMember, HouseholdRole
from app.models.user import User

DEFAULT_INVITE_CODE_LENGTH = 20


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    *,
    request: Request = cast(Request, None),
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if settings.AUTH_MOCK:
        user = await _mock_auth(authorization, db)
    else:
        user = await _firebase_auth(authorization, db)

    request_state = getattr(request, "state", None)
    if request_state is not None:
        request_state.user_id = str(user.id)
    return user


async def _mock_auth(authorization: str | None, db: AsyncSession) -> User:
    if authorization != "Bearer test-token":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    result = await db.execute(select(User).where(User.email == "dev@fridgefriend.local"))
    user = result.scalars().first()
    if user is None:
        user = User(email="dev@fridgefriend.local")
        db.add(user)
        await db.commit()
        await db.refresh(user)
    await _ensure_default_household(user, db)
    return user


def get_firebase_auth_service() -> FirebaseAuthInterface:
    if settings.FIREBASE_PROJECT_ID:
        return FirebaseAuthService(project_id=settings.FIREBASE_PROJECT_ID)
    if not settings.AUTH_MOCK:
        raise RuntimeError(
            "AUTH_MOCK is disabled but FIREBASE_PROJECT_ID is not set. "
            + "Set FIREBASE_PROJECT_ID to a valid Firebase project, "
            + "or enable AUTH_MOCK for development."
        )
    return MockFirebaseAuth()


async def _firebase_auth(authorization: str | None, db: AsyncSession) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization")

    token = authorization.removeprefix("Bearer ")
    firebase_service: FirebaseAuthInterface = get_firebase_auth_service()

    try:
        decoded: dict[str, object] = await firebase_service.verify_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    uid = decoded.get("uid")
    if not isinstance(uid, str) or not uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    email_value = decoded.get("email")
    email = email_value if isinstance(email_value, str) and email_value else f"{uid}@firebase.local"

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user is None:
        try:
            user = User(email=email)
            db.add(user)
            await db.commit()
            await db.refresh(user)
        except Exception:
            # Race condition: another request created the user concurrently.
            await db.rollback()
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalars().first()
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create or find user",
                )
    user._firebase_uid = uid  # type: ignore[attr-defined]  # transient attr for request-scoped UID check
    await _ensure_default_household(user, db)
    return user


async def _ensure_default_household(user: User, db: AsyncSession) -> None:
    count_result = await db.execute(
        select(func.count())
        .select_from(HouseholdMember)
        .where(HouseholdMember.user_id == user.id)
    )
    count = count_result.scalar() or 0

    if count != 0:
        return

    household = Household(
        name=f"{user.email}'s Kitchen",
        invite_code=secrets.token_urlsafe(8)[:DEFAULT_INVITE_CODE_LENGTH],
    )
    db.add(household)
    await db.flush()

    member = HouseholdMember(
        household_id=household.id,
        user_id=user.id,
        role=HouseholdRole.OWNER,
        is_active=True,
    )
    db.add(member)
    await db.commit()
    await db.refresh(user)
