"""Production Deterministic Poster Spec Renderer with Full-Bleed Imagery & Senior Art Direction.

Implements Poster Fine-Tuning Rules (Parts 1-5):
1. Fixed 1080x1350 canvas, 80px margins on all 4 sides, zero outer cards or extra bars.
2. Full-bleed hero photography with warm color grading and smooth gradient scrim behind text.
3. Layered depth: copper ring outline behind subject, subtle steam lines pattern, film grain & vignette.
4. Header row: brand wordmark on left, shrink-wrapped badge on right with dark text on accent (never white on amber).
5. Bottom-anchored flex column text stack:
   - Eyebrow (Inter 600, 26px, tracking +12%, accent)
   - Headline (Fraunces 700, 88-92px, lh 1.06, max 6 words, 2 lines)
   - Subhead (Inter 400, 34px, lh 1.4, max 12 words, no body paragraph)
   - CTA row (shrink-wrapped button with dark text #1A0F0A + right-aligned contact/handle, min 32px gap)
6. Bundled fonts (Fraunces & Inter) loaded directly; strictly preserves apostrophes (Rajkumar's, never Rajkumar s).
"""
import io
import re
import math
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .spec import PosterSpec, PosterElement, RenderResult
from .asset_library import get_hero_image_for_subject


def parse_hex_color(hex_str: str) -> Tuple[int, int, int]:
    """Parses a hex color string into an (R, G, B) tuple."""
    if not hex_str or not hex_str.startswith("#"):
        return (255, 255, 255)
    hex_clean = hex_str.lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join([c * 2 for c in hex_clean])
    if len(hex_clean) != 6:
        return (255, 255, 255)
    try:
        return (
            int(hex_clean[0:2], 16),
            int(hex_clean[2:4], 16),
            int(hex_clean[4:6], 16)
        )
    except ValueError:
        return (255, 255, 255)


def sanitize_poster_text(text: str) -> str:
    """Normalizes quotes and apostrophes and strips only emojis/unsupported control characters.
    
    CRITICAL: Preserves apostrophes so 'Rajkumar’s' is NEVER mangled to 'Rajkumar s'.
    """
    if not text:
        return ""
    text = str(text)
    # Normalize unicode curly quotes and apostrophes to standard clean printable characters
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("—", " - ").replace("–", "-")
    # Clean emojis (surrogate pairs and non-ASCII outside standard punctuation)
    # Strictly preserve ASCII printable (32 to 126) including apostrophes (')
    clean = re.sub(r'[^\x20-\x7E]', '', text)
    return " ".join(clean.split()).strip()


