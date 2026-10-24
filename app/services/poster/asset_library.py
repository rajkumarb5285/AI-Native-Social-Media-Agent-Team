"""Curated Hero Image & Pattern Asset Library.

Rule 7 of the Poster Design Rulebook:
"Image fallback chain: generated image, then library image, then a pattern and gradient composition. Never ship an empty box."

Provides verified, ultra-high resolution royalty-free photography backdrops and textures
categorized by industry vertical.
"""
import io
import urllib.request
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFilter


# Verified high-resolution photographic backdrops (licensed for commercial use / Unsplash CDN)
LIBRARY_IMAGES: Dict[str, str] = {
    "coffee": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?auto=format&fit=crop&w=1080&q=85",
    "cafe": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=1080&q=85",
    "cold_brew": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?auto=format&fit=crop&w=1080&q=85",
    "food": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1080&q=85",
    "dining": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1080&q=85",
    "tech": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1080&q=85",
    "ai": "https://images.unsplash.com/photo-1634017839464-5c339ebe3cb4?auto=format&fit=crop&w=1080&q=85",
    "festival": "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=1080&q=85",
    "diwali": "https://images.unsplash.com/photo-1605647540924-852290f6b0d5?auto=format&fit=crop&w=1080&q=85",
    "luxury": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1080&q=85",
    "sale": "https://images.unsplash.com/photo-1607082348824-0a96f2a4b9da?auto=format&fit=crop&w=1080&q=85",
    "wellness": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?auto=format&fit=crop&w=1080&q=85",
    "event": "https://images.unsplash.com/photo-1511578314322-379afb476865?auto=format&fit=crop&w=1080&q=85",
}

# In-memory cache for downloaded library images
_IMAGE_CACHE: Dict[str, Image.Image] = {}


def get_hero_image_for_subject(subject_or_category: str, width: int = 952, height: int = 540) -> Image.Image:
    """Retrieves or synthesizes an on-brand hero image. Never returns an empty box."""
    term = subject_or_category.lower()

    # Find matching keyword
    matched_key = None
    for k in LIBRARY_IMAGES:
        if k in term:
            matched_key = k
            break
    if not matched_key:
        matched_key = "coffee" if any(w in term for w in ("roastery", "brew", "espresso", "latte")) else "food"

    url = LIBRARY_IMAGES.get(matched_key, LIBRARY_IMAGES["coffee"])

    # 1. Try fetching real photo from cache or CDN
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

    # 2. Rule 7 Fallback: Rich atmospheric gradient + geometric pattern composition (NEVER an empty box)
    return generate_pattern_composition(width, height, matched_key)


def generate_pattern_composition(width: int, height: int, theme_key: str) -> Image.Image:
    """Creates a high-end atmospheric pattern backdrop with soft lighting and ambient depth."""
    theme_palettes = {
        "coffee": ((38, 20, 12), (18, 9, 5), (217, 119, 6)),
        "food": ((42, 18, 10), (20, 8, 4), (234, 88, 12)),
        "tech": ((10, 20, 45), (5, 10, 24), (59, 130, 246)),
        "festival": ((45, 15, 60), (20, 5, 28), (234, 179, 8)),
        "wellness": ((8, 42, 38), (4, 20, 18), (16, 185, 129)),
        "luxury": ((24, 23, 20), (12, 11, 10), (212, 175, 55)),
        "sale": ((50, 10, 15), (24, 5, 8), (239, 68, 68))
    }
    c_top, c_bot, accent = theme_palettes.get(theme_key, theme_palettes["coffee"])

    img = Image.new("RGBA", (width, height), (*c_bot, 255))
    draw = ImageDraw.Draw(img)

    # Vertical gradient
    for y in range(height):
        t = y / float(height - 1)
        r = int(c_top[0] * (1 - t) + c_bot[0] * t)
        g = int(c_top[1] * (1 - t) + c_bot[1] * t)
        b = int(c_top[2] * (1 - t) + c_bot[2] * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # Ambient radial spotlight
    spotlight = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(spotlight)
    cx, cy = width // 2, height // 2
    for rad in range(min(width, height) // 2, 20, -15):
        alpha = int(35 * (1.0 - rad / (min(width, height) / 2.0)))
        s_draw.ellipse(
            [(cx - rad, cy - rad), (cx + rad, cy + rad)],
            fill=(accent[0], accent[1], accent[2], alpha)
        )
    spotlight = spotlight.filter(ImageFilter.GaussianBlur(radius=24))
    img = Image.alpha_composite(img, spotlight)

    # Architectural line pattern
    pattern = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(pattern)
    for x in range(0, width, 48):
        p_draw.line([(x, 0), (x + 80, height)], fill=(255, 255, 255, 8), width=1)
    img = Image.alpha_composite(img, pattern)

    return img.convert("RGB")
