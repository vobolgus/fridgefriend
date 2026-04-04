from __future__ import annotations

import httpx
import pytest


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_200(client: httpx.AsyncClient) -> None:
    response = await client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")


@pytest.mark.asyncio
async def test_metrics_contain_request_duration(client: httpx.AsyncClient) -> None:
    response = await client.get("/metrics")

    assert response.status_code == 200
    assert "fridgefriend_http_request_duration_seconds" in response.text
