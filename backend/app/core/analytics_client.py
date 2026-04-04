from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol


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


@dataclass(slots=True)
class AmplitudeClient:
    api_key: str

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
        _ = (user_id, event_type, payload)
