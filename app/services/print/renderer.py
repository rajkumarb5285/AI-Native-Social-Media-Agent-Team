"""Production Print Renderer for Flyers, Leaflets, and Tri-Fold Brochures.

Generates:
1. Commercial Print PDF with 300 DPI imagery, 3mm bleed, and crop/fold marks via ReportLab.
2. High-Resolution 300 DPI PNG with embedded pHYs DPI header for raster printing.
3. Web preview image and thumbnail for instant Studio UI display.
"""
import io
import math
import base64
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from PIL import Image, ImageDraw, ImageFont

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas

from app.services.print.spec import (
    PRINT_FORMATS, PrintDimensions, PrintCollateralSpec, PrintOfferingItem,
    BLEED_MM, MM_TO_PX_300DPI, DPI
)
from app.services.print.qr_generator import generate_print_qr_image, parse_hex_color


class PrintRenderResult(BaseModel):
    """Complete output package for print collateral."""
    pdf_bytes: bytes
    png_bytes: bytes
    thumbnail_bytes: bytes
    pdf_base64: str
    png_base64: str
    thumbnail_base64: str
    format: str
    trim_width_mm: float
    trim_height_mm: float
    bleed_mm: float
    total_width_px: int
    total_height_px: int
    dpi: int = 300
    page_count: int = 1


def draw_crop_marks(
    pdf_c: pdf_canvas.Canvas,
    trim_w_mm: float,
    trim_h_mm: float,
    bleed_mm: float = 3.0,
    mark_len_mm: float = 5.0,
    offset_mm: float = 1.0
):
    """Draws standard commercial printer crop marks outside the trim box."""
    pdf_c.saveState()
    pdf_c.setLineWidth(0.3)
    pdf_c.setStrokeColor(colors.black)

    # Coordinates in points
    b = bleed_mm * mm
    w = trim_w_mm * mm
    h = trim_h_mm * mm
    m_len = mark_len_mm * mm
    off = offset_mm * mm

    # Origin is at (0, 0) of the bleed box (bottom-left)
    # The trim box origin is at (b, b), top-right is at (b + w, b + h)
    x1, y1 = b, b
    x2, y2 = b + w, b + h

    # Top-Left marks
    pdf_c.line(x1 - off, y2, x1 - off - m_len, y2)  # Horizontal
    pdf_c.line(x1, y2 + off, x1, y2 + off + m_len)  # Vertical

    # Top-Right marks
    pdf_c.line(x2 + off, y2, x2 + off + m_len, y2)  # Horizontal
    pdf_c.line(x2, y2 + off, x2, y2 + off + m_len)  # Vertical

    # Bottom-Left marks
    pdf_c.line(x1 - off, y1, x1 - off - m_len, y1)  # Horizontal
    pdf_c.line(x1, y1 - off, x1, y1 - off - m_len)  # Vertical

    # Bottom-Right marks
    pdf_c.line(x2 + off, y1, x2 + off + m_len, y1)  # Horizontal
    pdf_c.line(x2, y1 - off, x2, y1 - off - m_len)  # Vertical

    pdf_c.restoreState()


def draw_fold_marks(
    pdf_c: pdf_canvas.Canvas,
    fold_x_positions_mm: List[float],
    total_h_mm: float,
    mark_len_mm: float = 4.0
):
    """Draws dashed fold/score marks in the top and bottom bleed areas."""
    pdf_c.saveState()
    pdf_c.setLineWidth(0.3)
    pdf_c.setStrokeColor(colors.gray)
    pdf_c.setDash(2, 2)

    total_h = total_h_mm * mm
    m_len = mark_len_mm * mm

    for fx_mm in fold_x_positions_mm:
        x = fx_mm * mm
        # Top bleed fold mark
        pdf_c.line(x, total_h, x, total_h - m_len)
        # Bottom bleed fold mark
        pdf_c.line(x, 0, x, m_len)

    pdf_c.restoreState()


