from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Generator
from collections import defaultdict
from typing import cast
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.modules.households.event_bus import (
    InMemoryHouseholdEventBus,
    RedisHouseholdEventBus,
    get_event_bus,
    reset_event_bus_cache,
)


class FakePipeline:
    def __init__(self, redis: "FakeRedis") -> None:
        self._redis: FakeRedis = redis
        self._operations: list[tuple[str, tuple[object, ...]]] = []

    def rpush(self, key: str, value: str) -> "FakePipeline":
        self._operations.append(("rpush", (key, value)))
        return self

    def ltrim(self, key: str, start: int, end: int) -> "FakePipeline":
        self._operations.append(("ltrim", (key, start, end)))
        return self

    def expire(self, key: str, ttl: int) -> "FakePipeline":
        self._operations.append(("expire", (key, ttl)))
        return self

    def publish(self, channel: str, payload: str) -> "FakePipeline":
        self._operations.append(("publish", (channel, payload)))
        return self

    async def execute(self) -> list[object]:
        results: list[object] = []
        for operation, args in self._operations:
            method = cast(Callable[..., Awaitable[object]], getattr(self._redis, operation))
            results.append(await method(*args))
        self._operations.clear()
        return results


class FakePubSub:
    def __init__(self, redis: "FakeRedis") -> None:
        self._redis: FakeRedis = redis
        self._channels: set[str] = set()
        self._queue: asyncio.Queue[dict[str, object]] = asyncio.Queue()
        self.closed: bool = False

    async def subscribe(self, channel: str) -> None:
        self._channels.add(channel)
        self._redis.register_subscriber(channel, self)

    async def unsubscribe(self, channel: str) -> None:
        self._channels.discard(channel)
        self._redis.unregister_subscriber(channel, self)

    async def get_message(self, ignore_subscribe_messages: bool = True, timeout: float = 1.0) -> dict[str, object] | None:
        _ = ignore_subscribe_messages
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except TimeoutError:
            return None

    async def push_message(self, payload: str) -> None:
        await self._queue.put({"type": "message", "data": payload})

    async def close(self) -> None:
        self.closed = True
        for channel in list(self._channels):
            self._redis.unregister_subscriber(channel, self)
        self._channels.clear()


class FakeRedis:
    def __init__(self) -> None:
        self._lists: defaultdict[str, list[str]] = defaultdict(list)
        self._subscribers: defaultdict[str, set[FakePubSub]] = defaultdict(set)
        self.expiry: dict[str, int] = {}

    def pipeline(self, transaction: bool = True, shard_hint: str | None = None) -> FakePipeline:
        _ = (transaction, shard_hint)
        return FakePipeline(self)

    def pubsub(self, **kwargs: object) -> FakePubSub:
        _ = kwargs
        return FakePubSub(self)

    def register_subscriber(self, channel: str, subscriber: FakePubSub) -> None:
        self._subscribers[channel].add(subscriber)

    def unregister_subscriber(self, channel: str, subscriber: FakePubSub) -> None:
        subscribers = self._subscribers.get(channel)
        if subscribers is None:
            return
        subscribers.discard(subscriber)
        if not subscribers:
            _ = self._subscribers.pop(channel, None)

    async def rpush(self, key: str, value: str) -> int:
        self._lists[key].append(value)
        return len(self._lists[key])

    async def ltrim(self, key: str, start: int, end: int) -> bool:
        values = self._lists.get(key, [])
        length = len(values)
        normalized_start = max(length + start, 0) if start < 0 else start
        normalized_end = length + end if end < 0 else end
        normalized_end = min(normalized_end, length - 1)
        if normalized_start > normalized_end or not values:
            self._lists[key] = []
            return True
        self._lists[key] = values[normalized_start : normalized_end + 1]
        return True

    async def expire(self, key: str, ttl: int) -> bool:
        self.expiry[key] = ttl
        return True

    async def publish(self, channel: str, payload: str) -> int:
        subscribers = list(self._subscribers.get(channel, set()))
        for subscriber in subscribers:
            await subscriber.push_message(payload)
        return len(subscribers)

    async def lrange(self, key: str, start: int, end: int) -> tuple[object, ...]:
        values = self._lists.get(key, [])
        if end == -1:
            return tuple(values[start:])
        return tuple(values[start : end + 1])


@pytest.fixture(autouse=True)
def reset_cached_bus() -> Generator[None, None, None]:
    reset_event_bus_cache()
    yield
    reset_event_bus_cache()


@pytest.mark.asyncio
async def test_publish_and_subscribe() -> None:
    redis = FakeRedis()
    bus = RedisHouseholdEventBus(redis)
    household_id = uuid4()

    async with bus.subscribe(household_id) as queue:
        published = await bus.publish(household_id, {"action": "added", "item_id": "item-1"})
        event = await asyncio.wait_for(queue.get(), timeout=1)

    assert event == published
    assert event["action"] == "added"
    assert isinstance(event["event_id"], str)


@pytest.mark.asyncio
async def test_event_history_stored() -> None:
    redis = FakeRedis()
    bus = RedisHouseholdEventBus(redis)
    household_id = uuid4()

    first = await bus.publish(household_id, {"action": "added", "item_id": "item-1"})
    second = await bus.publish(household_id, {"action": "updated", "item_id": "item-1"})

    replayed = await bus.get_events_after(household_id, str(first["event_id"]))

    assert replayed == [second]
    assert redis.expiry[f"household:{household_id}:event_history"] == 3600


@pytest.mark.asyncio
async def test_reconnect_replays_missed() -> None:
    redis = FakeRedis()
    bus = RedisHouseholdEventBus(redis)
    household_id = uuid4()

    first = await bus.publish(household_id, {"action": "added", "item_id": "item-1"})
    second = await bus.publish(household_id, {"action": "updated", "item_id": "item-1"})
    third = await bus.publish(household_id, {"action": "removed", "item_id": "item-1"})

    replayed = await bus.get_events_after(household_id, str(first["event_id"]))

    assert replayed == [second, third]


@pytest.mark.asyncio
async def test_backpressure_drops_oldest() -> None:
    bus = InMemoryHouseholdEventBus()
    household_id = uuid4()

    async with bus.subscribe(household_id) as queue:
        for index in range(105):
            _ = await bus.publish(household_id, {"sequence": index})

        events = [queue.get_nowait() for _ in range(queue.qsize())]

    sequences = [event["sequence"] for event in events if isinstance(event.get("sequence"), int)]
    assert len(sequences) == 100
    assert sequences[0] == 5
    assert sequences[-1] == 104


def test_fallback_to_in_memory() -> None:
    with patch("app.modules.households.event_bus.get_redis_client", return_value=None):
        bus = get_event_bus()

    assert isinstance(bus, InMemoryHouseholdEventBus)
