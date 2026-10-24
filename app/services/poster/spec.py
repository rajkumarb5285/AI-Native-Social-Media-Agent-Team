"""Pydantic Design Specification Schema for Poster Design Agent.

Enforces deterministic layouts, coordinates, type scales, and metadata
as specified in Section 3 (Prompt 3) and Section 4 of the Poster Design Agent pack.
"""
from typing import List, Optional, Literal, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator


class CanvasConfig(BaseModel):
    width: int = Field(default=1080, description="Canvas width in pixels")
    height: int = Field(default=1350, description="Canvas height in pixels")
    scale: float = Field(default=1.0, description="shorter side / 1080")
    margin: int = Field(default=64, description="6% of shorter side, rounded to multiple of 8")


class BackgroundConfig(BaseModel):
    type: Literal["solid", "gradient", "image"] = "solid"
    value: str = Field(default="#0B0F19", description="Hex color, linear-gradient string, or asset ID")


class FontsConfig(BaseModel):
    display: str = Field(default="Playfair Display", description="Display font family name")
    text: str = Field(default="Inter", description="Body / UI font family name")


class PosterElement(BaseModel):
    id: str = Field(description="Unique element identifier (e.g. headline, cta_bg, cta_text)")
    type: Literal["text", "shape", "image", "logo", "badge", "line"] = "text"
    z: int = Field(default=1, description="Z-index layer order (higher sits on top)")
    x: int = Field(default=64, description="Top-left X coordinate (multiple of 8)")
    y: int = Field(default=64, description="Top-left Y coordinate (multiple of 8)")
    w: int = Field(default=952, description="Bounding box width (multiple of 8)")
    h: int = Field(default=100, description="Bounding box height (multiple of 8)")
    radius: Optional[int] = Field(default=0, description="Border radius for rounded rectangles/pills")
    decorative: bool = Field(default=False, description="True if background decoration or scrim")

    # Typography Fields (type == 'text' or 'badge')
    text: Optional[str] = Field(default=None, description="Clean text content")
    font: Optional[Literal["display", "text"]] = Field(default="text", description="Display or body font family")
    weight: Optional[int] = Field(default=400, description="Font weight: 400, 500, 600, 700, 800, 900")
    size: Optional[int] = Field(default=32, description="Font size in px")
    line_height: Optional[float] = Field(default=1.2, description="Multiplier (e.g. 1.05 to 1.6)")
    letter_spacing: Optional[str] = Field(default="0em", description="e.g. '0.08em', '-0.01em', '0em'")
    color: Optional[str] = Field(default="#FFFFFF", description="Hex text color #RRGGBB")
    align: Optional[Literal["left", "center", "right"]] = Field(default="left", description="Horizontal alignment")
    max_lines: Optional[int] = Field(default=None, description="Max line wrap limit")
    transform: Optional[Literal["none", "uppercase"]] = Field(default="none", description="Text transform")

    # Visual & Vector Properties (shapes, pills, containers)
    fill: Optional[str] = Field(default=None, description="Fill color #RRGGBB or 'none'")
    stroke: Optional[str] = Field(default=None, description="Border / outline color #RRGGBB or 'none'")
    stroke_width: Optional[int] = Field(default=1, description="Border thickness in px")
    opacity: Optional[float] = Field(default=1.0, description="Opacity from 0.0 to 1.0")

    # Media Properties (type == 'image' or 'logo')
    asset: Optional[str] = Field(default=None, description="Asset ID or image source URL")
    fit: Optional[Literal["cover", "contain"]] = Field(default="cover", description="Image object-fit")
    object_position: Optional[str] = Field(default="50% 50%", description="CSS object-position focus anchor")


class OverlayScrim(BaseModel):
    needed: bool = False
    enabled: Optional[bool] = None
    type: Optional[str] = "solid"  # solid | gradient
    color: Optional[str] = "#000000"
    from_color: Optional[str] = Field(default="#000000", alias="from")
    opacity: float = 0.0
    blur: Optional[int] = 0
    area: Optional[Dict[str, int]] = Field(default_factory=lambda: {"x": 0, "y": 0, "w": 0, "h": 0})

    def is_active(self) -> bool:
        if self.enabled is not None:
            return self.enabled
        return self.needed or self.opacity > 0.0



class SelfCheck(BaseModel):
    fits: bool = True
    contrast_ok: bool = True
    overlaps_ok: bool = True
    margins_ok: bool = True
    notes: Optional[str] = ""


class PosterSpec(BaseModel):
    canvas: CanvasConfig = Field(default_factory=CanvasConfig)
    background: BackgroundConfig = Field(default_factory=BackgroundConfig)
    fonts: FontsConfig = Field(default_factory=FontsConfig)
    elements: List[PosterElement] = Field(default_factory=list)
    overlay_scrim: Optional[OverlayScrim] = Field(default_factory=OverlayScrim)
    reading_order: List[str] = Field(default_factory=list, description="Ordered element IDs by reading hierarchy")
    focal_element: str = Field(default="headline", description="Primary visual focal element ID")
    self_check: Optional[SelfCheck] = Field(default_factory=SelfCheck)
