from __future__ import annotations

from typing import Protocol


class PushServiceInterface(Protocol):
    async def send(self, token: str, title: str, body: str) -> bool: ...


class MockPushService:
    async def send(self, token: str, title: str, body: str) -> bool:
        _ = (token, title, body)
        return True


class FCMPushService:
    async def send(self, token: str, title: str, body: str) -> bool:
        _ = (token, title, body)
        return True
