"""Curated Hero Image & Pattern Asset Library.

Rule 7 of the Poster Design Rulebook:
"Image fallback chain: generated image, then library image, then a pattern and gradient composition. Never ship an empty box."

Provides verified, ultra-high resolution royalty-free photography backdrops and textures
strictly categorized by the 14 core industry verticals. Zero coffee defaults for other verticals.
"""
import io
import urllib.request
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFilter
from app.services.creative_direction import resolve_vertical


# Verified high-resolution photographic backdrops (licensed for commercial use / Unsplash CDN)
LIBRARY_IMAGES: Dict[str, str] = {
    "sneakers_streetwear": "https://images.unsplash.com/photo-1552346154-21d32810aba3?auto=format&fit=crop&w=1080&q=85",
    "sneaker": "https://images.unsplash.com/photo-1552346154-21d32810aba3?auto=format&fit=crop&w=1080&q=85",
    "salon_spa": "https://images.unsplash.com/photo-1560066984-138dadb4c035?auto=format&fit=crop&w=1080&q=85",
    "salon": "https://images.unsplash.com/photo-1560066984-138dadb4c035?auto=format&fit=crop&w=1080&q=85",
    "clinic_healthcare": "https://images.unsplash.com/photo-1629909613654-28e377c37b09?auto=format&fit=crop&w=1080&q=85",
    "clinic": "https://images.unsplash.com/photo-1629909613654-28e377c37b09?auto=format&fit=crop&w=1080&q=85",
    "dental": "https://images.unsplash.com/photo-1629909613654-28e377c37b09?auto=format&fit=crop&w=1080&q=85",
    "real_estate": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1080&q=85",
    "architecture": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1080&q=85",
    "cafe_coffee": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?auto=format&fit=crop&w=1080&q=85",
    "coffee": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?auto=format&fit=crop&w=1080&q=85",
    "cafe": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=1080&q=85",
    "gym_fitness": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=1080&q=85",
    "gym": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=1080&q=85",
    "fitness": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=1080&q=85",
    "boutique_fashion": "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=1080&q=85",
    "fashion": "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=1080&q=85",
    "jewelry_luxury": "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?auto=format&fit=crop&w=1080&q=85",
    "luxury": "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?auto=format&fit=crop&w=1080&q=85",
    "education_tutoring": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=1080&q=85",
    "education": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=1080&q=85",
    "tech_saas": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1080&q=85",
    "tech": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1080&q=85",
    "auto_detail": "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=1080&q=85",
    "auto": "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=1080&q=85",
    "travel_hospitality": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1080&q=85",
    "travel": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1080&q=85",
    "event_wedding": "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=1080&q=85",
    "event": "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=1080&q=85",
    "local_services": "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=1080&q=85",
    "services": "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=1080&q=85"
}

# In-memory cache for downloaded library images
_IMAGE_CACHE: Dict[str, Image.Image] = {}


def get_hero_image_for_subject(subject_or_category: str, width: int = 952, height: int = 540) -> Image.Image:
    """Retrieves or synthesizes an on-brand hero image. Strictly industry-aware.
    Never returns an empty box and never defaults to coffee for other businesses.
    """
    term = (subject_or_category or "").lower()

    # 1. Direct key match
    matched_key = None
    for k in LIBRARY_IMAGES:
        if k in term:
            matched_key = k
            break

    # 2. If no direct key match, resolve via 14-vertical taxonomy
    if not matched_key:
        resolved_vert = resolve_vertical(term)
        matched_key = resolved_vert if resolved_vert in LIBRARY_IMAGES else "local_services"

    url = LIBRARY_IMAGES.get(matched_key, LIBRARY_IMAGES["local_services"])

    # 3. Try fetching real photo from cache or CDN
    if url in _IMAGE_CACHE:
        cached = _IMAGE_CACHE[url]
        return cached.resize((width, height), Image.Resampling.LANCZOS)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=3.5) as response:
            raw_data = response.read()
            img = Image.open(io.BytesIO(raw_data)).convert("RGB")
            # Center crop to aspect ratio
            img_w, img_h = img.size
            target_aspect = width / float(height)
            curr_aspect = img_w / float(img_h)

            if curr_aspect > target_aspect:
                new_w = int(img_h * target_aspect)
                left = (img_w - new_w) // 2
                img = img.crop((left, 0, left + new_w, img_h))
            else:
                new_h = int(img_w / target_aspect)
                top = (img_h - new_h) // 2
                img = img.crop((0, top, img_w, top + new_h))

            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            _IMAGE_CACHE[url] = resized
            return resized
    except Exception:
        pass

    # 4. Fallback: Rich atmospheric gradient + geometric pattern composition
    return generate_pattern_composition(width, height, matched_key)


