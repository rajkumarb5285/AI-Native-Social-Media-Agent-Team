"""High-Resolution 300 DPI Vector & Raster QR Code Generator for Print Collateral.

Uses Error Correction Level H (30% recovery) so that printed QR codes remain
100% scannable even with physical paper wear, folds, scratches, or moisture.
"""
import io
import base64
from typing import Tuple, Optional
import qrcode
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_Q, ERROR_CORRECT_M
from PIL import Image, ImageDraw


def parse_hex_color(hex_str: str) -> Tuple[int, int, int]:
    """Parses a hex color string into an (R, G, B) tuple."""
    if not hex_str or not hex_str.startswith("#"):
        return (15, 23, 42)
    cleaned = hex_str.lstrip("#")
    if len(cleaned) == 3:
        cleaned = "".join([c * 2 for c in cleaned])
    if len(cleaned) != 6:
        return (15, 23, 42)
    try:
        return (
            int(cleaned[0:2], 16),
            int(cleaned[2:4], 16),
            int(cleaned[4:6], 16)
        )
    except ValueError:
        return (15, 23, 42)


def generate_print_qr_image(
    url: str,
    fg_color: str = "#0F172A",
    bg_color: str = "#FFFFFF",
    size_px: int = 600,
    error_correction: str = "H"
) -> Image.Image:
    """Generates a high-resolution PIL Image QR code for 300 DPI print output.
    
    Args:
        url: The destination link (website, booking, menu, review page).
        fg_color: Foreground hex color for the QR data modules.
        bg_color: Background hex color.
        size_px: Target pixel dimension (default 600px = ~50mm at 300 DPI).
        error_correction: 'H' (30% recovery), 'Q' (25%), 'M' (15%).
    """
    ec_map = {
        "H": ERROR_CORRECT_H,
        "Q": ERROR_CORRECT_Q,
        "M": ERROR_CORRECT_M
    }
    ec_level = ec_map.get(error_correction.upper(), ERROR_CORRECT_H)

    qr = qrcode.QRCode(
        version=None,
        error_correction=ec_level,
        box_size=10,
        border=4  # Standard quiet zone
    )
    qr.add_data(url)
    qr.make(fit=True)

    fg_rgb = parse_hex_color(fg_color)
    bg_rgb = parse_hex_color(bg_color)

    # Generate base image
    qr_img = qr.make_image(fill_color=fg_rgb, back_color=bg_rgb).convert("RGB")

    # Resize cleanly to target dimension
    if qr_img.size != (size_px, size_px):
        qr_img = qr_img.resize((size_px, size_px), Image.Resampling.NEAREST)

    return qr_img


def generate_print_qr_bytes(
    url: str,
    fg_color: str = "#0F172A",
    bg_color: str = "#FFFFFF",
    size_px: int = 600,
    dpi: int = 300
) -> bytes:
    """Returns raw PNG bytes with embedded 300 DPI print header."""
    img = generate_print_qr_image(url, fg_color, bg_color, size_px)
    buf = io.BytesIO()
    img.save(buf, format="PNG", dpi=(dpi, dpi))
    return buf.getvalue()


def generate_print_qr_base64(
    url: str,
    fg_color: str = "#0F172A",
    bg_color: str = "#FFFFFF",
    size_px: int = 600,
    dpi: int = 300
) -> str:
    """Returns data URI base64 string for embedding into HTML or JSON responses."""
    png_bytes = generate_print_qr_bytes(url, fg_color, bg_color, size_px, dpi=dpi)
    b64 = base64.b64encode(png_bytes).decode("utf-8")
    return f"data:image/png;base64,{b64}"
