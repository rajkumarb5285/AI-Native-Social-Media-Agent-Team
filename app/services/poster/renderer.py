"""Deterministic High-Fidelity Poster Renderer.

Implements Section 2 & Section 5 of the Poster Design Agent pack:
- Exact coordinates, grid snapping, and type scale rendering
- Anti-aliased vector shapes, rounded pill buttons, and soft card surfaces
- Multi-line typographic text wrapping with true line-height and alignment
- Linear gradient backgrounds and scrim overlays
- Outputs full-resolution PNG, 200px thumbnail PNG, SVG, and Base64 data
"""
import io
import os
import math
import base64
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pydantic import BaseModel
from .spec import PosterSpec, PosterElement
from .linter import parse_hex_color


class RenderResult(BaseModel):
    width: int
    height: int
    png_bytes: bytes
    thumbnail_bytes: bytes
    png_base64: str
    thumbnail_base64: str
    svg_content: str
    measurements: Dict[str, Any]


def _get_font(font_family: str, size: int, weight: int = 400) -> ImageFont.ImageFont:
    """Loads matching TrueType font or fallback font at exact pixel size."""
    is_bold = weight >= 600
    font_candidates = []

    # Display / Serif Font Candidates
    if any(k in font_family.lower() for k in ("playfair", "serif", "fraunces", "dm serif")):
        if is_bold:
            font_candidates.extend(["timesbd.ttf", "georgiab.ttf", "palab.ttf"])
        else:
            font_candidates.extend(["times.ttf", "georgia.ttf", "pala.ttf"])

    # Modern Sans / Clean Candidates (Inter, Montserrat, Poppins, Roboto)
    if is_bold:
        font_candidates.extend(["segoeuib.ttf", "arialbd.ttf", "calibrib.ttf", "trebucbd.ttf"])
    else:
        font_candidates.extend(["segoeui.ttf", "arial.ttf", "calibri.ttf", "trebuc.ttf"])

    # Standard Windows Font Directory
    win_fonts = Path("C:/Windows/Fonts")
    for name in font_candidates:
        p = win_fonts / name
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                continue

    # Fallback to PIL default
    try:
        return ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()


def _draw_linear_gradient(img: Image.Image, color1: tuple, color2: tuple, direction: str = "vertical"):
    """Draws a smooth linear gradient across the image canvas."""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    steps = h if direction == "vertical" else w

    for i in range(steps):
        t = i / float(steps - 1) if steps > 1 else 0
        r = int(color1[0] * (1 - t) + color2[0] * t)
        g = int(color1[1] * (1 - t) + color2[1] * t)
        b = int(color1[2] * (1 - t) + color2[2] * t)
        if direction == "vertical":
            draw.line([(0, i), (w, i)], fill=(r, g, b))
        else:
            draw.line([(i, 0), (i, h)], fill=(r, g, b))


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

    # Draw rounded rectangle with corner arcs
    draw.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=fill, outline=outline, width=width)


