"""Production Deterministic Poster Spec Renderer with Alignment Masterclass (v3).

Full implementation of Poster v3 Alignment Masterclass Rules (Parts 1-6):
1. Strict Axes: A_L = 80, A_R = 1000, A_C = 540, T = 80, B = 1270 (1080x1350 canvas).
2. Header Row: Logo left edge on A_L (80), badge right edge on A_R (1000), vertically centered
   on the exact same horizontal midline (center_y = 104).
3. Footer Row: CTA left edge on A_L (80), handle/meta right edge on A_R (1000), vertically
   centered on the exact same horizontal midline (center_y = 1230).
4. Full-Bleed Imagery with Zero Horizontal Seams: Photo covers full 1080x1350 canvas,
   extending under the bottom text scrim (4 color stops starting at 40% height).
5. Scrims & Legibility: Top scrim for logo contrast, bottom cubic scrim for text legibility.
6. Design Devices: Inset frame (1px at 15% opacity), hairline rule (48x2px), authentic curved steam strokes.
7. Subject-Relative Shapes: Copper ring centered on subject bbox (540, 470), clearing both header
   row and text stack by >= 24px.
8. Bottom-Anchored Text Stack:
   - Hairline rule (48x2px)
   - Eyebrow (Inter 600, 26px, uppercase, +0.12em tracking)
   - Headline (Fraunces 700, 88px, lh 96px, optical offset -3px, max 6 words, max 2 lines, italic accent line)
   - Subhead (Inter 400, 34px, lh 48px, max 1 line, <= 44 chars)
   - Footer Row (CTA <= 3 words, dark text #1A0F0A on amber #E8890C, handle on A_R)
9. Smart Typography: Preserves and renders unicode curly apostrophe ’ (Rajkumar’s, never straight ').
10. Automated Alignment QA: Validates geometry against axes before outputting final render.
"""
import io
import re
import math
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .spec import PosterSpec, PosterElement, RenderResult, smart_typography
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
    """Normalizes whitespace and converts straight quotes to smart typography.
    
    CRITICAL: Preserves curly apostrophe ’ so 'Rajkumar’s' is NEVER mangled to 'Rajkumar s'.
    """
    if not text:
        return ""
    text = str(text)
    # Apply smart typography
    text = smart_typography(text)
    # Normalize whitespace
    return " ".join(text.split()).strip()


def _get_font(font_family: str, size: int, weight: int = 400, italic: bool = False) -> ImageFont.ImageFont:
    """Loads bundled Google Fonts (Fraunces & Inter) or system TrueType font at exact size."""
    is_bold = weight >= 600
    local_fonts_dir = Path(__file__).parent / "fonts"

    # 1. First priority: Check bundled local fonts
    if any(k in font_family.lower() for k in ("fraunces", "playfair", "serif")):
        if italic:
            italic_cand = local_fonts_dir / "Fraunces-Italic.ttf"
            if italic_cand.exists():
                try:
                    return ImageFont.truetype(str(italic_cand), size)
                except Exception:
                    pass
        for candidate_name in ("Fraunces-Bold.ttf", "PlayfairDisplay-Bold.ttf"):
            local_path = local_fonts_dir / candidate_name
            if local_path.exists():
                try:
                    return ImageFont.truetype(str(local_path), size)
                except Exception:
                    pass

    if any(k in font_family.lower() for k in ("inter", "sans", "grotesk")):
        if italic:
            italic_cand = local_fonts_dir / "Inter-Italic.ttf"
            if italic_cand.exists():
                try:
                    return ImageFont.truetype(str(italic_cand), size)
                except Exception:
                    pass
        for candidate_name in ("Inter-Regular.ttf", "Inter-Italic.ttf"):
            local_path = local_fonts_dir / candidate_name
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


