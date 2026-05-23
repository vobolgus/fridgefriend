from __future__ import annotations

from pathlib import Path

import httpx
import pytest


SPEC_PATH = Path(__file__).resolve().parents[2] / "SPEC.md"
CONTRACT_START = "<!-- api-contract:start -->"
CONTRACT_END = "<!-- api-contract:end -->"


def _load_spec_endpoints() -> tuple[tuple[str, str], ...]:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    start = spec.index(CONTRACT_START) + len(CONTRACT_START)
    end = spec.index(CONTRACT_END)
    endpoints: list[tuple[str, str]] = []

    for line in spec[start:end].splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0] in {"Method", "---"}:
            continue
        endpoints.append((cells[0].upper(), cells[1]))

    if not endpoints:
        raise AssertionError(f"No API endpoints found in {SPEC_PATH}")

    return tuple(endpoints)


SPEC_ENDPOINTS = _load_spec_endpoints()


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
