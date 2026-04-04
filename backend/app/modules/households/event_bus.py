from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import inspect
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import AsyncContextManager, Protocol, cast
from uuid import UUID, uuid4

from app.core.redis import get_redis_client

try:
    from redis.exceptions import RedisError

    redis_exception_types: tuple[type[Exception], ...] = (RedisError, OSError, RuntimeError)
except ImportError:
    redis_exception_types = (OSError, RuntimeError)

logger = logging.getLogger(__name__)

_QUEUE_MAXSIZE = 100
_EVENT_HISTORY_LIMIT = 500
_EVENT_HISTORY_TTL_SECONDS = 3600


class HouseholdEventBus(Protocol):
    async def publish(self, household_id: UUID, event: dict[str, object]) -> dict[str, object]: ...

    def subscribe(self, household_id: UUID) -> AsyncContextManager[asyncio.Queue[dict[str, object]]]: ...

    async def get_events_after(self, household_id: UUID, last_event_id: str) -> list[dict[str, object]]: ...


class RedisPipelineProtocol(Protocol):
    def rpush(self, key: str, value: str) -> object: ...

    def ltrim(self, key: str, start: int, end: int) -> object: ...

    def expire(self, key: str, ttl: int) -> object: ...

    def publish(self, channel: str, payload: str) -> object: ...

    async def execute(self) -> list[object]: ...


class RedisPubSubProtocol(Protocol):
    async def subscribe(self, channel: str) -> None: ...

    async def unsubscribe(self, channel: str) -> object: ...

    async def get_message(self, ignore_subscribe_messages: bool = True, timeout: float = 1.0) -> dict[str, object] | None: ...

    async def close(self) -> None: ...


class RedisClientProtocol(Protocol):
    def pipeline(self, transaction: bool = True, shard_hint: str | None = None) -> RedisPipelineProtocol: ...

    def pubsub(self, **kwargs: object) -> RedisPubSubProtocol: ...

    async def lrange(self, key: str, start: int, end: int) -> tuple[object, ...] | list[object]: ...


def _channel_key(household_id: UUID) -> str:
    return f"household:{household_id}:events"


def _history_key(household_id: UUID) -> str:
    return f"household:{household_id}:event_history"


def _with_event_id(event: dict[str, object]) -> dict[str, object]:
    if "event_id" in event:
        return dict(event)
    return {**event, "event_id": str(uuid4())}


def _decode_event_payload(payload: str) -> dict[str, object] | None:
    parsed_object = cast(object, json.loads(payload))
    if not isinstance(parsed_object, dict):
        return None
    parsed = cast(dict[object, object], parsed_object)
    return {str(key): value for key, value in parsed.items()}


async def _enqueue_event(queue: asyncio.Queue[dict[str, object]], event: dict[str, object]) -> None:
    if queue.full():
        with contextlib.suppress(asyncio.QueueEmpty):
            _ = queue.get_nowait()
    await queue.put(event)


class RedisHouseholdEventBus:
    def __init__(self, redis_client: RedisClientProtocol | None = None) -> None:
        self._redis: RedisClientProtocol | None = redis_client

    @asynccontextmanager
    async def _redis_session(self) -> AsyncIterator[RedisClientProtocol | None]:
        if self._redis is not None:
            yield self._redis
            return

        redis_client = cast(RedisClientProtocol | None, get_redis_client())
        try:
            yield redis_client
        finally:
            if redis_client is not None:
                close_method = getattr(redis_client, "aclose", None)
                if callable(close_method):
                    maybe_awaitable = close_method()
                    if inspect.isawaitable(maybe_awaitable):
                        await maybe_awaitable

    async def publish(self, household_id: UUID, event: dict[str, object]) -> dict[str, object]:
        event_with_id = _with_event_id(event)
        payload = json.dumps(event_with_id, default=str)
        history_key = _history_key(household_id)

        async with self._redis_session() as redis_client:
            if redis_client is None:
                return event_with_id

            pipeline = redis_client.pipeline()
            _ = pipeline.rpush(history_key, payload)
            _ = pipeline.ltrim(history_key, -_EVENT_HISTORY_LIMIT, -1)
            _ = pipeline.expire(history_key, _EVENT_HISTORY_TTL_SECONDS)
            _ = pipeline.publish(_channel_key(household_id), payload)
            _ = await pipeline.execute()
        return event_with_id

    @asynccontextmanager
    async def subscribe(self, household_id: UUID) -> AsyncIterator[asyncio.Queue[dict[str, object]]]:
        async with self._redis_session() as redis_client:
            if redis_client is None:
                queue: asyncio.Queue[dict[str, object]] = asyncio.Queue(maxsize=_QUEUE_MAXSIZE)
                yield queue
                return

            queue = asyncio.Queue[dict[str, object]](maxsize=_QUEUE_MAXSIZE)
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(_channel_key(household_id))

            async def pump() -> None:
                try:
                    while True:
                        message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                        if message is None:
                            await asyncio.sleep(0.05)
                            continue

                        raw_data = message.get("data")
                        if isinstance(raw_data, bytes):
                            decoded = raw_data.decode("utf-8")
                        elif isinstance(raw_data, str):
                            decoded = raw_data
                        else:
                            continue

                        typed_event = _decode_event_payload(decoded)
                        if typed_event is not None:
                            await _enqueue_event(queue, typed_event)
                except asyncio.CancelledError:
                    raise

            task = asyncio.create_task(pump())
            try:
                yield queue
            finally:
                _ = task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
                with contextlib.suppress(*redis_exception_types):
                    _ = await pubsub.unsubscribe(_channel_key(household_id))
                with contextlib.suppress(*redis_exception_types):
                    _ = await pubsub.close()

    async def get_events_after(self, household_id: UUID, last_event_id: str) -> list[dict[str, object]]:
        async with self._redis_session() as redis_client:
            if redis_client is None:
                return []

            raw_events = await redis_client.lrange(_history_key(household_id), 0, -1)
        parsed_events: list[dict[str, object]] = []
        found = False

        for raw_event in raw_events:
            if isinstance(raw_event, bytes):
                decoded = raw_event.decode("utf-8")
            else:
                decoded = str(raw_event)
            typed_event = _decode_event_payload(decoded)
            if typed_event is None:
                continue
            if found:
                parsed_events.append(typed_event)
                continue
            if typed_event.get("event_id") == last_event_id:
                found = True

        return parsed_events if found else []