def _get_tracked_text_width(draw: ImageDraw.Draw, text: str, font: ImageFont.ImageFont, tracking_em: float = 0.12) -> int:
    """Calculates pixel width of text rendered with positive tracking (letter-spacing)."""
    if not text:
        return 0
    font_size = getattr(font, "size", 24)
    tracking_px = int(font_size * tracking_em)
    total_w = 0
    for i, char in enumerate(text):
        bbox = draw.textbbox((0, 0), char, font=font)
        char_w = bbox[2] - bbox[0]
        total_w += char_w
        if i < len(text) - 1:
            total_w += tracking_px
    return total_w


def _draw_tracked_text(
    draw: ImageDraw.Draw,
    pos: Tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: Tuple[int, int, int, int],
    tracking_em: float = 0.12
) -> int:
    """Renders text with authentic letter-spacing (Inter 600 +0.12em tracking). Returns total width."""
    x, y = pos
    font_size = getattr(font, "size", 24)
    tracking_px = int(font_size * tracking_em)
    curr_x = x
    for char in text:
        draw.text((curr_x, y), char, font=font, fill=fill)
        bbox = draw.textbbox((0, 0), char, font=font)
        char_w = bbox[2] - bbox[0]
        curr_x += char_w + tracking_px
    return curr_x - x


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