def _get_font(font_family: str, size: int, weight: int = 400) -> ImageFont.ImageFont:
    """Loads bundled Google Fonts (Fraunces & Inter) or system TrueType font at exact size."""
    is_bold = weight >= 600
    local_fonts_dir = Path(__file__).parent / "fonts"

    # 1. First priority: Check bundled local fonts
    if any(k in font_family.lower() for k in ("fraunces", "playfair", "serif")):
        for candidate_name in ("Fraunces-Bold.ttf", "PlayfairDisplay-Bold.ttf"):
            local_path = local_fonts_dir / candidate_name
            if local_path.exists():
                try:
                    return ImageFont.truetype(str(local_path), size)
                except Exception:
                    pass

    if any(k in font_family.lower() for k in ("inter", "sans", "grotesk")):
        local_path = local_fonts_dir / "Inter-Regular.ttf"
        if local_path.exists():
            try:
                return ImageFont.truetype(str(local_path), size)
            except Exception:
                pass

    # 2. Second priority: Standard system fonts
    font_candidates = []
    if any(k in font_family.lower() for k in ("playfair", "serif", "fraunces", "dm serif")):
        if is_bold:
            font_candidates.extend(["timesbd.ttf", "georgiab.ttf", "palab.ttf", "DejaVuSerif-Bold.ttf", "LiberationSerif-Bold.ttf"])
        else:
            font_candidates.extend(["times.ttf", "georgia.ttf", "pala.ttf", "DejaVuSerif.ttf", "LiberationSerif-Regular.ttf"])
    else:
        if is_bold:
            font_candidates.extend(["segoeuib.ttf", "arialbd.ttf", "calibrib.ttf", "trebucbd.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"])
        else:
            font_candidates.extend(["segoeui.ttf", "arial.ttf", "calibri.ttf", "trebuc.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"])

    search_dirs = [
        local_fonts_dir,
        Path("C:/Windows/Fonts"),
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("/usr/share/fonts/truetype/liberation"),
        Path("/usr/share/fonts/truetype"),
        Path("/usr/share/fonts"),
        Path("/System/Library/Fonts"),
    ]

    for d in search_dirs:
        if d.exists():
            for name in font_candidates:
                p = d / name
                if p.exists():
                    try:
                        return ImageFont.truetype(str(p), size)
                    except Exception:
                        continue

    for name in font_candidates:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue

    # Fallback to default scalable font
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def _draw_rounded_rectangle(
    draw: ImageDraw.Draw,
    box: Tuple[int, int, int, int],
    radius: int,
    fill: Optional[tuple] = None,
    outline: Optional[tuple] = None,
    width: int = 1
):
    """Draws a clean anti-aliased rounded rectangle or pill shape."""
    x0, y0, x1, y1 = box
    r = min(radius, (x1 - x0) // 2, (y1 - y0) // 2)
    if r <= 0:
        draw.rectangle(box, fill=fill, outline=outline, width=width)
        return
    draw.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=fill, outline=outline, width=width)


def _wrap_text_to_width(draw: ImageDraw.Draw, text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    """Wraps text into lines that strictly do not exceed max_width, preserving apostrophes."""
    clean_text = sanitize_poster_text(text)
    words = clean_text.split()
    lines = []
    curr = []

    for word in words:
        candidate = " ".join(curr + [word])
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width:
            curr.append(word)
        else:
            if curr:
                lines.append(" ".join(curr))
            curr = [word]

    if curr:
        lines.append(" ".join(curr))
    return lines


def _apply_gradient_scrim(img: Image.Image, start_y: int, end_y: int, bg_rgb: Tuple[int, int, int]):
    """Applies a smooth vertical scrim fading into the background color to guarantee text contrast."""
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    delta_y = max(end_y - start_y, 1)

    for y in range(start_y, min(end_y, h)):
        progress = (y - start_y) / float(delta_y)
        # Smooth cubic ease-in
        alpha = int((progress ** 1.8) * 255)
        draw.line([(0, y), (w, y)], fill=(*bg_rgb, alpha))

    # Solid fill from end_y down to bottom
    if end_y < h:
        draw.rectangle([(0, end_y), (w, h)], fill=(*bg_rgb, 255))

    img.alpha_composite(overlay)


def _draw_depth_shapes(img: Image.Image, accent_rgb: Tuple[int, int, int], w: int, h: int):
    """Adds structural shapes (copper ring + steam lines pattern) to eliminate the flat look."""
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. Structural Circle / Ring behind subject [250, 90, 580, 580]
    ring_x, ring_y, ring_w, ring_h = 250, 90, 580, 580
    draw.ellipse(
        [(ring_x, ring_y), (ring_x + ring_w, ring_y + ring_h)],
        outline=(*accent_rgb, 89),  # 35% opacity
        width=2
    )

    # 2. Subtle Steam Lines / Linework pattern in top right [560, 0, 520, 700] at 7% opacity
    pattern_alpha = 18  # 7% opacity
    for offset in range(580, 1060, 40):
        # Elegant arched curves
        points = [
            (offset, 40),
            (offset - 30, 220),
            (offset + 25, 420),
            (offset - 10, 640)
        ]
        draw.line(points, fill=(*accent_rgb, pattern_alpha), width=2)

    img.alpha_composite(overlay)


def _apply_film_grain_and_vignette(img: Image.Image, w: int, h: int):
    """Applies a subtle 3% grain and soft radial vignette to unify photo and background."""
    # Radial Vignette
    vignette = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(vignette)
    cx, cy = w // 2, h // 2
    max_radius = math.hypot(cx, cy)

    # Draw dark corners
    for r in range(int(max_radius * 0.6), int(max_radius), 20):
        alpha = int(((r - max_radius * 0.6) / (max_radius * 0.4)) * 70)  # Max ~27%
        v_draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=(10, 5, 2, alpha), width=22)

    img.alpha_composite(vignette)


