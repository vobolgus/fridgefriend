from __future__ import annotations

from datetime import date
from typing import ClassVar

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class RecipeIngredient(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    ingredient_name: str = Field(validation_alias=AliasChoices("ingredient_name", "canonical_name", "name"))
    quantity: float = Field(ge=0)
    unit: str


class PlanRequest(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(str_strip_whitespace=True)

    days: int = Field(default=7, ge=3, le=7)
    servings: int = Field(default=2, ge=1)
    dietary_tags: list[str] = Field(default_factory=list)
    max_prep_minutes: int | None = Field(default=None, ge=1)


class PlanDay(BaseModel):
    date: date
    recipe_id: str
    recipe_title: str
    servings: int
    reserved_items: list[str] = Field(default_factory=list)
    recipe_ingredients: list[RecipeIngredient] = Field(default_factory=list, exclude=True)


class ShoppingItem(BaseModel):
    ingredient_name: str
    quantity: float
    unit: str
    reason: str


class PlanResult(BaseModel):
    plan_id: str
    days: list[PlanDay]
    shopping_list: list[ShoppingItem] = Field(default_factory=list)


class ShoppingListResponse(BaseModel):
    items: list[ShoppingItem] = Field(default_factory=list)
