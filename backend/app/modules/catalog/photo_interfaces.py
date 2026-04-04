from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, cast

import httpx


class PhotoParserInterface(Protocol):
    async def parse_image(self, image_url: str) -> list[dict[str, object]]: ...


class PhotoParserHTTPClient(Protocol):
    async def post(self, url: str, json: Mapping[str, object]) -> httpx.Response | object: ...


type JSONDict = dict[str, object]


class MockPhotoParser:
    async def parse_image(self, image_url: str) -> list[dict[str, object]]:
        _ = image_url
        return [
            {
                "display_name": "Milk",
                "quantity": 1.0,
                "unit": "gallon",
                "confidence": 0.85,
            }
        ]


class LLMPhotoParser:
    def __init__(
        self,
        api_url: str,
        model: str,
        *,
        client: PhotoParserHTTPClient | None = None,
    ) -> None:
        self._api_url: str = api_url.rstrip("/")
        self._model: str = model
        self._client: PhotoParserHTTPClient | None = client

    async def parse_image(self, image_url: str) -> list[dict[str, object]]:
        payload: dict[str, object] = {
            "model": self._model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Extract fridge items and return JSON array fields: "
                                "display_name, quantity, unit, confidence, canonical_name."
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "fridgefriend_photo_scan",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "draft_items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "display_name": {"type": "string"},
                                        "quantity": {"type": "number"},
                                        "unit": {"type": "string"},
                                        "confidence": {"type": "number"},
                                        "canonical_name": {"type": ["string", "null"]},
                                    },
                                    "required": ["display_name", "quantity", "unit", "confidence"],
                                    "additionalProperties": True,
                                },
                            }
                        },
                        "required": ["draft_items"],
                        "additionalProperties": True,
                    },
                },
            },
        }

        if self._client is not None:
            response = await self._client.post(self._api_url, json=payload)
        else:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(self._api_url, json=payload)

        raise_for_status = getattr(response, "raise_for_status", None)
        if callable(raise_for_status):
            _ = raise_for_status()
        json_loader = getattr(response, "json", None)
        response_payload: object = json_loader() if callable(json_loader) else {}
        content = self._extract_content(response_payload)
        draft_items = cast(object, content.get("draft_items", []))
        if not isinstance(draft_items, list):
            return []
        return [cast(dict[str, object], item) for item in draft_items if isinstance(item, dict)]

    @staticmethod
    def _extract_content(payload: object) -> dict[str, object]:
        if not isinstance(payload, Mapping):
            return {}
        payload_dict = cast(JSONDict, payload)
        choices = payload_dict.get("choices", [])
        if not isinstance(choices, list) or not choices:
            return {}
        first_choice = choices[0]
        if not isinstance(first_choice, Mapping):
            return {}
        first_choice_dict = cast(JSONDict, first_choice)
        message = first_choice_dict.get("message", {})
        if not isinstance(message, Mapping):
            return {}
        message_dict = cast(JSONDict, message)
        parsed = message_dict.get("parsed", {})
        if isinstance(parsed, dict):
            return cast(dict[str, object], parsed)
        content = message_dict.get("content", [])
        if not isinstance(content, list):
            return {}
        for item in content:
            if not isinstance(item, Mapping):
                continue
            item_dict = cast(JSONDict, item)
            parsed_item = item_dict.get("parsed")
            if isinstance(parsed_item, dict):
                return cast(dict[str, object], parsed_item)
        return {}
