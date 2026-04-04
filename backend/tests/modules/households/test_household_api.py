# pyright: reportAny=false, reportUnusedParameter=false, reportUnusedCallResult=false, reportMissingImports=false, reportUnknownVariableType=false

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.household import Household, HouseholdMember, HouseholdRole
from app.models.user import User
from app.modules.inventory.dependencies import get_current_user


def _headers(test_headers: dict[str, str], key: str) -> dict[str, str]:
    return {**test_headers, "Idempotency-Key": key}


@pytest_asyncio.fixture
async def household_test_user(app: FastAPI, db_session: AsyncSession) -> AsyncIterator[User]:
    user = User(email="households-api@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    async def override_get_current_user() -> User:
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield user

    app.dependency_overrides.clear()


async def _create_household_with_member(
    db_session: AsyncSession,
    user: User,
    *,
    name: str,
    invite_code: str,
    role: HouseholdRole = HouseholdRole.OWNER,
) -> Household:
    household = Household(name=name, invite_code=invite_code)
    db_session.add(household)
    await db_session.flush()
    db_session.add(HouseholdMember(household_id=household.id, user_id=user.id, role=role))
    await db_session.commit()
    await db_session.refresh(household)
    return household


@pytest.mark.asyncio
async def test_create_household(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    household_test_user: User,
) -> None:
    response = await client.post(
        "/v1/households",
        headers=_headers(test_headers, "households-create"),
        json={"name": "Family Kitchen"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"]
    assert payload["name"] == "Family Kitchen"
    assert payload["invite_code"]


@pytest.mark.asyncio
async def test_list_user_households(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    household_test_user: User,
) -> None:
    response = await client.get("/v1/households", headers=test_headers)

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["name"] == f"{household_test_user.email}'s Kitchen"


@pytest.mark.asyncio
async def test_update_household_name(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    household_test_user: User,
    db_session: AsyncSession,
) -> None:
    household = await _create_household_with_member(
        db_session,
        household_test_user,
        name="Old Name",
        invite_code="invite-old-name",
    )

    response = await client.patch(
        f"/v1/households/{household.id}",
        headers=_headers(test_headers, "households-update-name"),
        json={"name": "Updated Name"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_get_household_detail(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    household_test_user: User,
    db_session: AsyncSession,
) -> None:
    household = await _create_household_with_member(
        db_session,
        household_test_user,
        name="Family Home",
        invite_code="invite-detail-house",
    )

    response = await client.get(f"/v1/households/{household.id}", headers=test_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(household.id)
    assert len(payload["members"]) == 1
    assert payload["members"][0]["user_id"] == str(household_test_user.id)


@pytest.mark.asyncio
async def test_join_household_by_invite_code(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    household_test_user: User,
    db_session: AsyncSession,
) -> None:
    owner = User(email="household-owner@example.com")
    db_session.add(owner)
    await db_session.commit()
    await db_session.refresh(owner)
    household = await _create_household_with_member(
        db_session,
        owner,
        name="Shared Kitchen",
        invite_code="joinable-invite-code",
    )

    response = await client.post(
        "/v1/households/join",
        headers=_headers(test_headers, "households-join"),
        json={"invite_code": household.invite_code},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(household.id)
    result = await db_session.execute(
        select(HouseholdMember).where(
            HouseholdMember.household_id == household.id,
            HouseholdMember.user_id == household_test_user.id,
        ),
    )
    membership = result.scalar_one_or_none()
    assert membership is not None


@pytest.mark.asyncio
async def test_leave_household(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    household_test_user: User,
    db_session: AsyncSession,
) -> None:
    owner = User(email="leave-owner@example.com")
    db_session.add(owner)
    await db_session.commit()
    await db_session.refresh(owner)
    household = await _create_household_with_member(
        db_session,
        owner,
        name="Leave Kitchen",
        invite_code="leave-invite-code",
    )
    db_session.add(
        HouseholdMember(
            household_id=household.id,
            user_id=household_test_user.id,
            role=HouseholdRole.MEMBER,
        ),
    )
    await db_session.commit()

    response = await client.post(
        f"/v1/households/{household.id}/leave",
        headers=_headers(test_headers, "households-leave"),
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_remove_member_as_owner(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    household_test_user: User,
    db_session: AsyncSession,
) -> None:
    household = await _create_household_with_member(
        db_session,
        household_test_user,
        name="Owner Kitchen",
        invite_code="owner-remove-code",
    )
    member = User(email="remove-member@example.com")
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)
    db_session.add(
        HouseholdMember(
            household_id=household.id,
            user_id=member.id,
            role=HouseholdRole.MEMBER,
        ),
    )
    await db_session.commit()

    response = await client.delete(
        f"/v1/households/{household.id}/members/{member.id}",
        headers=_headers(test_headers, "households-remove-member"),
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_create_household_marks_new_household_active(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    household_test_user: User,
) -> None:
    _ = household_test_user
    create_response = await client.post(
        "/v1/households",
        headers=_headers(test_headers, "households-active-create"),
        json={"name": "Weekend House"},
    )

    assert create_response.status_code == 201
    assert create_response.json()["is_active"] is True

    list_response = await client.get("/v1/households", headers=test_headers)
    assert list_response.status_code == 200
    active_households = [household for household in list_response.json() if household["is_active"]]
    assert len(active_households) == 1
    assert active_households[0]["name"] == "Weekend House"


@pytest.mark.asyncio
async def test_patch_household_can_switch_active_household(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    household_test_user: User,
    db_session: AsyncSession,
) -> None:
    first = await _create_household_with_member(
        db_session,
        household_test_user,
        name="Primary",
        invite_code="primary-household",
    )
    second = await _create_household_with_member(
        db_session,
        household_test_user,
        name="Secondary",
        invite_code="secondary-household",
    )

    first_membership = await db_session.execute(
        select(HouseholdMember).where(
            HouseholdMember.household_id == first.id,
            HouseholdMember.user_id == household_test_user.id,
        )
    )
    first_membership_obj = first_membership.scalar_one()
    first_membership_obj.is_active = True
    await db_session.commit()

    response = await client.patch(
        f"/v1/households/{second.id}",
        headers=_headers(test_headers, "households-switch-active"),
        json={"is_active": True},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is True

    list_response = await client.get("/v1/households", headers=test_headers)
    active_households = [household for household in list_response.json() if household["is_active"]]
    assert len(active_households) == 1
    assert active_households[0]["id"] == str(second.id)
