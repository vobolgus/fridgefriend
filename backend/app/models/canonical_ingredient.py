# pyright: reportUnannotatedClassAttribute=false

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CanonicalIngredient(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "canonical_ingredients"

    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(100))
    aliases: Mapped[list[str]] = mapped_column(JSON, default=list)

    shelf_life_rules: Mapped[list["ShelfLifeRule"]] = relationship(
        back_populates="canonical_ingredient"
    )
    barcodes: Mapped[list["ProductBarcode"]] = relationship(
        back_populates="canonical_ingredient"
    )


class ProductBarcode(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "product_barcodes"

    barcode: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    canonical_ingredient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("canonical_ingredients.id"),
        index=True,
    )
    display_name: Mapped[str] = mapped_column(String(255))
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)

    canonical_ingredient: Mapped[CanonicalIngredient] = relationship(
        back_populates="barcodes"
    )


class ShelfLifeRule(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "shelf_life_rules"

    canonical_ingredient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("canonical_ingredients.id"),
        index=True,
    )
    storage_type: Mapped[str] = mapped_column(String(50))
    shelf_life_days: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)

    canonical_ingredient: Mapped[CanonicalIngredient] = relationship(
        back_populates="shelf_life_rules"
    )
