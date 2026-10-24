"""Print Collateral Specification & Dimensions Standards.

Enforces physical print standards:
- 300 DPI resolution (1 mm = 11.811 pixels at 300 DPI)
- 3mm industry standard bleed on all outer edges
- 5mm inner safe margin from trim line
- Commercial crop marks (trim marks) and fold marks
- Supported formats: A4 Flyer, A5 Leaflet, Tri-fold Brochure (6 panels), Bi-fold Brochure (4 panels)
"""
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field

# Constants for 300 DPI conversion
DPI = 300
MM_TO_INCH = 1.0 / 25.4
MM_TO_PX_300DPI = 300.0 / 25.4  # ~11.8110236 px per mm
BLEED_MM = 3.0
BLEED_PX = int(round(BLEED_MM * MM_TO_PX_300DPI))  # ~35 px at 300 DPI
SAFE_MARGIN_MM = 5.0
SAFE_MARGIN_PX = int(round(SAFE_MARGIN_MM * MM_TO_PX_300DPI))  # ~59 px


def mm_to_px(mm: float, dpi: int = 300) -> int:
    """Converts millimetres to pixels at the given DPI."""
    return int(round(mm * (dpi / 25.4)))


class PrintDimensions(BaseModel):
    """Exact physical dimensions and pixel dimensions for print formats."""
    name: str
    trim_width_mm: float
    trim_height_mm: float
    bleed_mm: float = BLEED_MM
    safe_margin_mm: float = SAFE_MARGIN_MM
    dpi: int = DPI
    orientation: Literal["portrait", "landscape"] = "portrait"

    @property
    def total_width_mm(self) -> float:
        return self.trim_width_mm + (2 * self.bleed_mm)

    @property
    def total_height_mm(self) -> float:
        return self.trim_height_mm + (2 * self.bleed_mm)

    @property
    def trim_width_px(self) -> int:
        return mm_to_px(self.trim_width_mm, self.dpi)

    @property
    def trim_height_px(self) -> int:
        return mm_to_px(self.trim_height_mm, self.dpi)

    @property
    def bleed_px(self) -> int:
        return mm_to_px(self.bleed_mm, self.dpi)

    @property
    def safe_margin_px(self) -> int:
        return mm_to_px(self.safe_margin_mm, self.dpi)

    @property
    def total_width_px(self) -> int:
        return mm_to_px(self.total_width_mm, self.dpi)

    @property
    def total_height_px(self) -> int:
        return mm_to_px(self.total_height_mm, self.dpi)


# Standard Formats Catalog
PRINT_FORMATS: Dict[str, PrintDimensions] = {
    "a4_flyer": PrintDimensions(
        name="A4 Promotional Flyer",
        trim_width_mm=210.0,
        trim_height_mm=297.0,
        bleed_mm=3.0,
        safe_margin_mm=5.0,
        orientation="portrait"
    ),
    "a5_leaflet": PrintDimensions(
        name="A5 Compact Leaflet / Handout",
        trim_width_mm=148.0,
        trim_height_mm=210.0,
        bleed_mm=3.0,
        safe_margin_mm=5.0,
        orientation="portrait"
    ),
    "trifold_brochure": PrintDimensions(
        name="Tri-fold Brochure (A4 6-Panel)",
        trim_width_mm=297.0,
        trim_height_mm=210.0,
        bleed_mm=3.0,
        safe_margin_mm=5.0,
        orientation="landscape"
    ),
    "bifold_brochure": PrintDimensions(
        name="Bi-fold Brochure (A4 to 4x A5 Pages)",
        trim_width_mm=297.0,
        trim_height_mm=210.0,
        bleed_mm=3.0,
        safe_margin_mm=5.0,
        orientation="landscape"
    ),
}


class PrintQRCodeConfig(BaseModel):
    """Configuration for embedded high-resolution vector/raster QR code."""
    url: str
    label: str = "Scan to Visit / Book"
    fg_color: str = "#0F172A"
    bg_color: str = "#FFFFFF"
    size_mm: float = 28.0  # 28mm is optimum print scan size
    error_correction: Literal["M", "Q", "H"] = "H"  # High for print durability


class PrintOfferingItem(BaseModel):
    """Product or service row for print collateral."""
    name: str
    price: Optional[str] = None
    description: Optional[str] = None
    tag: Optional[str] = None  # e.g. "Bestseller", "New", "Featured"


class PrintCollateralSpec(BaseModel):
    """Pydantic specification for a multi-page or single-page print collateral."""
    format: str = "a4_flyer"  # a4_flyer | a5_leaflet | trifold_brochure | bifold_brochure
    headline: str
    subhead: Optional[str] = None
    business_name: str
    tagline: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    contact_address: Optional[str] = None
    website_url: Optional[str] = None
    primary_color: str = "#0F172A"
    accent_color: str = "#F59E0B"
    bg_color: str = "#FFFFFF"
    offerings: List[PrintOfferingItem] = Field(default_factory=list)
    qr_code: Optional[PrintQRCodeConfig] = None
    show_crop_marks: bool = True
    show_fold_marks: bool = True
    dpi: int = 300
