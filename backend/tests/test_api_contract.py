from __future__ import annotations

import httpx
import pytest


SPEC_ENDPOINTS = [
    ("POST", "/v1/items"),
    ("GET", "/v1/items"),
    ("GET", "/v1/items/{item_id}"),
    ("PATCH", "/v1/items/{item_id}"),
    ("PUT", "/v1/items/{item_id}"),
    ("DELETE", "/v1/items/{item_id}"),
    ("POST", "/v1/items/{item_id}/status"),
    ("POST", "/v1/items/{item_id}/undo"),
    ("POST", "/v1/scan/barcode"),
    ("POST", "/v1/scan/photo"),
    ("POST", "/v1/scan/photo/upload"),
    ("POST", "/v1/recommendations"),
    ("GET", "/v1/recipes/{recipe_id}"),
    ("POST", "/v1/plans"),
    ("GET", "/v1/plans/latest"),
    ("GET", "/v1/shopping-list"),
    ("DELETE", "/v1/plans/{plan_id}"),
    ("GET", "/v1/households"),
    ("POST", "/v1/households"),
    ("GET", "/v1/households/{household_id}"),
    ("PATCH", "/v1/households/{household_id}"),
    ("POST", "/v1/households/join"),
    ("POST", "/v1/households/{household_id}/leave"),
    ("DELETE", "/v1/households/{household_id}/members/{user_id}"),
    ("GET", "/v1/households/{household_id}/events"),
    ("GET", "/v1/households/{household_id}/activity"),
    ("GET", "/v1/notifications"),
    ("PATCH", "/v1/notifications"),
    ("POST", "/v1/notifications/devices"),
    ("DELETE", "/v1/notifications/devices/{token_id}"),
    ("POST", "/v1/analytics/events"),
    ("GET", "/health"),
]


@pytest.mark.asyncio
async def test_all_spec_endpoints_exist_in_openapi(client: httpx.AsyncClient) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    paths = schema["paths"]

    missing: list[str] = []
    for method, path in SPEC_ENDPOINTS:
        if path not in paths:
            missing.append(f"{method} {path}")
            continue
        if method.lower() not in paths[path]:
            missing.append(f"{method} {path}")

    assert not missing, f"Missing endpoints in OpenAPI schema:\n" + "\n".join(missing)


@pytest.mark.asyncio
async def test_openapi_schema_has_no_empty_paths(client: httpx.AsyncClient) -> None:
    response = await client.get("/openapi.json")
    schema = response.json()

    for path, methods in schema["paths"].items():
        assert len(methods) > 0, f"Path {path} has no methods"


@pytest.mark.asyncio
async def test_health_endpoint_contract(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "version" in body
    assert body["status"] == "ok"
