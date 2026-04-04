from __future__ import annotations

import argparse
import asyncio
from argparse import Namespace
from typing import cast

import httpx


def _assert_keys(payload: dict[str, object], keys: set[str], *, name: str) -> None:
    missing = keys - payload.keys()
    if missing:
        raise AssertionError(f"{name} missing keys: {sorted(missing)}")


async def verify(base_url: str, token: str) -> None:
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "contract-check"}
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        item_response = await client.post(
            "/v1/items",
            headers=headers,
            json={
                "display_name": "Contract Milk",
                "quantity": 1.0,
                "unit": "liter",
                "storage_location": "fridge",
            },
        )
        _ = item_response.raise_for_status()
        item_payload = cast(dict[str, object], item_response.json())
        _assert_keys(
            item_payload,
            {"itemId", "displayName", "quantity", "unit", "storageLocation", "estimatedExpiryDate", "confidence"},
            name="POST /v1/items",
        )

        barcode_response = await client.post(
            "/v1/scan/barcode",
            headers=headers,
            json={"barcode": "8710847909610", "quantity": 1.0, "storage_location": "fridge"},
        )
        _ = barcode_response.raise_for_status()
        _assert_keys(
            cast(dict[str, object], barcode_response.json()),
            {"barcode", "display_name", "canonical_name", "quantity", "storage_location", "source"},
            name="POST /v1/scan/barcode",
        )

        photo_response = await client.post(
            "/v1/scan/photo",
            headers=headers,
            json={"image_url": "https://example.test/contract.png"},
        )
        _ = photo_response.raise_for_status()
        photo_payload = cast(dict[str, object], photo_response.json())
        _assert_keys(photo_payload, {"draft_items"}, name="POST /v1/scan/photo")

        recommendations_response = await client.post(
            "/v1/recommendations",
            headers=headers,
            json={"servings": 2},
        )
        _ = recommendations_response.raise_for_status()
        recommendations_payload = cast(dict[str, object], recommendations_response.json())
        _assert_keys(recommendations_payload, {"recipes"}, name="POST /v1/recommendations")

        plans_response = await client.post(
            "/v1/plans",
            headers=headers,
            json={"days": 3, "servings": 2},
        )
        _ = plans_response.raise_for_status()
        plans_payload = cast(dict[str, object], plans_response.json())
        _assert_keys(plans_payload, {"planId", "days", "shoppingList"}, name="POST /v1/plans")

        shopping_response = await client.get("/v1/shopping-list", headers=headers)
        _ = shopping_response.raise_for_status()
        _assert_keys(cast(dict[str, object], shopping_response.json()), {"items"}, name="GET /v1/shopping-list")

        households_response = await client.get("/v1/households", headers=headers)
        _ = households_response.raise_for_status()
        households_payload = cast(object, households_response.json())
        if not isinstance(households_payload, list):
            raise AssertionError("GET /v1/households must return a list")

        notifications_response = await client.patch(
            "/v1/notifications",
            headers=headers,
            json={"expiry_reminder_enabled": True},
        )
        _ = notifications_response.raise_for_status()
        _assert_keys(
            cast(dict[str, object], notifications_response.json()),
            {"user_id", "expiry_reminder_enabled", "reminder_days_before"},
            name="PATCH /v1/notifications",
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    _ = parser.add_argument("--base-url", default="http://localhost:8000")
    _ = parser.add_argument("--token", default="test-token")
    args: Namespace = parser.parse_args()
    base_url = cast(str, args.base_url)
    token = cast(str, args.token)
    _ = asyncio.run(verify(base_url, token))


if __name__ == "__main__":
    main()
