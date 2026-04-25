from __future__ import annotations

from datetime import datetime
from datetime import date
from typing import ClassVar
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


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
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True, populate_by_name=True)

    date: date
    recipe_id: str = Field(alias="recipeId")
    recipe_title: str = Field(alias="recipeTitle")
    prep_minutes: int | None = Field(default=None, alias="prepMinutes")
    image_url: str | None = Field(default=None, alias="imageUrl")
    servings: int
    reserved_items: list[str] = Field(default_factory=list, alias="reservedItems")
    recipe_ingredients: list[RecipeIngredient] = Field(default_factory=list, exclude=True, alias="recipeIngredients")


class ShoppingItem(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True)

    ingredient_name: str = Field(alias="ingredientName")
    name: str | None = None
    quantity: float
    unit: str
    reason: str

    @model_validator(mode="after")
    def _populate_name(self) -> ShoppingItem:
        if self.name is None:
            self.name = self.ingredient_name
        return self


class PlanResult(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True, populate_by_name=True)

    plan_id: str = Field(alias="planId")
    days: list[PlanDay]
    shopping_list: list[ShoppingItem] = Field(default_factory=list, alias="shoppingList")


class PlanResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True)

    plan: PlanResult


class ShoppingListResponse(BaseModel):
    items: list[ShoppingItem] = Field(default_factory=list)


class ShoppingListItemCreate(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(str_strip_whitespace=True)

    name: str
    quantity: float | None = None
    unit: str | None = None
    recipe_id: UUID | None = None


class ShoppingListItemBatchCreate(BaseModel):
    items: list[ShoppingListItemCreate]


class ShoppingListItemRead(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True, from_attributes=True)

    id: UUID
    name: str
    quantity: float | None = None
    unit: str | None = None
    recipe_id: UUID | None = Field(default=None, alias="recipeId")
    created_at: datetime = Field(alias="createdAt")


class ShoppingListItemBatchRead(BaseModel):
    items: list[ShoppingListItemRead]
