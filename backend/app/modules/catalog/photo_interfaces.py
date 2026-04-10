from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from typing import Protocol, cast

import httpx

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.ai_inference_log import AiInferenceLog


logger = logging.getLogger(__name__)


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
        api_key: str = "",
        client: PhotoParserHTTPClient | None = None,
    ) -> None:
        self._api_url: str = api_url.rstrip("/")
        self._model: str = model
        self._api_key: str = api_key
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

        start = time.perf_counter()
        status = "success"
        error_detail = None
        response_payload: object = {}
        result: list[dict[str, object]] = []

        headers: dict[str, str] = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        try:
            if self._client is not None:
                response = await self._client.post(self._api_url, json=payload)
            else:
                async with httpx.AsyncClient(timeout=45.0, headers=headers) as client:
                    response = await client.post(self._api_url, json=payload)

            status_code = getattr(response, "status_code", None)
            if isinstance(status_code, int) and status_code >= 400:
                resp_text = getattr(response, "text", "")
                logger.error("LLM API error %s: %s", status_code, resp_text[:500] if isinstance(resp_text, str) else "")
            raise_for_status = getattr(response, "raise_for_status", None)
            if callable(raise_for_status):
                _ = raise_for_status()
            json_loader = getattr(response, "json", None)
            response_payload = json_loader() if callable(json_loader) else {}
            content = self._extract_content(response_payload)
            draft_items = content.get("draft_items", [])
            if not isinstance(draft_items, list):
                draft_items = []
            result = []
            for item in cast(list[object], draft_items):
                if isinstance(item, dict):
                    result.append(cast(JSONDict, item))
        except Exception as exc:
            status = "error"
            error_detail = str(exc)[:500]
            result = []
            response_payload = {}
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            await self._log_inference(response_payload, result, duration_ms, status, error_detail)

        return result

    async def _log_inference(
        self,
        response_payload: object,
        items: list[dict[str, object]],
        duration_ms: float,
        status: str,
        error_detail: str | None,
    ) -> None:
        try:
            usage: dict[str, object] = {}
            if isinstance(response_payload, Mapping):
                raw_usage = cast(JSONDict, response_payload).get("usage", {})
                if isinstance(raw_usage, dict):
                    usage = cast(JSONDict, raw_usage)

            input_tokens = usage.get("prompt_tokens")
            output_tokens = usage.get("completion_tokens")
            input_tokens_int = int(input_tokens) if isinstance(input_tokens, int | float) else None
            output_tokens_int = int(output_tokens) if isinstance(output_tokens, int | float) else None

            cost_usd = None
            if input_tokens_int is not None and output_tokens_int is not None:
                cost_usd = (
                    input_tokens_int * settings.LLM_INPUT_COST_PER_1M / 1_000_000
                    + output_tokens_int * settings.LLM_OUTPUT_COST_PER_1M / 1_000_000
                )

            confidences: list[float] = []
            for i in items:
                conf = i.get("confidence")
                if isinstance(conf, int | float):
                    confidences.append(float(conf))
            avg_conf = sum(confidences) / len(confidences) if confidences else None

            async with AsyncSessionLocal() as session:
                session.add(
                    AiInferenceLog(
                        provider="litellm",
                        operation="photo_parse",
                        model=self._model,
                        duration_ms=duration_ms,
                        status=status,
                        input_tokens=input_tokens_int,
                        output_tokens=output_tokens_int,
                        cost_usd=cost_usd,
                        items_returned=len(items),
                        avg_confidence=avg_conf,
                        error_detail=error_detail,
                    )
                )
                await session.commit()
        except Exception as exc:
            logger.warning("Photo parser inference logging failed: %s", exc)

    @staticmethod
    def _extract_content(payload: object) -> dict[str, object]:
        import json as _json

        if not isinstance(payload, Mapping):
            return {}
        payload_dict = cast(JSONDict, payload)
        choices = payload_dict.get("choices", [])
        if not isinstance(choices, list) or not choices:
            return {}
        normalized_choices = cast(list[object], choices)
        first_choice = normalized_choices[0]
        if not isinstance(first_choice, Mapping):
            return {}
        first_choice_dict = cast(JSONDict, first_choice)
        message = first_choice_dict.get("message", {})
        if not isinstance(message, Mapping):
            return {}
        message_dict = cast(JSONDict, message)

        parsed = message_dict.get("parsed")
        if isinstance(parsed, dict) and parsed:
            return cast(dict[str, object], parsed)

        content = message_dict.get("content")
        if isinstance(content, str):
            try:
                parsed_content = cast(object, _json.loads(content))
                if isinstance(parsed_content, dict):
                    return cast(dict[str, object], parsed_content)
            except (ValueError, TypeError):
                pass
        if isinstance(content, list):
            for item in cast(list[object], content):
                if not isinstance(item, Mapping):
                    continue
                item_dict = cast(JSONDict, item)
                parsed_item = item_dict.get("parsed")
                if isinstance(parsed_item, dict):
                    return cast(dict[str, object], parsed_item)
        return {}
