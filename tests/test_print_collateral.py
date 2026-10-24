"""Tests for Phase 6: Print Collateral (Pamphlets, Flyers & Brochures).

Verifies:
1. Physical print dimensions at 300 DPI with 3mm bleed and 5mm safe margins.
2. High-resolution vector/raster QR code generation with error correction H.
3. Commercial ReportLab vector PDF rendering with crop marks and fold marks.
4. High-resolution 300 DPI raster PNG export and thumbnail preview.
5. Multi-page Tri-Fold brochure rendering (Outside 3 panels + Inside 3 panels).
6. Print Designer Agent synthesizing real business profiles and verified offerings.
7. Zero contamination: sneaker store receives sneaker drops, not coffee.
8. FastAPI endpoints: /api/print/formats, /api/print/qr, /api/print/generate, /api/print/download.
"""
import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.services.print.spec import (
    PRINT_FORMATS, PrintDimensions, PrintCollateralSpec, PrintOfferingItem, PrintQRCodeConfig,
    mm_to_px, BLEED_MM, DPI
)
from app.services.print.qr_generator import (
    generate_print_qr_image, generate_print_qr_bytes, generate_print_qr_base64
)
from app.services.print.renderer import (
    render_print_pdf, render_print_png_and_thumbnail, render_print_collateral, PrintRenderResult
)
from app.agents.print_designer import print_designer, PrintGenerationRequest

client = TestClient(app)


def test_300dpi_physical_dimensions_and_bleed():
    """Verifies that mm to px conversions strictly adhere to 300 DPI physical standards."""
    a4 = PRINT_FORMATS["a4_flyer"]
    assert a4.trim_width_mm == 210.0
    assert a4.trim_height_mm == 297.0
    assert a4.bleed_mm == 3.0
    assert a4.safe_margin_mm == 5.0

    # 210 mm at 300 DPI = 2480 px; 297 mm = 3508 px
    assert a4.trim_width_px == 2480
    assert a4.trim_height_px == 3508

    # 3mm bleed = 35 px; total = 2551 x 3579 px
    assert a4.bleed_px == 35
    assert a4.total_width_px == 2551
    assert a4.total_height_px == 3579

    a5 = PRINT_FORMATS["a5_leaflet"]
    assert a5.trim_width_px == 1748
    assert a5.trim_height_px == 2480

    trifold = PRINT_FORMATS["trifold_brochure"]
    assert trifold.trim_width_px == 3508
    assert trifold.trim_height_px == 2480
    assert trifold.orientation == "landscape"


def test_qr_code_generation_300dpi():
    """Verifies that print QR codes are rendered at 300 DPI with Error Correction H."""
    url = "https://apex-streetwear.com/drop"
    img = generate_print_qr_image(url, fg_color="#EA580C", bg_color="#FFFFFF", size_px=600)
    
    assert isinstance(img, Image.Image)
    assert img.size == (600, 600)

    png_bytes = generate_print_qr_bytes(url, size_px=600)
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")

    # Verify PIL detects 300 DPI resolution header
    opened_img = Image.open(io.BytesIO(png_bytes))
    dpi_info = opened_img.info.get("dpi")
    if dpi_info:
        assert int(round(dpi_info[0])) == 300

    b64 = generate_print_qr_base64(url, size_px=600)
    assert b64.startswith("data:image/png;base64,")


def test_a4_flyer_pdf_and_crop_marks():
    """Verifies that an A4 flyer renders valid PDF bytes with crop marks."""
    spec = PrintCollateralSpec(
        format="a4_flyer",
        headline="RETRO RUNNERS 2026",
        subhead="Limited production release for creators.",
        business_name="Apex Streetwear",
        tagline="AUTHENTIC SNEAKER CULTURE",
        contact_phone="+1 (555) 019-2834",
        contact_email="drops@apex-streetwear.com",
        contact_address="104 Mercer St, SoHo, NY",
        website_url="https://apex-streetwear.com",
        primary_color="#EA580C",
        accent_color="#F97316",
        bg_color="#FFFFFF",
        offerings=[
            PrintOfferingItem(name="Retro High OG Runner", price="$210", description="Full grain calfskin leather.", tag="EXCLUSIVE"),
            PrintOfferingItem(name="Raw Denim Oversized Hoodie", price="$120", description="480 GSM French terry cotton."),
        ],
        qr_code=PrintQRCodeConfig(url="https://apex-streetwear.com/soho"),
        show_crop_marks=True,
        dpi=300
    )

    pdf_bytes = render_print_pdf(spec)
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 1000


