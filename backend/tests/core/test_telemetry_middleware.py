import httpx
import pytest


@pytest.mark.asyncio
async def test_health_request_returns_request_id_header(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) == 36


@pytest.mark.asyncio
async def test_middleware_does_not_break_existing_endpoints(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_middleware_handles_404_gracefully(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/v1/nonexistent-path")
    assert response.status_code in (404, 405)
    assert "x-request-id" in response.headers