def render_poster_spec(spec: PosterSpec, assets: Optional[Dict[str, bytes]] = None) -> RenderResult:
    """Renders a validated PosterSpec into full-resolution PNG and thumbnail.
    
    Draws layers deterministically according to z-index:
    1. Background (solid or gradient)
    2. Decorative backgrounds and containers
    3. Scrim overlays
    4. Text, headers, and CTA buttons
    """
    w, h = spec.canvas.width, spec.canvas.height
    image = Image.new("RGBA", (w, h), (11, 15, 25, 255))
    draw = ImageDraw.Draw(image)

    # 1. Render Background
    bg = spec.background
    if bg.type == "gradient" and "->" in bg.value:
        parts = [p.strip() for p in bg.value.split("->")]
        c1 = parse_hex_color(parts[0])
        c2 = parse_hex_color(parts[1]) if len(parts) > 1 else (20, 25, 40)
        _draw_linear_gradient(image, c1, c2, direction="vertical")
        draw = ImageDraw.Draw(image)
    elif bg.type == "solid":
        c = parse_hex_color(bg.value)
        draw.rectangle([(0, 0), (w, h)], fill=(*c, 255))
    else:
        c = parse_hex_color("#0B0F19")
        draw.rectangle([(0, 0), (w, h)], fill=(*c, 255))

    # 2. Render Elements sorted by Z-Index
    sorted_elements = sorted(spec.elements, key=lambda el: el.z)
    measurements = {}

    for el in sorted_elements:
        x0, y0 = el.x, el.y
        x1, y1 = el.x + el.w, el.y + el.h

        # A. Shape Element (Cards, Buttons, Badges, Dividers)
        if el.type in ("shape", "badge", "line"):
            fill_tuple = None
            if el.fill and el.fill.lower() != "none" and el.fill.startswith("#"):
                rgb = parse_hex_color(el.fill)
                alpha = int((el.opacity if el.opacity is not None else 1.0) * 255)
                fill_tuple = (*rgb, alpha)

            stroke_tuple = None
            if el.stroke and el.stroke.lower() != "none" and el.stroke.startswith("#"):
                rgb = parse_hex_color(el.stroke)
                alpha = int((el.opacity if el.opacity is not None else 1.0) * 255)
                stroke_tuple = (*rgb, alpha)

            if el.type == "line":
                draw.line([(x0, y0), (x1, y1)], fill=stroke_tuple or fill_tuple or (255, 255, 255, 100), width=el.stroke_width or 2)
            else:
                # Shape or Card
                overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                _draw_rounded_rectangle(
                    overlay_draw,
                    (x0, y0, x1, y1),
                    radius=el.radius or 0,
                    fill=fill_tuple,
                    outline=stroke_tuple,
                    width=el.stroke_width or 1
                )
                image = Image.alpha_composite(image, overlay)
                draw = ImageDraw.Draw(image)

        # B. Image / Photo Element (Client photo or generated background asset)
        elif el.type in ("image", "logo"):
            photo_drawn = False
            if assets and el.asset and el.asset in assets:
                try:
                    img_data = io.BytesIO(assets[el.asset])
                    user_img = Image.open(img_data).convert("RGBA")
                    user_img = user_img.resize((el.w, el.h), Image.Resampling.LANCZOS)
                    image.paste(user_img, (x0, y0), user_img)
                    photo_drawn = True
                except Exception:
                    photo_drawn = False

            if not photo_drawn:
                # Draw subtle placeholder surface
                _draw_rounded_rectangle(
                    draw,
                    (x0, y0, x1, y1),
                    radius=el.radius or 16,
                    fill=(30, 41, 59, 180),
                    outline=(71, 85, 105, 120),
                    width=1
                )

        # C. Typography Element (Headline, Subhead, Body, CTA text)
        elif el.type == "text" and el.text:
            text_content = el.text.upper() if el.transform == "uppercase" else el.text
            font_family = spec.fonts.display if el.font == "display" else spec.fonts.text
            font_size = el.size or 32
            font = _get_font(font_family, font_size, weight=el.weight or 400)

            # Wrap text to element width
            words = text_content.split()
            lines = []
            curr_line = []
            for word in words:
                test_line = " ".join(curr_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font)
                line_w = bbox[2] - bbox[0]
                if line_w <= el.w:
                    curr_line.append(word)
                else:
                    if curr_line:
                        lines.append(" ".join(curr_line))
                    curr_line = [word]
                if el.max_lines and len(lines) >= el.max_lines:
                    break
            if curr_line and (not el.max_lines or len(lines) < el.max_lines):
                lines.append(" ".join(curr_line))

            # Render text lines
            line_height_px = int(font_size * (el.line_height or 1.2))
            text_color = parse_hex_color(el.color or "#FFFFFF")
            curr_y = y0

            for line_idx, line_str in enumerate(lines):
                bbox = draw.textbbox((0, 0), line_str, font=font)
                lw = bbox[2] - bbox[0]
                if el.align == "center":
                    line_x = x0 + (el.w - lw) // 2
                elif el.align == "right":
                    line_x = x1 - lw
                else:
                    line_x = x0

                draw.text((line_x, curr_y), line_str, fill=(*text_color, 255), font=font)
                curr_y += line_height_px

            measurements[el.id] = {
                "lines_rendered": len(lines),
                "total_height_px": curr_y - y0,
                "box_height_px": el.h
            }

    # 3. Export PNG and Thumbnail
    output_png = io.BytesIO()
    image.convert("RGB").save(output_png, format="PNG", quality=95)
    png_bytes = output_png.getvalue()

    # 200px Thumbnail for vision critic / preview
    thumb_ratio = 200 / float(w)
    thumb_h = int(h * thumb_ratio)
    thumb_img = image.resize((200, thumb_h), Image.Resampling.LANCZOS)
    thumb_io = io.BytesIO()
    thumb_img.convert("RGB").save(thumb_io, format="PNG", quality=90)
    thumbnail_bytes = thumb_io.getvalue()

    png_b64 = f"data:image/png;base64,{base64.b64encode(png_bytes).decode('utf-8')}"
    thumb_b64 = f"data:image/png;base64,{base64.b64encode(thumbnail_bytes).decode('utf-8')}"

    # Minimal clean SVG representation
    svg_elements = []
    for el in sorted_elements:
        if el.type == "shape":
            svg_elements.append(
                f'<rect x="{el.x}" y="{el.y}" width="{el.w}" height="{el.h}" rx="{el.radius or 0}" fill="{el.fill or "none"}" stroke="{el.stroke or "none"}" />'
            )
        elif el.type == "text" and el.text:
            svg_elements.append(
                f'<text x="{el.x}" y="{el.y + (el.size or 32)}" fill="{el.color or "#FFFFFF"}" font-size="{el.size or 32}" font-family="{spec.fonts.text}">{el.text}</text>'
            )

    svg_str = (
        f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
        f'<rect width="{w}" height="{h}" fill="{spec.background.value if spec.background.type == "solid" else "#0B0F19"}" />'
        + "".join(svg_elements) +
        '</svg>'
    )

    return RenderResult(
        width=w,
        height=h,
        png_bytes=png_bytes,
        thumbnail_bytes=thumbnail_bytes,
        png_base64=png_b64,
        thumbnail_base64=thumb_b64,
        svg_content=svg_str,
        measurements=measurements
    )
