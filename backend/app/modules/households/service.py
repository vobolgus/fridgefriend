from __future__ import annotations

import secrets
import uuid

from app.models.household import Household, HouseholdMember, HouseholdRole
from app.models.user import User

from .repository import HouseholdRepository
from .schemas import HouseholdCreate, HouseholdUpdate

DEFAULT_INVITE_CODE_LENGTH = 20


class HouseholdNotFoundError(Exception):
    pass


class HouseholdAccessError(Exception):
    pass


class HouseholdInviteCodeError(Exception):
    pass


class HouseholdService:
    def __init__(self, repository: HouseholdRepository) -> None:
        self._repository = repository

    async def list_households(self, user: User) -> list[Household]:
        await self.ensure_default_household(user)
        return await self._repository.list_for_user(user.id)

    async def create_household(self, user: User, payload: HouseholdCreate) -> Household:
        return await self._repository.create(
            name=payload.name,
            invite_code=await self._generate_invite_code(),
            owner_user_id=user.id,
        )

    async def get_household(self, user: User, household_id: uuid.UUID) -> Household:
        household = await self._repository.get_for_user(household_id, user.id)
        if household is None:
            raise HouseholdNotFoundError
        return household

    async def update_household(
        self,
        user: User,
        household_id: uuid.UUID,
        payload: HouseholdUpdate,
    ) -> Household:
        household = await self.get_household(user, household_id)
        if payload.name is None:
            return household
        return await self._repository.update_name(household, payload.name)

    async def join_household(self, user: User, invite_code: str) -> Household:
        household = await self._repository.get_by_invite_code(invite_code)
        if household is None:
            raise HouseholdInviteCodeError

        membership = await self._repository.get_membership(household.id, user.id)
        if membership is not None:
            return household

        return await self._repository.add_member(household_id=household.id, user_id=user.id)

    async def leave_household(self, user: User, household_id: uuid.UUID) -> None:
        household = await self.get_household(user, household_id)
        membership = await self._repository.get_membership(household.id, user.id)
        if membership is None:
            raise HouseholdNotFoundError

        members_before = sorted(household.members, key=lambda member: member.created_at)
        await self._repository.remove_membership(membership)

        remaining = [member for member in members_before if member.user_id != user.id]
        if not remaining:
            refreshed_household = await self._repository.get_by_id(household.id)
            if refreshed_household is not None:
                await self._repository.delete_household(refreshed_household)
            return

        if membership.role == HouseholdRole.OWNER and not any(member.role == HouseholdRole.OWNER for member in remaining):
            promoted = await self._repository.get_membership(household.id, remaining[0].user_id)
            if promoted is not None:
                await self._repository.update_member_role(promoted, HouseholdRole.OWNER)

    async def remove_member(self, actor: User, household_id: uuid.UUID, user_id: uuid.UUID) -> None:
        actor_membership = await self._repository.get_membership(household_id, actor.id)
        if actor_membership is None:
            raise HouseholdNotFoundError
        if actor_membership.role != HouseholdRole.OWNER:
            raise HouseholdAccessError

        membership = await self._repository.get_membership(household_id, user_id)
        if membership is None:
            raise HouseholdNotFoundError

        await self._repository.remove_membership(membership)

        household = await self._repository.get_by_id(household_id)
        if household is None:
            return
        if not household.members:
            await self._repository.delete_household(household)

    async def get_active_household_id(self, user: User) -> uuid.UUID:
        memberships = await self._repository.list_memberships_for_user(user.id)
        if memberships:
            return memberships[0].household_id

        household = await self.ensure_default_household(user)
        return household.id

    async def ensure_default_household(self, user: User) -> Household:
        memberships = await self._repository.list_memberships_for_user(user.id)
        if memberships:
            return memberships[0].household

        return await self._repository.create(
            name=f"{user.email}'s Kitchen",
            invite_code=await self._generate_invite_code(),
            owner_user_id=user.id,
        )

    async def _generate_invite_code(self) -> str:
        while True:
            invite_code = secrets.token_urlsafe(8)[:DEFAULT_INVITE_CODE_LENGTH]
            if await self._repository.get_by_invite_code(invite_code) is None:
                return invite_code