def render_print_pdf(spec: PrintCollateralSpec) -> bytes:
    """Renders vector-accurate, print-ready PDF with ReportLab."""
    dims = PRINT_FORMATS.get(spec.format, PRINT_FORMATS["a4_flyer"])
    
    total_w_pt = dims.total_width_mm * mm
    total_h_pt = dims.total_height_mm * mm

    buf = io.BytesIO()
    pdf_c = pdf_canvas.Canvas(buf, pagesize=(total_w_pt, total_h_pt))
    pdf_c.setTitle(f"{spec.business_name} - {dims.name}")

    # Generate QR Code image if configured
    qr_img = None
    if spec.qr_code and spec.qr_code.url:
        qr_img = generate_print_qr_image(
            url=spec.qr_code.url,
            fg_color=spec.qr_code.fg_color,
            bg_color=spec.qr_code.bg_color,
            size_px=500,
            error_correction=spec.qr_code.error_correction
        )

    # -------------------------------------------------------------
    # Format 1: A4 Flyer or A5 Leaflet (Single Page / Double Page)
    # -------------------------------------------------------------
    if spec.format in ("a4_flyer", "a5_leaflet"):
        b = dims.bleed_mm * mm
        trim_w = dims.trim_width_mm * mm
        trim_h = dims.trim_height_mm * mm

        # Background fill over entire bleed box
        pdf_c.setFillColor(colors.HexColor(spec.bg_color))
        pdf_c.rect(0, 0, total_w_pt, total_h_pt, fill=True, stroke=False)

        # Header Hero Bar
        header_h = trim_h * 0.28
        header_y = b + trim_h - header_h
        pdf_c.setFillColor(colors.HexColor(spec.primary_color))
        pdf_c.rect(0, header_y, total_w_pt, header_h + b, fill=True, stroke=False)

        # Business Tagline / Eyebrow
        pdf_c.setFillColor(colors.HexColor(spec.accent_color))
        pdf_c.setFont("Helvetica-Bold", 10 if spec.format == "a5_leaflet" else 13)
        eyebrow_text = (spec.tagline or f"OFFICIAL • {spec.business_name.upper()}").upper()
        pdf_c.drawString(b + (12 * mm), b + trim_h - (16 * mm), eyebrow_text)

        # Headline
        pdf_c.setFillColor(colors.white)
        pdf_c.setFont("Helvetica-Bold", 20 if spec.format == "a5_leaflet" else 28)
        headline_lines = spec.headline.split("\n") if "\n" in spec.headline else [spec.headline[:40]]
        for i, line in enumerate(headline_lines[:2]):
            pdf_c.drawString(b + (12 * mm), b + trim_h - (28 * mm) - (i * 10 * mm), line)

        # Subhead
        if spec.subhead:
            pdf_c.setFillColor(colors.HexColor("#CBD5E1"))
            pdf_c.setFont("Helvetica", 10 if spec.format == "a5_leaflet" else 13)
            pdf_c.drawString(b + (12 * mm), b + trim_h - (50 * mm), spec.subhead[:80])

        # Offerings / Services Section
        start_y = header_y - (14 * mm)
        pdf_c.setFillColor(colors.HexColor(spec.primary_color))
        pdf_c.setFont("Helvetica-Bold", 12 if spec.format == "a5_leaflet" else 16)
        pdf_c.drawString(b + (12 * mm), start_y, "OUR SERVICES & SPECIALTIES")

        # Decorative hairline accent
        pdf_c.setStrokeColor(colors.HexColor(spec.accent_color))
        pdf_c.setLineWidth(1.5)
        pdf_c.line(b + (12 * mm), start_y - (2 * mm), b + (36 * mm), start_y - (2 * mm))

        # Render Offerings Items
        item_y = start_y - (12 * mm)
        spacing = 18 * mm if spec.format == "a4_flyer" else 14 * mm
        items = spec.offerings if spec.offerings else [
            PrintOfferingItem(name="Premium Service Package", price="$149", description="Full end-to-end bespoke solution.", tag="FEATURED"),
            PrintOfferingItem(name="Standard Signature Offering", price="$89", description="Tailored experience with guarantee.", tag="POPULAR"),
            PrintOfferingItem(name="Essential Consultation", price="$49", description="Direct expert evaluation and session.", tag=None),
        ]

        for item in items[:4]:
            # Item card background
            card_h = spacing - (3 * mm)
            pdf_c.setFillColor(colors.HexColor("#F8FAFC"))
            pdf_c.roundRect(b + (12 * mm), item_y - card_h + (3 * mm), trim_w - (24 * mm), card_h, 3 * mm, fill=True, stroke=False)

            # Item Name
            pdf_c.setFillColor(colors.HexColor("#0F172A"))
            pdf_c.setFont("Helvetica-Bold", 11 if spec.format == "a5_leaflet" else 13)
            pdf_c.drawString(b + (16 * mm), item_y - (4 * mm), item.name)

            # Price
            if item.price:
                pdf_c.setFillColor(colors.HexColor(spec.primary_color))
                pdf_c.setFont("Helvetica-Bold", 12 if spec.format == "a5_leaflet" else 15)
                pdf_c.drawRightString(b + trim_w - (16 * mm), item_y - (4 * mm), str(item.price))

            # Description
            if item.description:
                pdf_c.setFillColor(colors.HexColor("#64748B"))
                pdf_c.setFont("Helvetica", 8 if spec.format == "a5_leaflet" else 10)
                pdf_c.drawString(b + (16 * mm), item_y - (9 * mm), item.description[:75])

            item_y -= spacing

        # Footer Contact Bar & QR Code
        footer_h = 42 * mm if spec.format == "a4_flyer" else 36 * mm
        pdf_c.setFillColor(colors.HexColor("#0F172A"))
        pdf_c.rect(0, 0, total_w_pt, b + footer_h, fill=True, stroke=False)

        # Business Name in Footer
        pdf_c.setFillColor(colors.white)
        pdf_c.setFont("Helvetica-Bold", 12 if spec.format == "a5_leaflet" else 16)
        pdf_c.drawString(b + (12 * mm), b + footer_h - (12 * mm), spec.business_name)

        # Contact Info
        pdf_c.setFillColor(colors.HexColor("#94A3B8"))
        pdf_c.setFont("Helvetica", 8 if spec.format == "a5_leaflet" else 10)
        contact_str = " • ".join(filter(None, [spec.contact_phone, spec.contact_email, spec.website_url]))
        if contact_str:
            pdf_c.drawString(b + (12 * mm), b + footer_h - (20 * mm), contact_str[:60])
        if spec.contact_address:
            pdf_c.drawString(b + (12 * mm), b + footer_h - (27 * mm), spec.contact_address[:65])

        # Embed QR Code on the right
        if qr_img:
            qr_size = 26 * mm if spec.format == "a5_leaflet" else 30 * mm
            qr_x = b + trim_w - qr_size - (12 * mm)
            qr_y = b + (footer_h - qr_size) / 2.0
            
            # White card for QR code
            pdf_c.setFillColor(colors.white)
            pdf_c.roundRect(qr_x - (2 * mm), qr_y - (2 * mm), qr_size + (4 * mm), qr_size + (4 * mm), 2 * mm, fill=True, stroke=False)

            # Draw QR image directly
            from reportlab.lib.utils import ImageReader
            pdf_c.drawImage(ImageReader(qr_img), qr_x, qr_y, width=qr_size, height=qr_size)

        # Draw Crop Marks
        if spec.show_crop_marks:
            draw_crop_marks(pdf_c, dims.trim_width_mm, dims.trim_height_mm, dims.bleed_mm)

        pdf_c.showPage()

    # -------------------------------------------------------------
    # Format 2: Tri-Fold Brochure (A4 6-Panel: Outside & Inside)
    # -------------------------------------------------------------
    elif spec.format == "trifold_brochure":
        b = dims.bleed_mm * mm
        trim_w = dims.trim_width_mm * mm
        trim_h = dims.trim_height_mm * mm
        panel_w = trim_w / 3.0  # 99mm per panel (or 97, 100, 100)

        # --- Page 1: Outside (Inside Flap, Back Cover, Front Cover) ---
        pdf_c.setFillColor(colors.HexColor(spec.bg_color))
        pdf_c.rect(0, 0, total_w_pt, total_h_pt, fill=True, stroke=False)

        # Panel 3 (Right): Front Cover
        fc_x = b + (2 * panel_w)
        pdf_c.setFillColor(colors.HexColor(spec.primary_color))
        pdf_c.rect(fc_x, 0, panel_w + b, total_h_pt, fill=True, stroke=False)

        pdf_c.setFillColor(colors.HexColor(spec.accent_color))
        pdf_c.setFont("Helvetica-Bold", 11)
        pdf_c.drawString(fc_x + (10 * mm), b + trim_h - (24 * mm), (spec.tagline or "EXCLUSIVE OVERVIEW").upper())

        pdf_c.setFillColor(colors.white)
        pdf_c.setFont("Helvetica-Bold", 24)
        pdf_c.drawString(fc_x + (10 * mm), b + trim_h - (40 * mm), spec.business_name[:24])

        pdf_c.setFont("Helvetica", 12)
        pdf_c.setFillColor(colors.HexColor("#E2E8F0"))
        pdf_c.drawString(fc_x + (10 * mm), b + trim_h - (54 * mm), spec.headline[:35])

        # Panel 2 (Center): Back Cover (Contact & QR Code)
        bc_x = b + panel_w
        pdf_c.setFillColor(colors.HexColor("#0F172A"))
        pdf_c.setFont("Helvetica-Bold", 14)
        pdf_c.drawString(bc_x + (10 * mm), b + trim_h - (24 * mm), "CONTACT & LOCATION")

        pdf_c.setFillColor(colors.HexColor("#64748B"))
        pdf_c.setFont("Helvetica", 10)
        if spec.contact_phone:
            pdf_c.drawString(bc_x + (10 * mm), b + trim_h - (36 * mm), f"Tel: {spec.contact_phone}")
        if spec.contact_email:
            pdf_c.drawString(bc_x + (10 * mm), b + trim_h - (44 * mm), f"Email: {spec.contact_email}")
        if spec.contact_address:
            pdf_c.drawString(bc_x + (10 * mm), b + trim_h - (52 * mm), f"Address: {spec.contact_address}")

        # Embed QR Code on Back Cover
        if qr_img:
            qr_size = 32 * mm
            qr_x = bc_x + (panel_w - qr_size) / 2.0
            qr_y = b + (30 * mm)
            from reportlab.lib.utils import ImageReader
            pdf_c.drawImage(ImageReader(qr_img), qr_x, qr_y, width=qr_size, height=qr_size)
            pdf_c.setFillColor(colors.HexColor("#0F172A"))
            pdf_c.setFont("Helvetica-Bold", 9)
            pdf_c.drawCentredString(bc_x + (panel_w / 2.0), qr_y - (6 * mm), "SCAN TO CONNECT")

        # Panel 1 (Left): Inside Flap
        flap_x = b
        pdf_c.setFillColor(colors.HexColor("#0F172A"))
        pdf_c.setFont("Helvetica-Bold", 14)
        pdf_c.drawString(flap_x + (10 * mm), b + trim_h - (24 * mm), "ABOUT OUR MISSION")
        pdf_c.setFillColor(colors.HexColor("#475569"))
        pdf_c.setFont("Helvetica", 9)
        story_lines = [
            f"At {spec.business_name}, we are dedicated",
            "to exceptional standards of craft, precision,",
            "and client service.",
            "",
            "Experience tailored excellence crafted",
            "specifically for your needs."
        ]
        for i, line in enumerate(story_lines):
            pdf_c.drawString(flap_x + (10 * mm), b + trim_h - (36 * mm) - (i * 5 * mm), line)

        # Crop & Fold Marks on Page 1
        if spec.show_crop_marks:
            draw_crop_marks(pdf_c, dims.trim_width_mm, dims.trim_height_mm, dims.bleed_mm)
        if spec.show_fold_marks:
            draw_fold_marks(pdf_c, [dims.bleed_mm + 97.0, dims.bleed_mm + 197.0], dims.total_height_mm)

        pdf_c.showPage()

        # --- Page 2: Inside (3 Content Panels) ---
        pdf_c.setFillColor(colors.HexColor("#F8FAFC"))
        pdf_c.rect(0, 0, total_w_pt, total_h_pt, fill=True, stroke=False)

        # Inside Header across all 3 panels
        pdf_c.setFillColor(colors.HexColor(spec.primary_color))
        pdf_c.rect(0, b + trim_h - (24 * mm), total_w_pt, (24 * mm) + b, fill=True, stroke=False)
        pdf_c.setFillColor(colors.white)
        pdf_c.setFont("Helvetica-Bold", 16)
        pdf_c.drawCentredString(total_w_pt / 2.0, b + trim_h - (14 * mm), f"{spec.business_name.upper()} • FULL SERVICES DIRECTORY")

        # Render offerings across the 3 inside panels
        for p_idx in range(3):
            p_x = b + (p_idx * panel_w)
            pdf_c.setFillColor(colors.HexColor("#0F172A"))
            pdf_c.setFont("Helvetica-Bold", 12)
            panel_titles = ["01. SIGNATURE", "02. SPECIALTIES", "03. GUARANTEE"]
            pdf_c.drawString(p_x + (8 * mm), b + trim_h - (36 * mm), panel_titles[p_idx])

            # Content inside panel
            pdf_c.setFillColor(colors.HexColor("#334155"))
            pdf_c.setFont("Helvetica", 9)
            if p_idx < len(spec.offerings):
                offering = spec.offerings[p_idx]
                pdf_c.drawString(p_x + (8 * mm), b + trim_h - (46 * mm), f"• {offering.name}")
                if offering.price:
                    pdf_c.setFont("Helvetica-Bold", 10)
                    pdf_c.drawString(p_x + (8 * mm), b + trim_h - (53 * mm), f"Starting at {offering.price}")
                    pdf_c.setFont("Helvetica", 9)
                if offering.description:
                    pdf_c.drawString(p_x + (8 * mm), b + trim_h - (60 * mm), offering.description[:40])
            else:
                pdf_c.drawString(p_x + (8 * mm), b + trim_h - (46 * mm), "• Tailored Consultation")
                pdf_c.drawString(p_x + (8 * mm), b + trim_h - (54 * mm), "• Certified Quality Assurance")

        if spec.show_crop_marks:
            draw_crop_marks(pdf_c, dims.trim_width_mm, dims.trim_height_mm, dims.bleed_mm)
        if spec.show_fold_marks:
            draw_fold_marks(pdf_c, [dims.bleed_mm + 100.0, dims.bleed_mm + 200.0], dims.total_height_mm)

        pdf_c.showPage()

    pdf_c.save()
    return buf.getvalue()


