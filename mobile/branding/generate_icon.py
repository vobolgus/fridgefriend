"""Generate the FridgeFriend app icon.

Produces three PNGs in this directory:
- ``icon_source.png``        — 1024×1024 source for ``flutter_launcher_icons``
                                (full bleed, brand-green gradient + glyph).
- ``icon_foreground.png``    — 1024×1024 transparent PNG with the glyph only,
                                centered inside a 432×432 safe zone (the
                                Android adaptive-icon spec). Used as the
                                foreground layer.
- ``icon_background.png``    — 1024×1024 solid brand-green background for the
                                Android adaptive icon.

Usage::

    cd mobile && python branding/generate_icon.py

Idempotent: re-running overwrites the three outputs deterministically.

The glyph is the Material Symbols Rounded ``kitchen`` codepoint (U+EB47),
rendered from the open-source font fetched at build time. The font is cached
locally to avoid repeat network calls.
"""

from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# === Brand tokens (must match mobile/lib/core/design/colors.dart) ===
BRAND_PRIMARY = (0x00, 0xC8, 0x53)      # #00C853  AppColors.primary
BRAND_PRIMARY_DARK = (0x00, 0x96, 0x24)  # #009624 AppColors.primaryDark
WHITE = (255, 255, 255)

CANVAS = 1024
# Android adaptive-icon safe zone is the inner 66% of the canvas
# (foreground icon must fit in a 432×432 box centered on a 1024 source).
SAFE_ZONE = int(CANVAS * (432 / 1024))  # 432

# Material Symbols Rounded — kitchen glyph (U+EB47).
GLYPH_CODEPOINT = "\uEB47"
FONT_URL = (
    "https://github.com/google/material-design-icons/raw/master/variablefont/"
    "MaterialSymbolsRounded%5BFILL%2CGRAD%2Copsz%2Cwght%5D.ttf"
)
FONT_CACHE = Path(__file__).parent / ".material_symbols_rounded.ttf"

OUT_DIR = Path(__file__).parent
SOURCE = OUT_DIR / "icon_source.png"
FOREGROUND = OUT_DIR / "icon_foreground.png"
BACKGROUND = OUT_DIR / "icon_background.png"


def _ensure_font() -> Path:
    """Download Material Symbols Rounded once and cache it next to this script.

    Uses ``curl`` (which has a working CA bundle on macOS) instead of urllib to
    sidestep ``ssl.SSLCertVerificationError`` on standalone Python installs that
    ship without certifi. Falls back to ``requests`` if curl is unavailable.
    """
    if FONT_CACHE.exists() and FONT_CACHE.stat().st_size > 100_000:
        return FONT_CACHE

    print(f"Fetching Material Symbols font → {FONT_CACHE}")
    if shutil.which("curl"):
        result = subprocess.run(
            ["curl", "-fsSL", "--max-time", "60", "-o", str(FONT_CACHE), FONT_URL],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"curl failed: {result.stderr.strip()}")
    else:
        import requests  # type: ignore[import-untyped]
        r = requests.get(FONT_URL, timeout=60)
        r.raise_for_status()
        FONT_CACHE.write_bytes(r.content)

    size = FONT_CACHE.stat().st_size
    if size < 100_000:
        FONT_CACHE.unlink(missing_ok=True)
        raise RuntimeError(f"Font download too small ({size} bytes)")
    return FONT_CACHE


def _radial_gradient(size: int, inner: tuple[int, int, int], outer: tuple[int, int, int]) -> Image.Image:
    """Subtle top-left highlight → bottom-right darken. Adds depth without busy texture."""
    img = Image.new("RGB", (size, size), outer)
    px = img.load()
    cx, cy = size * 0.35, size * 0.30
    max_dist = math.hypot(size, size)
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - cx, y - cy) / max_dist
            t = min(1.0, d * 1.6)
            r = int(inner[0] * (1 - t) + outer[0] * t)
            g = int(inner[1] * (1 - t) + outer[1] * t)
            b = int(inner[2] * (1 - t) + outer[2] * t)
            px[x, y] = (r, g, b)
    return img


def _glyph_layer(size: int, color: tuple[int, int, int, int]) -> Image.Image:
    """Render the kitchen glyph centered, sized to fill ~70% of the canvas."""
    font_path = _ensure_font()
    glyph = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(glyph)
    font_size = int(size * 0.72)
    font = ImageFont.truetype(str(font_path), size=font_size)

    # Measure + center. textbbox gives tight bounds including font ascent quirks.
    bbox = draw.textbbox((0, 0), GLYPH_CODEPOINT, font=font, anchor="lt")
    glyph_w = bbox[2] - bbox[0]
    glyph_h = bbox[3] - bbox[1]
    x = (size - glyph_w) // 2 - bbox[0]
    y = (size - glyph_h) // 2 - bbox[1]
    draw.text((x, y), GLYPH_CODEPOINT, font=font, fill=color)
    return glyph


def _drop_shadow(layer: Image.Image, offset: int = 6, blur: int = 14, alpha: int = 90) -> Image.Image:
    """Soft shadow under the glyph for depth on solid backgrounds."""
    shadow_color = (0, 0, 0, alpha)
    a = layer.split()[3]
    shadow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    shadow.paste(shadow_color, mask=a)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    composite = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    composite.paste(shadow, (offset, offset), shadow)
    composite = Image.alpha_composite(composite, layer)
    return composite


def generate() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- 1. Full-bleed source icon (iOS + non-adaptive Android) ---
    bg = _radial_gradient(CANVAS, BRAND_PRIMARY, BRAND_PRIMARY_DARK).convert("RGBA")
    glyph = _glyph_layer(CANVAS, (*WHITE, 255))
    glyph = _drop_shadow(glyph, offset=4, blur=18, alpha=70)
    source = Image.alpha_composite(bg, glyph)
    source.convert("RGB").save(SOURCE, "PNG", optimize=True)
    print(f"Wrote {SOURCE} ({SOURCE.stat().st_size // 1024} KB)")

    # --- 2. Android adaptive foreground (transparent, glyph in 432×432 safe zone) ---
    fg = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    safe_glyph = _glyph_layer(SAFE_ZONE, (*WHITE, 255))
    safe_glyph = _drop_shadow(safe_glyph, offset=2, blur=8, alpha=60)
    offset = (CANVAS - SAFE_ZONE) // 2
    fg.paste(safe_glyph, (offset, offset), safe_glyph)
    fg.save(FOREGROUND, "PNG", optimize=True)
    print(f"Wrote {FOREGROUND} ({FOREGROUND.stat().st_size // 1024} KB)")

    # --- 3. Android adaptive background (solid brand gradient) ---
    bg.convert("RGB").save(BACKGROUND, "PNG", optimize=True)
    print(f"Wrote {BACKGROUND} ({BACKGROUND.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    generate()
