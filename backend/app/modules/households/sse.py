# pyright: reportExplicitAny=false

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import Request

from .event_bus import HouseholdEventBus


async def household_event_stream(
    request: Request,
    event_bus: HouseholdEventBus,
    household_id: UUID,
    queue: asyncio.Queue[dict[str, object]],
    last_event_id: str | None = None,
) -> AsyncIterator[str]:
    yield ": connected\n\n"

    if last_event_id:
        replay_events = await event_bus.get_events_after(household_id, last_event_id)
        for event in replay_events:
            event_id = event.get("event_id")
            if isinstance(event_id, str):
                yield f"id: {event_id}\n"
            yield f"data: {json.dumps(event, default=str)}\n\n"

    while True:
        if await request.is_disconnected():
            break

        try:
            event = await asyncio.wait_for(queue.get(), timeout=15)
            event_id = event.get("event_id")
            if isinstance(event_id, str):
                yield f"id: {event_id}\n"
            yield f"data: {json.dumps(event, default=str)}\n\n"
        except TimeoutError:
            yield ": keep-alive\n\n"
