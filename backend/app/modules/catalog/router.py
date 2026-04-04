from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.idempotency import get_cached, store_cached
from app.models.user import User
from app.modules.inventory.dependencies import get_current_user

from .photo_interfaces import LLMPhotoParser, MockPhotoParser, PhotoParserInterface
from .schemas import (
    BarcodeScanRequest,
    BarcodeScanResponse,
    DraftItem,
    PhotoScanRequest,
    PhotoScanResponse,
)
from .service import CatalogService

router = APIRouter(prefix="/v1/scan", tags=["catalog"])


async def get_catalog_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CatalogService:
    return CatalogService(db_session=db)


def get_photo_parser() -> PhotoParserInterface:
    if settings.STORAGE_BACKEND == "llm":
        return LLMPhotoParser(settings.LLM_API_URL, settings.LLM_MODEL)
    return MockPhotoParser()


@router.post("/barcode", response_model=BarcodeScanResponse)
async def scan_barcode(
    payload: BarcodeScanRequest,
    service: Annotated[CatalogService, Depends(get_catalog_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> BarcodeScanResponse:
    if idempotency_key:
        cached = get_cached(str(current_user.id), request.url.path, idempotency_key)
        if cached:
            return BarcodeScanResponse.model_validate(cached)

    resolved = await service.lookup_barcode_with_canonical(payload.barcode)
    if resolved is None:
        response = BarcodeScanResponse(
            barcode=payload.barcode,
            display_name="",
            canonical_name="",
            canonical_ingredient_id=None,
            brand="",
            quantity=payload.quantity,
            storage_location=payload.storage_location,
            source="barcode",
        )
    else:
        result, canonical = resolved

        response = BarcodeScanResponse(
            barcode=result.barcode,
            display_name=result.display_name,
            canonical_name=result.canonical_name,
            canonical_ingredient_id=str(canonical.id) if canonical is not None else None,
            brand=result.brand,
            quantity=payload.quantity,
            storage_location=payload.storage_location,
            source="barcode",
        )

    if idempotency_key:
        store_cached(str(current_user.id), request.url.path, idempotency_key, response.model_dump(mode="json"))

    return response


@router.post("/photo", response_model=PhotoScanResponse)
async def scan_photo(
    payload: PhotoScanRequest,
    parser: Annotated[PhotoParserInterface, Depends(get_photo_parser)],
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> PhotoScanResponse:
    if idempotency_key:
        cached = get_cached(str(current_user.id), request.url.path, idempotency_key)
        if cached:
            return PhotoScanResponse.model_validate(cached)

    try:
        raw_items = await parser.parse_image(payload.image_url)
    except Exception:
        raw_items = []

    draft_items: list[DraftItem] = []
    for raw_item in raw_items:
        display_name = str(raw_item.get("display_name", "")).strip()
        if not display_name:
            continue
        quantity = _to_float(raw_item.get("quantity"), default=0.0)
        unit = str(raw_item.get("unit", "unit")).strip() or "unit"
        confidence = min(max(_to_float(raw_item.get("confidence"), default=0.0), 0.0), 1.0)
        canonical_name = raw_item.get("canonical_name")
        normalized_canonical_name = (
            str(canonical_name).strip().lower() if canonical_name is not None else service_normalize(display_name)
        )

        draft_items.append(
            DraftItem(
                display_name=display_name,
                quantity=max(quantity, 0.0),
                unit=unit,
                confidence=confidence,
                canonical_name=normalized_canonical_name or None,
            )
        )

    response = PhotoScanResponse(draft_items=draft_items)
    if idempotency_key:
        store_cached(str(current_user.id), request.url.path, idempotency_key, response.model_dump(mode="json"))
    return response


def service_normalize(display_name: str) -> str:
    return CatalogService().normalize(display_name)


def _to_float(value: object, *, default: float) -> float:
    if isinstance(value, bool):
        return float(default)
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default
