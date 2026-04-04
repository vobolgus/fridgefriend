# pyright: reportExplicitAny=false

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID


class HouseholdEventBus:
    def __init__(self) -> None:
        self._subscribers: defaultdict[UUID, set[asyncio.Queue[dict[str, object]]]] = defaultdict(set)

    @asynccontextmanager
    async def subscribe(self, household_id: UUID) -> AsyncIterator[asyncio.Queue[dict[str, object]]]:
        queue: asyncio.Queue[dict[str, object]] = asyncio.Queue()
        self._subscribers[household_id].add(queue)
        try:
            yield queue
        finally:
            subscribers = self._subscribers.get(household_id)
            if subscribers is not None:
                _ = subscribers.discard(queue)
                if not subscribers:
                    _ = self._subscribers.pop(household_id, None)

    async def publish(self, household_id: UUID, event: dict[str, object]) -> None:
        for queue in list(self._subscribers.get(household_id, set())):
            await queue.put(event)


household_event_bus = HouseholdEventBus()