def render_print_png_and_thumbnail(
    spec: PrintCollateralSpec
) -> Tuple[bytes, bytes, str, str]:
    """Renders high-resolution 300 DPI PNG and lightweight preview thumbnail."""
    dims = PRINT_FORMATS.get(spec.format, PRINT_FORMATS["a4_flyer"])
    
    # 300 DPI pixel dimensions
    w_px = dims.total_width_px
    h_px = dims.total_height_px
    b_px = dims.bleed_px

    img = Image.new("RGB", (w_px, h_px), parse_hex_color(spec.bg_color))
    draw = ImageDraw.Draw(img)

    # 1. Header Hero Bar
    header_h = int(h_px * 0.28)
    primary_rgb = parse_hex_color(spec.primary_color)
    accent_rgb = parse_hex_color(spec.accent_color)
    draw.rectangle([(0, 0), (w_px, header_h)], fill=primary_rgb)

    # Typography
    font_title_size = int(round(w_px * 0.042))
    font_sub_size = int(round(w_px * 0.020))
    font_body_size = int(round(w_px * 0.016))

    # Basic system fonts for PIL raster output
    font_headline = ImageFont.load_default()
    font_subhead = ImageFont.load_default()
    font_body = ImageFont.load_default()

    draw.text((b_px + 80, b_px + 80), (spec.tagline or "EXCLUSIVE OVERVIEW").upper(), fill=accent_rgb, font=font_subhead)
    draw.text((b_px + 80, b_px + 160), spec.headline[:50], fill=(255, 255, 255), font=font_headline)
    if spec.subhead:
        draw.text((b_px + 80, b_px + 260), spec.subhead[:80], fill=(203, 213, 225), font=font_subhead)

    # 2. Offerings / Services Cards
    card_start_y = header_h + 120
    card_spacing = int(h_px * 0.10)
    items = spec.offerings if spec.offerings else [
        PrintOfferingItem(name="Premium Service Package", price="$149", description="Full end-to-end bespoke solution."),
        PrintOfferingItem(name="Standard Signature Offering", price="$89", description="Tailored experience with guarantee."),
        PrintOfferingItem(name="Essential Consultation", price="$49", description="Direct expert evaluation and session.")
    ]

    for i, item in enumerate(items[:3]):
        cy = card_start_y + (i * card_spacing)
        draw.rectangle([(b_px + 80, cy), (w_px - b_px - 80, cy + card_spacing - 40)], fill=(248, 250, 252))
        draw.text((b_px + 120, cy + 30), item.name, fill=(15, 23, 42), font=font_subhead)
        if item.price:
            draw.text((w_px - b_px - 260, cy + 30), str(item.price), fill=primary_rgb, font=font_subhead)

    # 3. Footer Bar & QR code
    footer_h = int(h_px * 0.16)
    draw.rectangle([(0, h_px - footer_h), (w_px, h_px)], fill=(15, 23, 42))
    draw.text((b_px + 80, h_px - footer_h + 60), spec.business_name, fill=(255, 255, 255), font=font_subhead)

    contact_str = " • ".join(filter(None, [spec.contact_phone, spec.contact_email, spec.website_url]))
    if contact_str:
        draw.text((b_px + 80, h_px - footer_h + 140), contact_str[:60], fill=(148, 163, 184), font=font_body)

    # Paste QR Code if provided
    if spec.qr_code and spec.qr_code.url:
        qr_size = int(round(w_px * 0.14))
        qr_img = generate_print_qr_image(spec.qr_code.url, fg_color=spec.qr_code.fg_color, bg_color=spec.qr_code.bg_color, size_px=qr_size)
        qr_x = w_px - b_px - qr_size - 80
        qr_y = h_px - footer_h + int((footer_h - qr_size) / 2.0)
        img.paste(qr_img, (qr_x, qr_y))

    # 4. Draw Crop Marks on Raster Image
    if spec.show_crop_marks:
        c_len = int(round(5.0 * MM_TO_PX_300DPI))
        # Top-left
        draw.line([(b_px - 10, b_px), (b_px - 10 - c_len, b_px)], fill=(0, 0, 0), width=2)
        draw.line([(b_px, b_px - 10), (b_px, b_px - 10 - c_len)], fill=(0, 0, 0), width=2)
        # Top-right
        draw.line([(w_px - b_px + 10, b_px), (w_px - b_px + 10 + c_len, b_px)], fill=(0, 0, 0), width=2)
        draw.line([(w_px - b_px, b_px - 10), (w_px - b_px, b_px - 10 - c_len)], fill=(0, 0, 0), width=2)
        # Bottom-left
        draw.line([(b_px - 10, h_px - b_px), (b_px - 10 - c_len, h_px - b_px)], fill=(0, 0, 0), width=2)
        draw.line([(b_px, h_px - b_px + 10), (b_px, h_px - b_px + 10 + c_len)], fill=(0, 0, 0), width=2)
        # Bottom-right
        draw.line([(w_px - b_px + 10, h_px - b_px), (w_px - b_px + 10 + c_len, h_px - b_px)], fill=(0, 0, 0), width=2)
        draw.line([(w_px - b_px, h_px - b_px + 10), (w_px - b_px, h_px - b_px + 10 + c_len)], fill=(0, 0, 0), width=2)

    # Export 300 DPI PNG
    png_buf = io.BytesIO()
    img.save(png_buf, format="PNG", dpi=(300, 300))
    png_bytes = png_buf.getvalue()

    # Generate 250px thumbnail for UI preview
    thumb_ratio = 250.0 / float(w_px)
    thumb_h = int(round(h_px * thumb_ratio))
    thumb_img = img.resize((250, thumb_h), Image.Resampling.LANCZOS)
    thumb_buf = io.BytesIO()
    thumb_img.save(thumb_buf, format="PNG", quality=90)
    thumbnail_bytes = thumb_buf.getvalue()

    png_b64 = f"data:image/png;base64,{base64.b64encode(png_bytes).decode('utf-8')}"
    thumb_b64 = f"data:image/png;base64,{base64.b64encode(thumbnail_bytes).decode('utf-8')}"

    return png_bytes, thumbnail_bytes, png_b64, thumb_b64


