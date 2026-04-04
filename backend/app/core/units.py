from __future__ import annotations

UNIT_ALIASES: dict[str, str] = {
    "g": "g",
    "gram": "g",
    "grams": "g",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "ml": "ml",
    "milliliter": "ml",
    "milliliters": "ml",
    "millilitre": "ml",
    "millilitres": "ml",
    "l": "l",
    "liter": "l",
    "liters": "l",
    "litre": "l",
    "litres": "l",
    "oz": "oz",
    "ounce": "oz",
    "ounces": "oz",
    "lb": "lb",
    "lbs": "lb",
    "pound": "lb",
    "pounds": "lb",
    "cup": "cup",
    "cups": "cup",
    "tbsp": "tbsp",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "tsp": "tsp",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "gallon": "gallon",
    "gallons": "gallon",
    "pint": "pint",
    "pints": "pint",
    "piece": "piece",
    "pieces": "piece",
    "unit": "unit",
    "units": "unit",
    "pack": "pack",
    "packs": "pack",
    "pk": "pack",
    "bunch": "bunch",
    "can": "can",
    "cans": "can",
    "bottle": "bottle",
    "bottles": "bottle",
    "slice": "slice",
    "slices": "slice",
}

CONVERSION_TO_BASE: dict[str, tuple[str, float]] = {
    "g": ("g", 1.0),
    "kg": ("g", 1000.0),
    "oz": ("g", 28.3495),
    "lb": ("g", 453.592),
    "ml": ("ml", 1.0),
    "l": ("ml", 1000.0),
    "gallon": ("ml", 3785.41),
    "pint": ("ml", 473.176),
    "cup": ("ml", 236.588),
    "tbsp": ("ml", 14.787),
    "tsp": ("ml", 4.929),
}


def normalize_unit(raw_unit: str) -> str:
    return UNIT_ALIASES.get(raw_unit.strip().lower(), raw_unit.strip().lower())


def convert_to_base(quantity: float, unit: str) -> tuple[float, str]:
    normalized = normalize_unit(unit)
    if normalized in CONVERSION_TO_BASE:
        base_unit, factor = CONVERSION_TO_BASE[normalized]
        return quantity * factor, base_unit
    return quantity, normalized


def are_units_compatible(unit_a: str, unit_b: str) -> bool:
    norm_a = normalize_unit(unit_a)
    norm_b = normalize_unit(unit_b)
    if norm_a == norm_b:
        return True
    base_a = CONVERSION_TO_BASE.get(norm_a)
    base_b = CONVERSION_TO_BASE.get(norm_b)
    if base_a is None or base_b is None:
        return False
    return base_a[0] == base_b[0]


def convert_quantity(quantity: float, from_unit: str, to_unit: str) -> float | None:
    norm_from = normalize_unit(from_unit)
    norm_to = normalize_unit(to_unit)
    if norm_from == norm_to:
        return quantity
    base_from = CONVERSION_TO_BASE.get(norm_from)
    base_to = CONVERSION_TO_BASE.get(norm_to)
    if base_from is None or base_to is None:
        return None
    if base_from[0] != base_to[0]:
        return None
    base_quantity = quantity * base_from[1]
    return base_quantity / base_to[1]