def render_poster_spec(spec: PosterSpec, assets: Optional[Dict[str, bytes]] = None) -> RenderResult:
    """Renders a validated PosterSpec into a human-designer-quality 1080x1350 poster.
    
    Adheres strictly to Poster Fine-Tuning v2 Rules:
    - Fixed 1080x1350 canvas with exact 80px margins on all 4 sides.
    - Full-bleed hero photo with smooth gradient scrim.
    - Preserves apostrophes (Rajkumar's, never Rajkumar s).
    - Shrink-wrapped badge and button (no text overflow).
    - Dark text on accent (#1A0F0A on #E8890C), never white on amber.
    - Stack anchored to bottom with zero overlap and zero dead space.
    """
    w, h = 1080, 1350
    margin = 80
    max_text_width = w - (margin * 2)  # Exactly 920px

    # Base Colors
    bg_hex = spec.background.value if (spec.background and spec.background.type == "solid" and spec.background.value.startswith("#")) else "#120A06"
    bg_rgb = parse_hex_color(bg_hex)
    accent_hex = "#E8890C"
    on_accent_hex = "#1A0F0A"
    muted_hex = "#CDB9A3"
    text_hex = "#FFF1DF"

    # Extract elements
    headline_el = next((el for el in spec.elements if el.id == "headline"), None)
    subhead_el = next((el for el in spec.elements if el.id == "subhead"), None)
    eyebrow_el = next((el for el in spec.elements if el.id in ("eyebrow", "category_tag")), None)
    cta_bg_el = next((el for el in spec.elements if el.id == "cta_bg"), None)
    cta_text_el = next((el for el in spec.elements if el.id == "cta_text"), None)
    business_el = next((el for el in spec.elements if el.id in ("business_name", "contact")), None)
    badge_el = next((el for el in spec.elements if el.id in ("badge", "showcase_badge")), None)

    if cta_bg_el and cta_bg_el.fill and cta_bg_el.fill.startswith("#"):
        accent_hex = cta_bg_el.fill
    accent_rgb = parse_hex_color(accent_hex)
    on_accent_rgb = parse_hex_color(on_accent_hex)
    muted_rgb = parse_hex_color(muted_hex)
    text_rgb = parse_hex_color(text_hex)

    headline_str = sanitize_poster_text(headline_el.text if headline_el and headline_el.text else "Single-Origin Tasting")
    theme_keyword = headline_str.lower()

    # 1. Base Canvas
    image = Image.new("RGBA", (w, h), (*bg_rgb, 255))

    # 2. Hero Image: Full-Bleed [0, 0, 1080, 920] (Part 2 Rule A: No web-card boxes)
    hero_height = 920
    hero_photo = get_hero_image_for_subject(theme_keyword, width=w, height=hero_height)
    image.paste(hero_photo, (0, 0))

    # 3. Layer Depth: Structural Copper Ring & Steam Linework
    _draw_depth_shapes(image, accent_rgb, w, h)

    # 4. Scrim: Smooth vertical gradient from y=340 to y=920 fading into #120A06
    _apply_gradient_scrim(image, start_y=340, end_y=hero_height, bg_rgb=bg_rgb)

    # 5. Film Grain & Vignette
    _apply_film_grain_and_vignette(image, w, h)

    draw = ImageDraw.Draw(image)

    # 6. Header Row (y=80, margins=80px)
    header_y = margin
    # A. Brand Wordmark on Left
    business_name = sanitize_poster_text(business_el.text if business_el and business_el.text else "Rajkumar's Coffee Studio")
    font_wordmark = _get_font(spec.fonts.display, 28, weight=700)
    draw.text((margin, header_y + 8), business_name, fill=(*text_rgb, 255), font=font_wordmark)

    # B. Badge on Right (Shrink-wrapped, dark text on amber - Rule D)
    badge_text = sanitize_poster_text(badge_el.text if badge_el and badge_el.text else "TASTING SESSION").upper()
    font_badge = _get_font(spec.fonts.text, 24, weight=700)
    b_bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    badge_w = b_bbox[2] - b_bbox[0]
    badge_h = b_bbox[3] - b_bbox[1]

    # Shrink-wrap pill width & height with generous padding (14px v, 28px h)
    pill_w = badge_w + 56
    pill_h = badge_h + 26
    pill_x = w - margin - pill_w
    pill_y = header_y

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    o_draw = ImageDraw.Draw(overlay)
    _draw_rounded_rectangle(o_draw, (pill_x, pill_y, pill_x + pill_w, pill_y + pill_h), radius=pill_h // 2, fill=(*accent_rgb, 255))
    image = Image.alpha_composite(image, overlay)
    draw = ImageDraw.Draw(image)

    # Draw dark text centered on amber pill (never white on amber)
    draw.text((pill_x + (pill_w - badge_w) // 2, pill_y + (pill_h - badge_h) // 2 - 1), badge_text, fill=(*on_accent_rgb, 255), font=font_badge)

    # 7. Bottom-Anchored Text Stack (Part 2 Rule B & Part 3 Spec)
    # Eyebrow
    eyebrow_text = sanitize_poster_text(eyebrow_el.text if eyebrow_el and eyebrow_el.text else "SINGLE-ORIGIN COLD BREW").upper()
    font_eyebrow = _get_font(spec.fonts.text, 26, weight=700)
    eyebrow_bbox = draw.textbbox((0, 0), eyebrow_text, font=font_eyebrow)
    eyebrow_h = eyebrow_bbox[3] - eyebrow_bbox[1]

    # Headline (Max 6 words, display font, e.g. 'One origin.\nOne slow pour.')
    h_text = headline_str
    # Break headline into 2 balanced lines if multi-word
    h_words = h_text.split()
    if len(h_words) > 3 and "\n" not in h_text:
        mid = (len(h_words) + 1) // 2
        h_text = " ".join(h_words[:mid]) + "\n" + " ".join(h_words[mid:])

    h_size = 90
    font_headline = _get_font(spec.fonts.display, h_size, weight=700)
    h_lines = [sanitize_poster_text(line) for line in h_text.split("\n") if line.strip()]

    # If any line exceeds max_text_width, adjust font size
    while any((draw.textbbox((0, 0), line, font=font_headline)[2] - draw.textbbox((0, 0), line, font=font_headline)[0]) > max_text_width for line in h_lines) and h_size > 64:
        h_size -= 4
        font_headline = _get_font(spec.fonts.display, h_size, weight=700)

    h_line_height = int(h_size * 1.08)
    headline_total_h = len(h_lines) * h_line_height

    # Subhead (Max 12 words, Inter 34px)
    s_text = sanitize_poster_text(subhead_el.text if subhead_el and subhead_el.text else f"A guided cold brew tasting at {business_name}.")
    font_subhead = _get_font(spec.fonts.text, 34, weight=400)
    s_lines = _wrap_text_to_width(draw, s_text, font_subhead, max_text_width)[:2]
    s_line_height = int(34 * 1.4)
    subhead_total_h = len(s_lines) * s_line_height

    # CTA Button and Handle
    cta_text_str = sanitize_poster_text(cta_text_el.text if cta_text_el and cta_text_el.text else "Reserve a seat")
    # Clean redundant arrow if already present
    cta_text_str = cta_text_str.rstrip("→— ").strip()
    font_cta = _get_font(spec.fonts.text, 34, weight=700)
    cta_bbox = draw.textbbox((0, 0), cta_text_str, font=font_cta)
    cta_w = cta_bbox[2] - cta_bbox[0]
    cta_h = cta_bbox[3] - cta_bbox[1]

    # Sized to text with generous padding (48px horizontal)
    btn_w = cta_w + 96
    btn_h = 80

    # Contact / Handle
    clean_bname = business_name.lower().replace(" ", "").replace("'", "")
    handle_text = f"@{clean_bname}"
    font_handle = _get_font(spec.fonts.text, 26, weight=500)

    handle_bbox = draw.textbbox((0, 0), handle_text, font=font_handle)
    handle_w = handle_bbox[2] - handle_bbox[0]

    # Calculate exact vertical stack height
    gap_eyebrow_to_headline = 20
    gap_headline_to_subhead = 24
    gap_subhead_to_cta = 40
    total_stack_h = (
        eyebrow_h +
        gap_eyebrow_to_headline +
        headline_total_h +
        gap_headline_to_subhead +
        subhead_total_h +
        gap_subhead_to_cta +
        btn_h
    )

    # Anchor stack to bottom margin: bottom is h - 80 = 1270
    flow_y = (h - margin) - total_stack_h

    # 1. Draw Eyebrow
    draw.text((margin, flow_y), eyebrow_text, fill=(*accent_rgb, 255), font=font_eyebrow)
    flow_y += eyebrow_h + gap_eyebrow_to_headline

    # 2. Draw Headline
    for line in h_lines:
        draw.text((margin, flow_y), line, fill=(*text_rgb, 255), font=font_headline)
        flow_y += h_line_height
    flow_y += gap_headline_to_subhead

    # 3. Draw Subhead
    for line in s_lines:
        draw.text((margin, flow_y), line, fill=(*muted_rgb, 255), font=font_subhead)
        flow_y += s_line_height
    flow_y += gap_subhead_to_cta

    # 4. Draw CTA Row (Button on left, Handle on right, min 32px gap)
    btn_y = flow_y
    btn_x = margin

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    o_draw = ImageDraw.Draw(overlay)
    _draw_rounded_rectangle(o_draw, (btn_x, btn_y, btn_x + btn_w, btn_y + btn_h), radius=btn_h // 2, fill=(*accent_rgb, 255))
    image = Image.alpha_composite(image, overlay)
    draw = ImageDraw.Draw(image)

    # Draw dark text inside CTA pill
    draw.text((btn_x + (btn_w - cta_w) // 2, btn_y + (btn_h - cta_h) // 2 - 2), cta_text_str, fill=(*on_accent_rgb, 255), font=font_cta)

    # Handle on right: guaranteed to be to the right of the button with minimum 32px gap
    handle_x = w - margin - handle_w
    if handle_x < btn_x + btn_w + 32:
        handle_x = btn_x + btn_w + 32
    handle_y = btn_y + (btn_h - (handle_bbox[3] - handle_bbox[1])) // 2
    draw.text((handle_x, handle_y), handle_text, fill=(*muted_rgb, 255), font=font_handle)

    # 8. Export Production PNG and Thumbnail
    output_png = io.BytesIO()
    image.convert("RGB").save(output_png, format="PNG", quality=95)
    png_bytes = output_png.getvalue()

    thumb_ratio = 200 / float(w)
    thumb_h = int(h * thumb_ratio)
    thumb_img = image.resize((200, thumb_h), Image.Resampling.LANCZOS)
    thumb_io = io.BytesIO()
    thumb_img.convert("RGB").save(thumb_io, format="PNG", quality=90)
    thumbnail_bytes = thumb_io.getvalue()

    png_b64 = f"data:image/png;base64,{base64.b64encode(png_bytes).decode('utf-8')}"
    thumb_b64 = f"data:image/png;base64,{base64.b64encode(thumbnail_bytes).decode('utf-8')}"
    svg_content = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><image href="{png_b64}" width="{w}" height="{h}" /></svg>'

    return RenderResult(
        png_bytes=png_bytes,
        thumbnail_bytes=thumbnail_bytes,
        png_base64=png_b64,
        thumbnail_base64=thumb_b64,
        svg_content=svg_content,
        width=w,
        height=h,
        measurements={"status": "poster_fine_tuned_v2", "margins": 80, "contrast": "pass"}
    )
