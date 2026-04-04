from __future__ import annotations

import uuid

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.household import Household, HouseholdMember, HouseholdRole


class HouseholdRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def session(self) -> AsyncSession:
        return self._session

    def _household_with_members(self) -> Select[tuple[Household]]:
        return select(Household).options(selectinload(Household.members).selectinload(HouseholdMember.user))

    async def list_for_user(self, user_id: uuid.UUID) -> list[Household]:
        statement = (
            self._household_with_members()
            .join(HouseholdMember, HouseholdMember.household_id == Household.id)
            .where(HouseholdMember.user_id == user_id)
            .order_by(HouseholdMember.created_at.asc(), Household.created_at.asc())
        )
        result = await self._session.execute(statement)
        return list(result.scalars().unique().all())

    async def get_for_user(self, household_id: uuid.UUID, user_id: uuid.UUID) -> Household | None:
        statement = (
            self._household_with_members()
            .join(HouseholdMember, HouseholdMember.household_id == Household.id)
            .where(Household.id == household_id, HouseholdMember.user_id == user_id)
        )
        result = await self._session.execute(statement)
        return result.scalars().unique().one_or_none()

    async def get_by_id(self, household_id: uuid.UUID) -> Household | None:
        result = await self._session.execute(
            self._household_with_members().where(Household.id == household_id),
        )
        return result.scalars().unique().one_or_none()

    async def get_membership(self, household_id: uuid.UUID, user_id: uuid.UUID) -> HouseholdMember | None:
        result = await self._session.execute(
            select(HouseholdMember).where(
                HouseholdMember.household_id == household_id,
                HouseholdMember.user_id == user_id,
            ),
        )
        return result.scalar_one_or_none()

    async def list_memberships_for_user(self, user_id: uuid.UUID) -> list[HouseholdMember]:
        result = await self._session.execute(
            select(HouseholdMember)
            .options(selectinload(HouseholdMember.household).selectinload(Household.members).selectinload(HouseholdMember.user))
            .where(HouseholdMember.user_id == user_id)
            .order_by(HouseholdMember.created_at.asc()),
        )
        return list(result.scalars().unique().all())

    async def get_by_invite_code(self, invite_code: str) -> Household | None:
        result = await self._session.execute(
            self._household_with_members().where(Household.invite_code == invite_code),
        )
        return result.scalars().unique().one_or_none()

    async def create(self, *, name: str, invite_code: str, owner_user_id: uuid.UUID) -> Household:
        household = Household(name=name, invite_code=invite_code)
        self._session.add(household)
        await self._session.flush()

        self._session.add(
            HouseholdMember(
                household_id=household.id,
                user_id=owner_user_id,
                role=HouseholdRole.OWNER,
            ),
        )
        await self._session.commit()
        refreshed = await self.get_by_id(household.id)
        if refreshed is None:
            raise RuntimeError("Failed to load created household")
        return refreshed

    async def add_member(
        self,
        *,
        household_id: uuid.UUID,
        user_id: uuid.UUID,
        role: HouseholdRole = HouseholdRole.MEMBER,
    ) -> Household:
        self._session.add(HouseholdMember(household_id=household_id, user_id=user_id, role=role))
        await self._session.commit()
        household = await self.get_by_id(household_id)
        if household is None:
            raise RuntimeError("Failed to load household after adding member")
        return household

    async def update_name(self, household: Household, name: str) -> Household:
        household.name = name
        household.version += 1
        await self._session.commit()
        refreshed = await self.get_by_id(household.id)
        if refreshed is None:
            raise RuntimeError("Failed to load updated household")
        return refreshed

    async def remove_membership(self, membership: HouseholdMember) -> None:
        await self._session.delete(membership)
        await self._session.commit()

    async def delete_household(self, household: Household) -> None:
        await self._session.delete(household)
        await self._session.commit()

    async def update_member_role(self, membership: HouseholdMember, role: HouseholdRole) -> HouseholdMember:
        membership.role = role
        await self._session.commit()
        await self._session.refresh(membership)
        return membership
