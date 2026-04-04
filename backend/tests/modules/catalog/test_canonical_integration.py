from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canonical_ingredient import CanonicalIngredient, ProductBarcode
from app.models.household import Household
from app.models.user import User
from app.modules.catalog.service import CatalogService
from app.modules.inventory.repository import InventoryRepository
from app.modules.inventory.schemas import ItemCreate
from app.modules.inventory.service import InventoryService


async def _create_user_and_household(db_session: AsyncSession) -> tuple[User, Household]:
    user = User(email="canonical-integration@example.com")
    household = Household(name="Canonical Household", invite_code="canonical-household")
    db_session.add_all([user, household])
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(household)
    return user, household


@pytest.mark.asyncio
async def test_barcode_resolves_to_canonical_ingredient(db_session: AsyncSession) -> None:
    service = CatalogService(db_session=db_session)

    resolved = await service.lookup_barcode_with_canonical("8710847909610")

    assert resolved is not None
    _, canonical = resolved
    assert canonical is not None
    assert canonical.name == "milk"


@pytest.mark.asyncio
async def test_normalization_creates_canonical_if_not_exists(db_session: AsyncSession) -> None:
    service = CatalogService(db_session=db_session)

    canonical = await service.resolve_canonical("Tesco Ketchup 500g")

    assert canonical is not None
    assert canonical.name == "ketchup"
    saved = (await db_session.execute(select(CanonicalIngredient).where(CanonicalIngredient.id == canonical.id))).scalar_one()
    assert saved.name == "ketchup"


@pytest.mark.asyncio
async def test_inventory_item_links_to_canonical(db_session: AsyncSession) -> None:
    user, household = await _create_user_and_household(db_session)
    catalog_service = CatalogService(db_session=db_session)
    inventory_service = InventoryService(
        InventoryRepository(db_session),
        catalog_service=catalog_service,
    )

    item = await inventory_service.create_item(
        user,
        household.id,
        ItemCreate(
            display_name="Whole Milk 1L",
            quantity=1.0,
            unit="liter",
            storage_location="fridge",
        ),
    )

    assert item.canonical_ingredient_id is not None
    canonical = (await db_session.execute(select(CanonicalIngredient).where(CanonicalIngredient.id == item.canonical_ingredient_id))).scalar_one()
    assert canonical.name == "whole milk"


@pytest.mark.asyncio
async def test_barcode_lookup_persists_product_barcode_link(db_session: AsyncSession) -> None:
    service = CatalogService(db_session=db_session)

    resolved = await service.lookup_barcode_with_canonical("5000112637939")

    assert resolved is not None
    barcode = (await db_session.execute(select(ProductBarcode).where(ProductBarcode.barcode == "5000112637939"))).scalar_one()
    assert barcode.canonical_ingredient.name == "ketchup"