def generate_pattern_composition(width: int, height: int, theme_key: str) -> Image.Image:
    """Creates a high-end atmospheric pattern backdrop with soft lighting and ambient depth."""
    theme_palettes = {
        "sneakers_streetwear": ((26, 26, 36), (13, 13, 17), (255, 51, 102)),
        "sneakers": ((26, 26, 36), (13, 13, 17), (255, 51, 102)),
        "salon_spa": ((35, 31, 28), (20, 17, 16), (194, 155, 127)),
        "salon": ((35, 31, 28), (20, 17, 16), (194, 155, 127)),
        "clinic_healthcare": ((15, 35, 56), (8, 19, 31), (2, 132, 199)),
        "clinic": ((15, 35, 56), (8, 19, 31), (2, 132, 199)),
        "real_estate": ((22, 29, 42), (11, 15, 23), (212, 175, 55)),
        "cafe_coffee": ((38, 20, 12), (18, 9, 5), (217, 119, 6)),
        "coffee": ((38, 20, 12), (18, 9, 5), (217, 119, 6)),
        "gym_fitness": ((24, 24, 27), (9, 9, 11), (225, 29, 72)),
        "gym": ((24, 24, 27), (9, 9, 11), (225, 29, 72)),
        "boutique_fashion": ((23, 23, 23), (10, 10, 10), (229, 229, 229)),
        "jewelry_luxury": ((14, 19, 28), (5, 7, 10), (212, 175, 55)),
        "education_tutoring": ((21, 31, 54), (11, 17, 32), (37, 99, 235)),
        "tech_saas": ((17, 24, 39), (8, 11, 20), (99, 102, 241)),
        "tech": ((17, 24, 39), (8, 11, 20), (99, 102, 241)),
        "auto_detail": ((22, 25, 34), (10, 11, 14), (239, 68, 68)),
        "auto": ((22, 25, 34), (10, 11, 14), (239, 68, 68)),
        "travel_hospitality": ((19, 35, 51), (10, 20, 29), (14, 165, 233)),
        "event_wedding": ((32, 20, 24), (18, 11, 13), (226, 177, 177)),
        "local_services": ((21, 31, 54), (11, 17, 32), (37, 99, 235)),
    }
    c_top, c_bot, accent = theme_palettes.get(theme_key, theme_palettes["local_services"])

    img = Image.new("RGBA", (width, height), (*c_bot, 255))
    draw = ImageDraw.Draw(img)

    # Subtle ambient gradient
    for y in range(height):
        factor = y / float(height)
        r = int(c_top[0] * (1 - factor) + c_bot[0] * factor)
        g = int(c_top[1] * (1 - factor) + c_bot[1] * factor)
        b = int(c_top[2] * (1 - factor) + c_bot[2] * factor)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # Architectural atmospheric glow
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    cx, cy = width // 2, int(height * 0.45)
    radius = min(width, height) // 2
    glow_draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(*accent, 28))
    glow = glow.filter(ImageFilter.GaussianBlur(radius // 3))
    img = Image.alpha_composite(img, glow)

    return img.convert("RGB")
