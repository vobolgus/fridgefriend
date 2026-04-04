from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.units import normalize_unit
from app.models.canonical_ingredient import CanonicalIngredient, ProductBarcode

from .interfaces import BarcodeAPIInterface
from .mock_barcode_api import MockBarcodeAPI
from .normalizer import normalize_ingredient_name
from .schemas import BarcodeResult


class CatalogService:
    def __init__(
        self,
        barcode_api: BarcodeAPIInterface | None = None,
        db_session: AsyncSession | None = None,
    ) -> None:
        self.barcode_api: BarcodeAPIInterface = barcode_api or MockBarcodeAPI()
        self._db_session: AsyncSession | None = db_session

    async def lookup_barcode(self, barcode: str) -> BarcodeResult | None:
        return await self.barcode_api.lookup(barcode)

    def normalize(self, name: str) -> str:
        return normalize_ingredient_name(name)

    @staticmethod
    def normalize_unit(unit: str) -> str:
        return normalize_unit(unit)

    @staticmethod
    def normalize_quantity(quantity: float) -> float:
        return max(0.0, round(quantity, 3))

    async def resolve_canonical(self, name: str) -> CanonicalIngredient | None:
        if self._db_session is None:
            return None

        normalized_name = self.normalize(name)
        statement = select(CanonicalIngredient).where(CanonicalIngredient.name == normalized_name)
        existing = (await self._db_session.execute(statement)).scalar_one_or_none()
        if existing is not None:
            return existing

        ingredient = CanonicalIngredient(name=normalized_name, category="uncategorized", aliases=[])
        self._db_session.add(ingredient)
        await self._db_session.flush()
        return ingredient

    async def lookup_barcode_with_canonical(
        self,
        barcode: str,
    ) -> tuple[BarcodeResult, CanonicalIngredient | None] | None:
        result = await self.lookup_barcode(barcode)
        if result is None:
            return None

        canonical = await self.resolve_canonical(result.canonical_name)
        if canonical is not None:
            await self._upsert_product_barcode(result, canonical)

        return result, canonical

    async def _upsert_product_barcode(
        self,
        result: BarcodeResult,
        canonical: CanonicalIngredient,
    ) -> None:
        if self._db_session is None:
            return

        statement = select(ProductBarcode).where(ProductBarcode.barcode == result.barcode)
        existing = (await self._db_session.execute(statement)).scalar_one_or_none()
        if existing is None:
            self._db_session.add(
                ProductBarcode(
                    barcode=result.barcode,
                    canonical_ingredient_id=canonical.id,
                    display_name=result.display_name,
                    brand=result.brand,
                )
            )
            await self._db_session.flush()
            return

        existing.canonical_ingredient_id = canonical.id
        existing.display_name = result.display_name
        existing.brand = result.brand
        await self._db_session.flush()