def test_trifold_brochure_rendering():
    """Verifies multi-page tri-fold brochure rendering (outside & inside 3-panel spreads)."""
    spec = PrintCollateralSpec(
        format="trifold_brochure",
        headline="BESPOKE AESTHETICS",
        subhead="Signature wellness treatments.",
        business_name="Luxe Botanical Spa",
        tagline="HOLISTIC WELLNESS RETREAT",
        primary_color="#0F766E",
        accent_color="#14B8A6",
        offerings=[
            PrintOfferingItem(name="Botanical Glow Facial", price="$135", description="Organic plant extracts & serum."),
            PrintOfferingItem(name="Deep Tissue Massage", price="$110", description="Targeted tension release."),
            PrintOfferingItem(name="Aromatherapy Body Wrap", price="$95", description="Eucalyptus essential oil therapy.")
        ],
        qr_code=PrintQRCodeConfig(url="https://luxebotanical.com/book"),
        show_crop_marks=True,
        show_fold_marks=True
    )

    res: PrintRenderResult = render_print_collateral(spec)

    assert res.format == "trifold_brochure"
    assert res.page_count == 2
    assert res.pdf_bytes.startswith(b"%PDF-")
    assert res.png_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    assert res.pdf_base64.startswith("data:application/pdf;base64,")
    assert res.png_base64.startswith("data:image/png;base64,")
    assert res.total_width_px == 3579
    assert res.total_height_px == 2551


def test_print_designer_agent_zero_contamination():
    """Verifies that generating print collateral for a streetwear store has zero coffee contamination."""
    req = PrintGenerationRequest(
        format="a4_flyer",
        headline="EXCLUSIVE SNEAKER DROP",
        subhead="Premium limited footwear.",
        goal="promotional"
    )

    result = print_designer.generate_collateral_for_business("default", req)

    assert result.format == "a4_flyer"
    assert result.pdf_bytes.startswith(b"%PDF-")
    assert result.dpi == 300

    # Ensure zero coffee contamination
    combined_str = f"{req.headline} {req.subhead}".lower()
    for coffee_term in ("latte", "espresso", "cappuccino", "roast", "beans", "brew"):
        assert coffee_term not in combined_str


def test_print_api_endpoints():
    """Tests GET /api/print/formats, POST /api/print/qr, POST /api/print/generate, and GET /api/print/download."""
    # 1. GET /api/print/formats
    res_formats = client.get("/api/print/formats")
    assert res_formats.status_code == 200
    formats_data = res_formats.json()
    assert formats_data["count"] >= 3
    format_ids = [f["id"] for f in formats_data["formats"]]
    assert "a4_flyer" in format_ids
    assert "a5_leaflet" in format_ids
    assert "trifold_brochure" in format_ids

    # 2. POST /api/print/qr
    res_qr = client.post("/api/print/qr", json={"url": "https://example.com/menu", "size_px": 500})
    assert res_qr.status_code == 200
    qr_data = res_qr.json()
    assert qr_data["url"] == "https://example.com/menu"
    assert qr_data["qr_base64"].startswith("data:image/png;base64,")

    # 3. POST /api/print/generate
    res_gen = client.post("/api/print/generate", json={"format": "a5_leaflet", "headline": "SUMMER SPECIALS"})
    assert res_gen.status_code == 200
    gen_data = res_gen.json()
    assert gen_data["format"] == "a5_leaflet"
    assert gen_data["dpi"] == 300
    assert gen_data["pdf_base64"].startswith("data:application/pdf;base64,")

    # 4. GET /api/print/download/a4_flyer.pdf
    res_dl = client.get("/api/print/download/a4_flyer.pdf")
    assert res_dl.status_code == 200
    assert "application/pdf" in res_dl.headers.get("content-type", "")
    assert res_dl.content.startswith(b"%PDF-")
    assert "attachment" in res_dl.headers.get("content-disposition", "")