class InMemoryHouseholdEventBus:
    def __init__(self) -> None:
        self._subscribers: defaultdict[UUID, set[asyncio.Queue[dict[str, object]]]] = defaultdict(set)
        self._history: defaultdict[UUID, list[dict[str, object]]] = defaultdict(list)

    @asynccontextmanager
    async def subscribe(self, household_id: UUID) -> AsyncIterator[asyncio.Queue[dict[str, object]]]:
        queue: asyncio.Queue[dict[str, object]] = asyncio.Queue(maxsize=_QUEUE_MAXSIZE)
        self._subscribers[household_id].add(queue)
        try:
            yield queue
        finally:
            subscribers = self._subscribers.get(household_id)
            if subscribers is not None:
                _ = subscribers.discard(queue)
                if not subscribers:
                    _ = self._subscribers.pop(household_id, None)

    async def publish(self, household_id: UUID, event: dict[str, object]) -> dict[str, object]:
        event_with_id = _with_event_id(event)
        history = self._history[household_id]
        history.append(event_with_id)
        if len(history) > _EVENT_HISTORY_LIMIT:
            del history[:-_EVENT_HISTORY_LIMIT]

        for queue in list(self._subscribers.get(household_id, set())):
            await _enqueue_event(queue, event_with_id)
        return event_with_id

    async def get_events_after(self, household_id: UUID, last_event_id: str) -> list[dict[str, object]]:
        history = self._history.get(household_id, [])
        for index, event in enumerate(history):
            if event.get("event_id") == last_event_id:
                return history[index + 1 :]
        return []


_cached_event_bus: HouseholdEventBus | None = None


def get_event_bus() -> HouseholdEventBus:
    global _cached_event_bus
    if _cached_event_bus is not None:
        return _cached_event_bus

    redis_client = get_redis_client()
    if redis_client is not None:
        _cached_event_bus = RedisHouseholdEventBus()
        return _cached_event_bus

    logger.warning("Redis unavailable for household event bus, using in-memory fallback")
    _cached_event_bus = InMemoryHouseholdEventBus()
    return _cached_event_bus


def reset_event_bus_cache() -> None:
    global _cached_event_bus
    _cached_event_bus = None


class _LazyHouseholdEventBus:
    def _resolve(self) -> HouseholdEventBus:
        return get_event_bus()

    def _fallback_from_error(self, error: Exception) -> HouseholdEventBus:
        global _cached_event_bus
        logger.warning("Redis household event bus unavailable, falling back to in-memory bus", exc_info=error)
        if not isinstance(_cached_event_bus, InMemoryHouseholdEventBus):
            _cached_event_bus = InMemoryHouseholdEventBus()
        return _cached_event_bus

    async def publish(self, household_id: UUID, event: dict[str, object]) -> dict[str, object]:
        bus = self._resolve()
        try:
            return await bus.publish(household_id, event)
        except redis_exception_types as error:
            return await self._fallback_from_error(error).publish(household_id, event)

    @asynccontextmanager
    async def subscribe(self, household_id: UUID) -> AsyncIterator[asyncio.Queue[dict[str, object]]]:
        bus = self._resolve()
        try:
            async with bus.subscribe(household_id) as queue:
                yield queue
        except redis_exception_types as error:
            async with self._fallback_from_error(error).subscribe(household_id) as queue:
                yield queue

    async def get_events_after(self, household_id: UUID, last_event_id: str) -> list[dict[str, object]]:
        bus = self._resolve()
        try:
            return await bus.get_events_after(household_id, last_event_id)
        except redis_exception_types as error:
            return await self._fallback_from_error(error).get_events_after(household_id, last_event_id)


household_event_bus = _LazyHouseholdEventBus()
