import re


QUANTITY_SUFFIX_PATTERN = re.compile(
    r"(?:\s+\d+(?:\.\d+)?\s*(?:g|kg|ml|l|pk|pack|packs|oz|lb))+$",
)
PARENS_PATTERN = re.compile(r"\s*\([^)]*\)")
WHITESPACE_PATTERN = re.compile(r"\s+")

BRAND_PREFIXES = (
    "heinz",
    "tesco",
    "general mills",
    "coca-cola",
    "coca cola",
    "milka",
    "warburtons",
    "cheerios",
)

EXACT_VARIANTS = {
    "tomato": "tomatoes",
    "tomatoes": "tomatoes",
    "tomato ketchup": "ketchup",
    "whole milk": "whole milk",
}


def normalize_ingredient_name(raw_name: str) -> str:
    normalized = raw_name.lower().strip()
    normalized = PARENS_PATTERN.sub("", normalized)
    normalized = normalized.replace("-", " ")
    normalized = QUANTITY_SUFFIX_PATTERN.sub("", normalized).strip()

    for prefix in BRAND_PREFIXES:
        if normalized.startswith(f"{prefix} "):
            normalized = normalized.removeprefix(f"{prefix} ").strip()
            break

    normalized = WHITESPACE_PATTERN.sub(" ", normalized).strip()

    if normalized in EXACT_VARIANTS:
        return EXACT_VARIANTS[normalized]

    if "ketchup" in normalized:
        return "ketchup"

    return EXACT_VARIANTS.get(normalized, normalized)
