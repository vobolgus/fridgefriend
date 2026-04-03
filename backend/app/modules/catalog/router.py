from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.core.idempotency import get_cached, store_cached

from .schemas import BarcodeScanRequest, BarcodeScanResponse
from .service import CatalogService

router = APIRouter(prefix="/v1/scan", tags=["catalog"])


def get_catalog_service() -> CatalogService:
    return CatalogService()


@router.post("/barcode", response_model=BarcodeScanResponse)
async def scan_barcode(
    payload: BarcodeScanRequest,
    service: Annotated[CatalogService, Depends(get_catalog_service)],
    request: Request,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> BarcodeScanResponse:
    if idempotency_key:
        cached = get_cached("anon", request.url.path, idempotency_key)
        if cached:
            return BarcodeScanResponse(**cached)

    result = service.lookup_barcode(payload.barcode)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Barcode not found in catalog",
        )

    response = BarcodeScanResponse(
        barcode=result.barcode,
        display_name=result.display_name,
        canonical_name=result.canonical_name,
        brand=result.brand,
        quantity=payload.quantity,
        storage_location=payload.storage_location,
        source="barcode",
    )

    if idempotency_key:
        store_cached("anon", request.url.path, idempotency_key, response.model_dump(mode="json"))

    return response
