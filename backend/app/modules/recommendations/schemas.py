from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class RecommendationRequest(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(str_strip_whitespace=True)

    servings: int = Field(default=2, ge=1)
    dietary_tags: list[str] = Field(default_factory=list)
    max_prep_minutes: int | None = Field(default=None, ge=1)
    excluded_ingredients: list[str] = Field(default_factory=list)


class RecipeIngredient(BaseModel):
    canonical_name: str
    quantity: float
    unit: str


class FixtureRecipe(BaseModel):
    id: str
    title: str
    prep_minutes: int = Field(ge=0)
    dietary_tags: list[str] = Field(default_factory=list)
    ingredients: list[RecipeIngredient] = Field(default_factory=list)


class RecipeRecommendation(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    title: str
    use_soon_score: float = Field(alias="useSoonScore")
    coverage_pct: float = Field(alias="coveragePct")
    missing_items: list[str] = Field(alias="missingItems")
    substitutions: list[str]
    prep_minutes: int = Field(alias="prepMinutes")
    score: float


class RecommendationResponse(BaseModel):
    recipes: list[RecipeRecommendation]