def render_print_collateral(spec: PrintCollateralSpec) -> PrintRenderResult:
    """End-to-end rendering function outputting both commercial PDF and 300 DPI raster PNG."""
    dims = PRINT_FORMATS.get(spec.format, PRINT_FORMATS["a4_flyer"])
    
    # 1. Generate ReportLab PDF
    pdf_bytes = render_print_pdf(spec)

    # 2. Generate 300 DPI PNG & Thumbnail
    png_bytes, thumb_bytes, png_b64, thumb_b64 = render_print_png_and_thumbnail(spec)

    pdf_b64 = f"data:application/pdf;base64,{base64.b64encode(pdf_bytes).decode('utf-8')}"
    page_count = 2 if spec.format == "trifold_brochure" else 1

    return PrintRenderResult(
        pdf_bytes=pdf_bytes,
        png_bytes=png_bytes,
        thumbnail_bytes=thumb_bytes,
        pdf_base64=pdf_b64,
        png_base64=png_b64,
        thumbnail_base64=thumb_b64,
        format=spec.format,
        trim_width_mm=dims.trim_width_mm,
        trim_height_mm=dims.trim_height_mm,
        bleed_mm=dims.bleed_mm,
        total_width_px=dims.total_width_px,
        total_height_px=dims.total_height_px,
        dpi=300,
        page_count=page_count
    )