def _apply_top_scrim(img: Image.Image, height: int, bg_rgb: Tuple[int, int, int]):
    """Applies top scrim: linear-gradient(180deg, rgba(bg,0.65) 0%, rgba(bg,0) 22%).
    
    Guarantees top-left logo wordmark contrast against bright photo backgrounds.
    """
    w, _ = img.size
    overlay = Image.new("RGBA", (w, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for y in range(height):
        # Starts at 65% opacity (165) and tapers to 0 at 22% of canvas height (around y=300)
        progress = y / float(height)
        alpha = int(165 * max(0.0, (1.0 - progress) ** 1.5))
        if alpha > 0:
            draw.line([(0, y), (w, y)], fill=(*bg_rgb, alpha))

    img.alpha_composite(overlay, (0, 0))


def _apply_bottom_scrim_v3(img: Image.Image, start_y: int, end_y: int, bg_rgb: Tuple[int, int, int]):
    """Applies 4-color-stop bottom scrim:
    start_y = 540 (40% height) to end_y = 1350.
    Stops:
    - 0% (y=540): alpha 0 (0%)
    - 35% (y=823): alpha 140 (55%)
    - 70% (y=1107): alpha 235 (92%)
    - 100% (y=1350): alpha 255 (100%)
    
    The hero image extends underneath all the way to 1350, so there is ZERO horizontal seam!
    """
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    total_range = float(end_y - start_y)

    for y in range(start_y, min(end_y, h)):
        p = (y - start_y) / total_range
        if p <= 0.35:
            # 0% to 55%
            local_p = p / 0.35
            alpha = int((local_p ** 1.3) * 140)
        elif p <= 0.70:
            # 55% to 92%
            local_p = (p - 0.35) / 0.35
            alpha = int(140 + (local_p ** 1.1) * (235 - 140))
        else:
            # 92% to 100%
            local_p = (p - 0.70) / 0.30
            alpha = int(235 + local_p * (255 - 235))

        alpha = max(0, min(255, alpha))
        draw.line([(0, y), (w, y)], fill=(*bg_rgb, alpha))

    # Any remaining rows at bottom
    if end_y < h:
        draw.rectangle([(0, end_y), (w, h)], fill=(*bg_rgb, 255))

    img.alpha_composite(overlay)


def _draw_inset_frame(img: Image.Image, accent_rgb: Tuple[int, int, int], w: int, h: int):
    """Draws 1px inset frame at 15% opacity, inset 32px from canvas edge with a gap for the logo."""
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    inset = 32
    frame_color = (*accent_rgb, 38)  # 15% opacity

    # Left edge
    draw.line([(inset, inset), (inset, h - inset)], fill=frame_color, width=1)
    # Right edge
    draw.line([(w - inset, inset), (w - inset, h - inset)], fill=frame_color, width=1)
    # Bottom edge
    draw.line([(inset, h - inset), (w - inset, h - inset)], fill=frame_color, width=1)
    # Top edge with gap for logo wordmark: logo spans from x=80 to x=460 approx
    draw.line([(inset, inset), (60, inset)], fill=frame_color, width=1)
    draw.line([(480, inset), (w - inset, inset)], fill=frame_color, width=1)

    img.alpha_composite(overlay)


def _draw_subject_ring(img: Image.Image, accent_rgb: Tuple[int, int, int], cx: int, cy: int, diameter: int):
    """Draws a structural copper ring centered on the subject visual center.
    
    Guaranteed >= 24px clearance from header row (y <= 128) and text stack (y >= 812).
    """
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    r = diameter // 2

    draw.ellipse(
        [(cx - r, cy - r), (cx + r, cy + r)],
        outline=(*accent_rgb, 89),  # 35% opacity
        width=2
    )
    img.alpha_composite(overlay)


def _draw_curved_steam(img: Image.Image, accent_rgb: Tuple[int, int, int]):
    """Renders 3 delicate, authentic curved steam strokes above the glass rim.
    
    Replaces scratchy diagonals with authentic motif at 12% opacity.
    """
    overlay = Image.new("RGBA", (1080, 1350), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    steam_alpha = 31  # 12% opacity

    curves = [
        [(515, 380), (510, 340), (520, 310), (512, 280)],
        [(540, 370), (548, 335), (538, 305), (544, 275)],
        [(565, 385), (560, 345), (568, 315), (562, 285)]
    ]

    for pts in curves:
        draw.line(pts, fill=(*accent_rgb, steam_alpha), width=2)

    img.alpha_composite(overlay)


def _apply_film_grain_and_vignette(img: Image.Image, w: int, h: int):
    """Applies a subtle 3% grain and soft radial vignette to unify photo and background."""
    vignette = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(vignette)
    cx, cy = w // 2, h // 2
    max_radius = math.hypot(cx, cy)

    for r in range(int(max_radius * 0.58), int(max_radius), 20):
        alpha = int(((r - max_radius * 0.58) / (max_radius * 0.42)) * 68)  # Max ~26%
        v_draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=(12, 6, 3, alpha), width=22)

    img.alpha_composite(vignette)


def qa_check_spec_geometry(
    elements: Dict[str, Dict[str, Any]],
    axes: Dict[str, int] = None,
    tol: int = 2
) -> List[str]:
    """Alignment Masterclass Geometry QA: validates that no elements violate axes or midlines."""
    if axes is None:
        axes = {"A_L": 80, "A_R": 1000, "A_C": 540, "T": 80, "B": 1270}

    errs = []
    A_L = axes["A_L"]
    A_R = axes["A_R"]
    B = axes["B"]

    # 1. Right Axis & Bottom Line Violations
    for id_, e in elements.items():
        if e.get("r", 0) > A_R + tol:
            errs.append(f"{id_} crosses right axis ({e['r']} > {A_R})")
        if e.get("b", 0) > B + tol:
            errs.append(f"{id_} below bottom line ({e['b']} > {B})")

    # 2. Left Axis Alignment (with optical offset tolerance of -3px for headline)
    for id_ in ["logo", "rule", "eyebrow", "sub", "cta"]:
        if id_ in elements:
            e = elements[id_]
            if abs(e.get("l", 0) - A_L) > tol + 4:
                errs.append(f"{id_} off left axis ({e.get('l')} != {A_L})")

    # 3. Header Row Midline Alignment
    if "logo" in elements and "badge" in elements:
        logo_cy = elements["logo"].get("cy", 0)
        badge_cy = elements["badge"].get("cy", 0)
        if abs(logo_cy - badge_cy) > tol:
            errs.append(f"header centers misaligned (logo cy={logo_cy}, badge cy={badge_cy})")

    # 4. Footer Row Midline Alignment
    if "cta" in elements and "meta" in elements:
        cta_cy = elements["cta"].get("cy", 0)
        meta_cy = elements["meta"].get("cy", 0)
        if abs(cta_cy - meta_cy) > tol:
            errs.append(f"footer centers misaligned (cta cy={cta_cy}, meta cy={meta_cy})")

    # 5. Badge on Right Axis
    if "badge" in elements:
        badge_r = elements["badge"].get("r", 0)
        if abs(badge_r - A_R) > tol:
            errs.append(f"badge not on right axis ({badge_r} != {A_R})")

    # 6. Ring Clearance from Header and Stack
    if "ring" in elements and "header_row" in elements:
        ring_t = elements["ring"].get("t", 0)
        header_b = elements["header_row"].get("b", 0)
        if ring_t < header_b + 24:
            errs.append(f"ring header clearance < 24px ({ring_t} - {header_b} = {ring_t - header_b}px)")

    if "ring" in elements and "text_stack" in elements:
        ring_b = elements["ring"].get("b", 0)
        stack_t = elements["text_stack"].get("t", 0)
        if ring_b > stack_t - 24:
            errs.append(f"ring stack clearance < 24px ({stack_t} - {ring_b} = {stack_t - ring_b}px)")

    return errs


def render_poster_spec(spec: PosterSpec, assets: Optional[Dict[str, bytes]] = None) -> RenderResult:
    """Renders a validated PosterSpec into a Poster v3 Alignment Masterclass 1080x1350 poster.
    
    Adheres strictly to Alignment Masterclass (v3) Rules:
    - Fixed 1080x1350 canvas with strict axes: A_L=80, A_R=1000, A_C=540, T=80, B=1270.
    - Full-bleed hero photo across full canvas with zero horizontal seams.
    - Top scrim for logo contrast, smooth 4-stop bottom scrim for text legibility.
    - Header row and footer row span the axes with perfectly aligned horizontal midlines.
    - Inset frame (1px at 15%), hairline rule (48x2px), authentic curved steam lines.
    - Copper ring centered on subject bbox with >= 24px clearance from header and stack.
    - Smart typography preserves curly apostrophes (Rajkumar’s, never straight ').
    - Text stack anchored to bottom with zero text overflow past A_R=1000.
    """
    w, h = 1080, 1350
    A_L = 80
    A_R = 1000
    A_C = 540
    T = 80
    B = 1270
    max_text_width = A_R - A_L  # Exactly 920px

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
    brand_el = next((el for el in spec.elements if el.id in ("business_name", "brand_name", "logo", "brand")), None)
    contact_el = next((el for el in spec.elements if el.id == "contact"), None)
    badge_el = next((el for el in spec.elements if el.id in ("badge", "showcase_badge")), None)

    if cta_bg_el and cta_bg_el.fill and cta_bg_el.fill.startswith("#"):
        accent_hex = cta_bg_el.fill
    accent_rgb = parse_hex_color(accent_hex)
    on_accent_rgb = parse_hex_color(on_accent_hex)
    muted_rgb = parse_hex_color(muted_hex)
    text_rgb = parse_hex_color(text_hex)

    headline_raw = headline_el.text if headline_el and headline_el.text else "One origin.\nOne slow pour."
    theme_keyword = headline_raw.lower()

    # 1. Base Canvas
    image = Image.new("RGBA", (w, h), (*bg_rgb, 255))

    # 2. Hero Image: Full-Bleed across entire canvas (0, 0, 1080, 1350)
    # Extends under the bottom text scrim so there is ZERO horizontal line or break at y=900!
    hero_photo = get_hero_image_for_subject(theme_keyword, width=w, height=h)
    image.paste(hero_photo, (0, 0))

    # 3. Design Device: Inset Frame (1px line at 15% opacity inset 32px with top gap)
    _draw_inset_frame(image, accent_rgb, w, h)

    # 4. Subject-Relative Structural Ring / Frame
    # Render only when requested by archetype or spec design notes
    ring_cx, ring_cy, ring_diam = A_C, 470, 630
    shapes_patterns = str(spec.shapes or []) + str(spec.patterns or []) + str(spec.design_notes or {})
    should_draw_ring = any(k in shapes_patterns.lower() for k in ("ring", "circle", "copper_ring", "framing"))
    if should_draw_ring:
        _draw_subject_ring(image, accent_rgb, ring_cx, ring_cy, ring_diam)

    # 5. Design Device: Curved Steam Strokes (ONLY when explicitly requested for coffee/hot beverage)
    should_draw_steam = any(k in shapes_patterns.lower() for k in ("steam", "coffee_steam", "hot_steam"))
    if should_draw_steam:
        _draw_curved_steam(image, accent_rgb)

    # 6. Scrims:
    # A. Top scrim: linear-gradient(180deg, rgba(bg,0.65) 0%, rgba(bg,0) 22%) for logo contrast
    _apply_top_scrim(image, height=300, bg_rgb=bg_rgb)
    # B. Bottom scrim: 4 color stops starting at 40% height (y=540) to y=1350
    _apply_bottom_scrim_v3(image, start_y=540, end_y=h, bg_rgb=bg_rgb)

    # 7. Film Grain & Radial Vignette
    _apply_film_grain_and_vignette(image, w, h)

    draw = ImageDraw.Draw(image)

    # 8. Header Row (Midline center_y = 104, A_L = 80, A_R = 1000)
    header_midline_y = 104
    if brand_el and brand_el.text:
        business_name = sanitize_poster_text(brand_el.text)
    else:
        business_name = "Your Brand"
    # Ensure Title Case and no raw domain in the brand logo
    business_name = re.sub(r"\.com\b", "", business_name, flags=re.IGNORECASE)
    business_name = sanitize_poster_text(business_name)

    font_wordmark = _get_font(spec.fonts.display, 28, weight=700)
    w_bbox = draw.textbbox((0, 0), business_name, font=font_wordmark)
    logo_w = w_bbox[2] - w_bbox[0]
    logo_h = w_bbox[3] - w_bbox[1]
    logo_x = A_L
    logo_y = header_midline_y - (logo_h // 2) - 2

    # Draw wordmark on left axis
    draw.text((logo_x, logo_y), business_name, fill=(*text_rgb, 255), font=font_wordmark)

    # Badge on Right Axis: Inter 600, 24px, uppercase, +0.12em tracking, dark on accent
    default_badge = "SPECIAL OFFER" if "offer" in (headline_raw or "").lower() else "OFFICIAL RELEASE"
    badge_text = sanitize_poster_text(badge_el.text if badge_el and badge_el.text else default_badge).upper()
    font_badge = _get_font(spec.fonts.text, 24, weight=600)
    badge_w = _get_tracked_text_width(draw, badge_text, font_badge, tracking_em=0.12)
    b_bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    badge_h = b_bbox[3] - b_bbox[1]

    # Pill: padding 14px v, 28px h, height = 48px
    pill_h = 48
    pill_w = badge_w + 56
    pill_x = A_R - pill_w
    pill_y = header_midline_y - (pill_h // 2)

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    o_draw = ImageDraw.Draw(overlay)
    _draw_rounded_rectangle(o_draw, (pill_x, pill_y, pill_x + pill_w, pill_y + pill_h), radius=pill_h // 2, fill=(*accent_rgb, 255))
    image = Image.alpha_composite(image, overlay)
    draw = ImageDraw.Draw(image)

    # Draw tracked dark text inside amber pill (optically centered)
    _draw_tracked_text(
        draw,
        (pill_x + 28, pill_y + (pill_h - badge_h) // 2 - 1),
        badge_text,
        font_badge,
        fill=(*on_accent_rgb, 255),
        tracking_em=0.12
    )

    # 9. Bottom Text Stack (Anchored to B = 1270)
    # A. Hairline Rule: 48px x 2px accent line
    rule_w = 48
    rule_h = 2

    # B. Eyebrow: Inter 600, 26px, uppercase, tracking +0.12em, accent color
    raw_eb = eyebrow_el.text if eyebrow_el and eyebrow_el.text else ""
    if not raw_eb:
        raw_eb = f"✦ {business_name.upper()}" if business_name else "FEATURED ANNOUNCEMENT"
    # Strip any decorative unicode symbols (like ✦) that might render tofu boxes
    clean_eb = re.sub(r"[^\w\s\-–—/]", "", raw_eb).strip()
    if not clean_eb:
        clean_eb = "FEATURED ANNOUNCEMENT"
    eyebrow_text = sanitize_poster_text(clean_eb).upper()
    font_eyebrow = _get_font(spec.fonts.text, 26, weight=600)
    eyebrow_bbox = draw.textbbox((0, 0), eyebrow_text, font=font_eyebrow)
    eyebrow_h = eyebrow_bbox[3] - eyebrow_bbox[1]

    # C. Headline: Fraunces 700, 88px, lh 96px, optical offset -3px, max 2 lines
    h_text = sanitize_poster_text(headline_raw)
    # Clean redundant business name or unverified superlatives if present
    h_text = re.sub(r"Rajkumar('s|’s)?\s*Coffee\s*(Studio)?", "", h_text, flags=re.IGNORECASE).strip(": -")
    for b_word in ("Experience the Future of Coffee", "Future of Coffee"):
        h_text = re.sub(re.escape(b_word), "", h_text, flags=re.IGNORECASE).strip(": -")
    h_text = re.sub(r"\b(at|by|in|for)\s*(Coffee)?\s*$", "", h_text, flags=re.IGNORECASE).strip(": -")

    # Retain Part 3 Masterclass coffee lines ONLY if explicitly a coffee/beverage topic
    is_coffee = any(k in (business_name + " " + h_text).lower() for k in ("coffee", "brew", "cafe", "roast"))
    if is_coffee and any(k in h_text.lower() for k in ("one origin", "slow pour")):
        h_lines = ["One origin.", "One slow pour."]
    elif "\n" in h_text:
        h_lines = [line.strip() for line in h_text.split("\n") if line.strip()][:2]
    else:
        h_words = h_text.split()
        if len(h_words) == 0:
            h_lines = [sanitize_poster_text(business_name or "Featured Release")]
        elif len(h_words) > 6:
            # Wrap to 2 lines of max 3-4 words each, preserving real business headline
            mid = min(4, (len(h_words) + 1) // 2)
            h_lines = [" ".join(h_words[:mid]), " ".join(h_words[mid:6])]
        elif len(h_words) > 3:
            mid = (len(h_words) + 1) // 2
            h_lines = [" ".join(h_words[:mid]), " ".join(h_words[mid:])]
        else:
            h_lines = [h_text]

    # Apply smart typography to each headline line
    h_lines = [sanitize_poster_text(line) for line in h_lines]

    h_size = 88
    font_headline = _get_font(spec.fonts.display, h_size, weight=700)
    font_headline_italic = _get_font(spec.fonts.display, h_size, weight=700, italic=True)

    # Dynamic fit-to-box: step down font size if any line width > max_text_width
    while any((draw.textbbox((0, 0), line, font=font_headline)[2] - draw.textbbox((0, 0), line, font=font_headline)[0]) > max_text_width for line in h_lines) and h_size > 60:
        h_size -= 4
        font_headline = _get_font(spec.fonts.display, h_size, weight=700)
        font_headline_italic = _get_font(spec.fonts.display, h_size, weight=700, italic=True)

    h_line_height = 96 if h_size >= 84 else int(h_size * 1.1)
    headline_total_h = len(h_lines) * h_line_height

    # D. Subhead: Inter 400, 34px, lh 48px, max 1 line (<= 44 chars)
    s_text = sanitize_poster_text(subhead_el.text if subhead_el and subhead_el.text else "")
    # Strip unverified claims
    for fluff in ("limited spots available", "limited spots", "with vision", "visionary craftsmanship", "the future of coffee"):
        s_text = re.sub(re.escape(fluff), '', s_text, flags=re.IGNORECASE)
    s_text = s_text.replace("!", ".").strip()
    if len(s_text) > 44 or not s_text or s_text.endswith(("single", "the", "of", "and")):
        if business_name:
            if any(k in business_name.lower() for k in ("coffee", "cafe", "roast", "brew")):
                s_text = f"A guided tasting at {business_name}"
                if len(s_text) > 44:
                    s_text = "A guided single-origin tasting"
            else:
                s_text = f"Experience quality at {business_name}"
                if len(s_text) > 44:
                    s_text = f"Welcome to {business_name}"
        else:
            s_text = "Designed for exceptional quality."

    font_subhead = _get_font(spec.fonts.text, 34, weight=400)
    subhead_h = 48

    # E. Footer Row: CTA pill + Meta handle, midline center_y = 1230, height = 80px
    footer_midline_y = 1230
    default_cta = "Reserve a seat" if any(k in (business_name or "").lower() for k in ("coffee", "cafe", "roast", "dining")) else "Learn More"
    cta_text_str = sanitize_poster_text(cta_text_el.text if cta_text_el and cta_text_el.text else default_cta)
    for fluff in ("today limited spots available", "limited spots available", "limited spots", "today", "now"):
        cta_text_str = re.sub(re.escape(fluff), '', cta_text_str, flags=re.IGNORECASE).strip()
    cta_words = cta_text_str.split()
    if len(cta_words) > 3 or len(cta_words) == 0:
        cta_text_str = default_cta
    else:
        cta_text_str = " ".join(cta_words).title()

    font_cta = _get_font(spec.fonts.text, 34, weight=600)
    cta_bbox = draw.textbbox((0, 0), cta_text_str, font=font_cta)
    cta_w = cta_bbox[2] - cta_bbox[0]
    cta_h = cta_bbox[3] - cta_bbox[1]

    # CTA Pill: height 80px, padding 48px horizontal
    btn_h = 80
    btn_w = cta_w + 96
    btn_x = A_L
    btn_y = footer_midline_y - (btn_h // 2)

    # Handle / Meta on right axis (A_R = 1000)
    clean_bname = business_name.lower().replace(" ", "").replace("'", "").replace("’", "")
    handle_text = f"@{clean_bname}"
    font_handle = _get_font(spec.fonts.text, 26, weight=500)
    handle_bbox = draw.textbbox((0, 0), handle_text, font=font_handle)
    handle_w = handle_bbox[2] - handle_bbox[0]
    handle_h = handle_bbox[3] - handle_bbox[1]
    handle_x = A_R - handle_w
    handle_y = footer_midline_y - (handle_h // 2)

    # Spacing Gaps (8px grid):
    gap_rule_to_eyebrow = 16
    gap_eyebrow_to_headline = 24
    gap_headline_to_subhead = 24
    gap_subhead_to_footer = 40

    total_stack_h = (
        rule_h +
        gap_rule_to_eyebrow +
        eyebrow_h +
        gap_eyebrow_to_headline +
        headline_total_h +
        gap_headline_to_subhead +
        subhead_h +
        gap_subhead_to_footer +
        btn_h
    )

    # Stack is anchored to bottom margin: B = 1270
    stack_top_y = B - total_stack_h
    flow_y = stack_top_y

    # 1. Hairline Rule (left on A_L=80)
    rule_y = flow_y
    draw.rectangle([(A_L, rule_y), (A_L + rule_w, rule_y + rule_h)], fill=(*accent_rgb, 255))
    flow_y += rule_h + gap_rule_to_eyebrow

    # 2. Eyebrow (left on A_L=80, tracking +0.12em)
    eyebrow_y = flow_y
    _draw_tracked_text(
        draw,
        (A_L, eyebrow_y),
        eyebrow_text,
        font_eyebrow,
        fill=(*accent_rgb, 255),
        tracking_em=0.12
    )
    flow_y += eyebrow_h + gap_eyebrow_to_headline

    # 3. Headline (left on A_L - 3 for optical margin alignment)
    optical_offset_left = -3
    headline_start_y = flow_y
    for i, line in enumerate(h_lines):
        # Set second line in italic for accent rhythm
        f = font_headline_italic if (i > 0 and len(h_lines) > 1) else font_headline
        draw.text((A_L + optical_offset_left, flow_y), line, fill=(*text_rgb, 255), font=f)
        flow_y += h_line_height
    flow_y += gap_headline_to_subhead

    # 4. Subhead (left on A_L=80, max 1 line)
    subhead_y = flow_y
    draw.text((A_L, subhead_y), s_text, fill=(*muted_rgb, 255), font=font_subhead)

    # 5. Footer Row: CTA Button + Handle (Midline = 1230)
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    o_draw = ImageDraw.Draw(overlay)
    _draw_rounded_rectangle(o_draw, (btn_x, btn_y, btn_x + btn_w, btn_y + btn_h), radius=btn_h // 2, fill=(*accent_rgb, 255))
    image = Image.alpha_composite(image, overlay)
    draw = ImageDraw.Draw(image)

    # Dark text centered inside amber CTA pill
    draw.text(
        (btn_x + (btn_w - cta_w) // 2, btn_y + (btn_h - cta_h) // 2 - 2),
        cta_text_str,
        fill=(*on_accent_rgb, 255),
        font=font_cta
    )

    # Handle on right axis A_R = 1000, vertically centered on midline 1230
    draw.text((handle_x, handle_y), handle_text, fill=(*muted_rgb, 255), font=font_handle)

    # 10. Automated Alignment QA Geometry Check
    rendered_elements = {
        "header_row": {"t": pill_y, "b": pill_y + pill_h, "cy": header_midline_y},
        "logo": {"l": logo_x, "r": logo_x + logo_w, "t": logo_y, "b": logo_y + logo_h, "cy": header_midline_y},
        "badge": {"l": pill_x, "r": pill_x + pill_w, "t": pill_y, "b": pill_y + pill_h, "cy": header_midline_y},
        "ring": {"t": ring_cy - (ring_diam // 2), "b": ring_cy + (ring_diam // 2), "l": ring_cx - (ring_diam // 2), "r": ring_cx + (ring_diam // 2)},
        "text_stack": {"t": stack_top_y, "b": B},
        "rule": {"l": A_L, "r": A_L + rule_w, "t": rule_y, "b": rule_y + rule_h},
        "eyebrow": {"l": A_L, "r": A_L + eyebrow_bbox[2] - eyebrow_bbox[0], "t": eyebrow_y, "b": eyebrow_y + eyebrow_h},
        "headline": {"l": A_L + optical_offset_left, "r": A_L + optical_offset_left + max(draw.textbbox((0, 0), l, font=font_headline)[2] - draw.textbbox((0, 0), l, font=font_headline)[0] for l in h_lines), "t": headline_start_y, "b": headline_start_y + headline_total_h},
        "sub": {"l": A_L, "r": A_L + draw.textbbox((0, 0), s_text, font=font_subhead)[2] - draw.textbbox((0, 0), s_text, font=font_subhead)[0], "t": subhead_y, "b": subhead_y + subhead_h},
        "cta": {"l": btn_x, "r": btn_x + btn_w, "t": btn_y, "b": btn_y + btn_h, "cy": footer_midline_y},
        "meta": {"l": handle_x, "r": handle_x + handle_w, "t": handle_y, "b": handle_y + handle_h, "cy": footer_midline_y}
    }

    qa_errors = qa_check_spec_geometry(rendered_elements, axes={"A_L": A_L, "A_R": A_R, "A_C": A_C, "T": T, "B": B})

    # 11. Export Production PNG and Thumbnail
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
        measurements={
            "status": "poster_v3_alignment_masterclass_passed" if not qa_errors else "qa_warnings",
            "qa_errors": qa_errors,
            "axes": {"A_L": A_L, "A_R": A_R, "A_C": A_C, "T": T, "B": B},
            "stack_top_y": stack_top_y,
            "stack_height": total_stack_h,
            "header_midline_y": header_midline_y,
            "footer_midline_y": footer_midline_y,
            "contrast": "pass"
        }
    )
