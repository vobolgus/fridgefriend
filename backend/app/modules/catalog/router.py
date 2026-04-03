from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from .schemas import BarcodeScanRequest, BarcodeScanResponse
from .service import CatalogService

router = APIRouter(prefix="/v1/scan", tags=["catalog"])


def get_catalog_service() -> CatalogService:
    return CatalogService()


@router.post("/barcode", response_model=BarcodeScanResponse)
async def scan_barcode(
    payload: BarcodeScanRequest,
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> BarcodeScanResponse:
    result = service.lookup_barcode(payload.barcode)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Barcode not found in catalog",
        )

    return BarcodeScanResponse(
        barcode=result.barcode,
        display_name=result.display_name,
        canonical_name=result.canonical_name,
        brand=result.brand,
        quantity=payload.quantity,
        storage_location=payload.storage_location,
        source="barcode",
    )
