# pyright: reportExplicitAny=false

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import Request


async def household_event_stream(
    request: Request,
    queue: asyncio.Queue[dict[str, object]],
) -> AsyncIterator[str]:
    yield ": connected\n\n"
    while True:
        if await request.is_disconnected():
            break

        try:
            event = await asyncio.wait_for(queue.get(), timeout=15)
            yield f"data: {json.dumps(event, default=str)}\n\n"
        except TimeoutError:
            yield ": keep-alive\n\n"
