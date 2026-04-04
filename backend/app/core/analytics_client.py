from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol

import httpx


class AnalyticsInterface(Protocol):
    async def track(
        self,
        *,
        user_id: str,
        event_type: str,
        payload: Mapping[str, object],
    ) -> None: ...


@dataclass(slots=True)
class NoopAnalytics:
    async def track(
        self,
        *,
        user_id: str,
        event_type: str,
        payload: Mapping[str, object],
    ) -> None:
        _ = (user_id, event_type, payload)


AMPLITUDE_HTTP_API = "https://api2.amplitude.com/2/httpapi"


@dataclass(slots=True)
class AmplitudeClient:
    api_key: str
    _client: httpx.AsyncClient = field(default_factory=lambda: httpx.AsyncClient(timeout=5.0), repr=False)

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def track(
        self,
        *,
        user_id: str,
        event_type: str,
        payload: Mapping[str, object],
    ) -> None:
        if not self.is_configured:
            return
        try:
            await self._client.post(
                AMPLITUDE_HTTP_API,
                json={
                    "api_key": self.api_key,
                    "events": [
                        {
                            "user_id": user_id,
                            "event_type": event_type,
                            "event_properties": dict(payload),
                            "time": int(time.time() * 1000),
                        }
                    ],
                },
            )
        except Exception:
            pass
