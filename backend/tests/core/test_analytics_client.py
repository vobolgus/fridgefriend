from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.core.analytics_client import AmplitudeClient, NoopAnalytics


@pytest.mark.asyncio
async def test_noop_analytics_does_nothing() -> None:
    client = NoopAnalytics()
    await client.track(user_id="u1", event_type="test", payload={"key": "val"})


@pytest.mark.asyncio
async def test_amplitude_client_not_configured_skips_request() -> None:
    client = AmplitudeClient(api_key="")

    assert not client.is_configured

    with patch.object(client, "_client") as mock_http:
        await client.track(user_id="u1", event_type="test", payload={})
        mock_http.post.assert_not_called()


@pytest.mark.asyncio
async def test_amplitude_client_sends_event_to_http_api() -> None:
    client = AmplitudeClient(api_key="test-key-123")

    assert client.is_configured

    mock_response = AsyncMock()
    with patch.object(client, "_client") as mock_http:
        mock_http.post = AsyncMock(return_value=mock_response)

        await client.track(
            user_id="user-42",
            event_type="recipe_viewed",
            payload={"recipe_id": "r1"},
        )

        mock_http.post.assert_called_once()
        call_args = mock_http.post.call_args
        assert call_args[0][0] == "https://api2.amplitude.com/2/httpapi"
        body = call_args[1]["json"]
        assert body["api_key"] == "test-key-123"
        assert len(body["events"]) == 1
        event = body["events"][0]
        assert event["user_id"] == "user-42"
        assert event["event_type"] == "recipe_viewed"
        assert event["event_properties"] == {"recipe_id": "r1"}
        assert isinstance(event["time"], int)


@pytest.mark.asyncio
async def test_amplitude_client_suppresses_http_errors() -> None:
    client = AmplitudeClient(api_key="test-key")

    with patch.object(client, "_client") as mock_http:
        mock_http.post = AsyncMock(side_effect=ConnectionError("network down"))

        await client.track(user_id="u1", event_type="test", payload={})
