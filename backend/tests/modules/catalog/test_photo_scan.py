from __future__ import annotations

from collections.abc import AsyncIterator
from typing import cast

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI

from app.core.database import get_db
from app.models import Base
from app.modules.inventory.dependencies import get_current_user
from app.modules.catalog.photo_interfaces import LLMPhotoParser, PhotoParserInterface
from app.modules.catalog.router import get_photo_parser
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


def _headers(key: str) -> dict[str, str]:
    return {"Authorization": "Bearer test-token", "Idempotency-Key": key}


class _StaticPhotoParser:
    def __init__(self, items: list[dict[str, object]]) -> None:
        self._items: list[dict[str, object]] = items

    async def parse_image(self, image_url: str) -> list[dict[str, object]]:
        assert image_url.startswith("https://")
        return self._items


class _FailingPhotoParser:
    async def parse_image(self, image_url: str) -> list[dict[str, object]]:
        _ = image_url
        raise RuntimeError("llm unavailable")


class _LLMResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return {
            "choices": [
                {
                    "message": {
                        "parsed": {
                            "draft_items": [
                                {
                                    "display_name": "Milk",
                                    "quantity": 1.0,
                                    "unit": "gallon",
                                    "confidence": 0.87,
                                    "canonical_name": "milk",
                                }
                            ]
                        }
                    }
                }
            ]
        }


class _LLMClient:
    async def post(self, url: str, json: dict[str, object] | object) -> _LLMResponse:
        assert url == "https://litellm.example"
        payload = cast(dict[str, object], json)
        assert payload["model"] == "gpt-4.1-mini"
        return _LLMResponse()


@pytest_asyncio.fixture
async def photo_client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = AsyncSession(bind=engine, expire_on_commit=False)
    user = User(email="photo-scan@example.com")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield async_session

    async def override_get_current_user() -> User:
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as async_client:
        yield async_client

    await async_session.close()
    await engine.dispose()
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_photo_scan_requires_auth(client: httpx.AsyncClient) -> None:
    response = await client.post("/v1/scan/photo", json={"image_url": "https://example.com/fridge.jpg"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_photo_scan_returns_draft_items(photo_client: httpx.AsyncClient, app: FastAPI) -> None:
    app.dependency_overrides[get_photo_parser] = lambda: _StaticPhotoParser(
        [{"display_name": "Milk", "quantity": 1.0, "unit": "gallon", "confidence": 0.85}]
    )

    response = await photo_client.post(
        "/v1/scan/photo",
        headers=_headers("photo-scan-draft-1"),
        json={"image_url": "https://example.com/fridge.jpg"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "draft_items": [
            {
                "display_name": "Milk",
                "quantity": 1.0,
                "unit": "gallon",
                "confidence": 0.85,
                "canonical_name": "milk",
            }
        ],
        "source": "photo",
    }


@pytest.mark.asyncio
async def test_photo_scan_low_confidence_returns_editable_draft(
    photo_client: httpx.AsyncClient,
    app: FastAPI,
) -> None:
    app.dependency_overrides[get_photo_parser] = lambda: _StaticPhotoParser(
        [{"display_name": "Mystery Dairy", "quantity": 1.0, "unit": "unit", "confidence": 0.12}]
    )

    response = await photo_client.post(
        "/v1/scan/photo",
        headers=_headers("photo-scan-low-confidence-1"),
        json={"image_url": "https://example.com/low.jpg"},
    )

    assert response.status_code == 200
    payload = cast(dict[str, object], response.json())
    draft_items = cast(list[dict[str, object]], payload["draft_items"])
    assert draft_items[0]["display_name"] == "Mystery Dairy"
    assert draft_items[0]["confidence"] == 0.12


@pytest.mark.asyncio
async def test_photo_scan_failure_returns_empty_editable_draft(
    photo_client: httpx.AsyncClient,
    app: FastAPI,
) -> None:
    app.dependency_overrides[get_photo_parser] = lambda: _FailingPhotoParser()

    response = await photo_client.post(
        "/v1/scan/photo",
        headers=_headers("photo-scan-failure-1"),
        json={"image_url": "https://example.com/fail.jpg"},
    )

    assert response.status_code == 200
    assert response.json() == {"draft_items": [], "source": "photo"}


@pytest.mark.asyncio
async def test_photo_scan_with_mock_llm() -> None:
    parser: PhotoParserInterface = LLMPhotoParser(
        "https://litellm.example",
        "gpt-4.1-mini",
        client=_LLMClient(),
    )

    items = await parser.parse_image("https://example.com/mock-llm.jpg")

    assert items == [
        {
            "display_name": "Milk",
            "quantity": 1.0,
            "unit": "gallon",
            "confidence": 0.87,
            "canonical_name": "milk",
        }
    ]
