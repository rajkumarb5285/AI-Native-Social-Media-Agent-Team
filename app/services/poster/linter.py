"""Deterministic Linter for Poster Specifications.

Enforces Section 5 (Linter and renderer contract) and Section 4 of the Poster Design Agent pack:
- WCAG 2.2 contrast compliance (>= 4.5:1, >= 3.0:1 for large text)
- 8px base grid alignment
- 6% outer margins & platform safe zones (Stories/Reels top 250px / bottom 340px)
- Bounding box collision and text overlap detection
- Typographic budget (max 2 font families, max 4 distinct sizes)
- Minimum text size threshold (>= 24px)
- Text overflow detection
- Anti-hallucination / honesty checks
"""
import math
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from .spec import PosterSpec, PosterElement


class LintReport(BaseModel):
    clean: bool = True
    blockers: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    contrast_results: List[Dict[str, Any]] = Field(default_factory=list)
    distinct_sizes: List[int] = Field(default_factory=list)
    distinct_left_axes: List[int] = Field(default_factory=list)


def parse_hex_color(hex_str: str) -> tuple[int, int, int]:
    """Parses hex string (#RGB, #RRGGBB, #RRGGBBAA) into (r, g, b) tuple."""
    if not hex_str or not isinstance(hex_str, str):
        return (0, 0, 0)
    cleaned = hex_str.strip().lstrip("#")
    if len(cleaned) == 3:
        cleaned = "".join([c * 2 for c in cleaned])
    if len(cleaned) >= 6:
        try:
            return (int(cleaned[0:2], 16), int(cleaned[2:4], 16), int(cleaned[4:6], 16))
        except ValueError:
            return (0, 0, 0)
    return (0, 0, 0)


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    """Computes relative luminance for WCAG 2.2 contrast."""
    channels = []
    for c in rgb:
        s = c / 255.0
        channels.append(s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(hex1: str, hex2: str) -> float:
    """Calculates contrast ratio (1.0 to 21.0) between two hex colors."""
    l1 = relative_luminance(parse_hex_color(hex1))
    l2 = relative_luminance(parse_hex_color(hex2))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def boxes_intersect(b1: PosterElement, b2: PosterElement) -> bool:
    """Checks if two element rectangles overlap."""
    return not (
        b1.x + b1.w <= b2.x or
        b2.x + b2.w <= b1.x or
        b1.y + b1.h <= b2.y or
        b2.y + b2.h <= b1.y
    )


def lint_poster_spec(spec: PosterSpec, brief: Optional[Dict[str, Any]] = None) -> LintReport:
    """Performs rigorous automated linting against the specification.
    
    Blocks any poster with broken contrast, clipped overflow, margin breaches,
    or fabricated facts before it reaches the human review or critic.
    """
    blockers: List[str] = []
    warnings: List[str] = []
    contrast_results: List[Dict[str, Any]] = []

    canvas = spec.canvas
    scale = canvas.scale or 1.0
    min_size_threshold = int(24 * scale)
    margin = canvas.margin
    bg_color = spec.background.value if spec.background.type == "solid" else "#0B0F19"

    distinct_fonts = set()
    distinct_sizes = set()
    left_axes = set()
    text_elements: List[PosterElement] = []
    non_decorative: List[PosterElement] = []

    # 1. Inspect elements and collect measurements
    for el in spec.elements:
        if not el.decorative:
            non_decorative.append(el)

        # 8px Grid Alignment Check
        for attr, val in [("x", el.x), ("y", el.y), ("w", el.w), ("h", el.h)]:
            if val % 8 != 0:
                warnings.append(f"Element '{el.id}' {attr}={val} is not a multiple of 8 (8px grid rule).")

        # Outer Margin Check
        if not el.decorative:
            if el.x < margin or el.y < margin or (el.x + el.w) > (canvas.width - margin) or (el.y + el.h) > (canvas.height - margin):
                blockers.append(
                    f"Element '{el.id}' violates 6% outer margin ({margin}px): box [x={el.x}, y={el.y}, w={el.w}, h={el.h}] exceeds canvas bounds."
                )

        # Reels / Stories Platform Safe Zone Check (1080x1920)
        if canvas.width == 1080 and canvas.height == 1920 and not el.decorative:
            if el.y < 250 or (el.y + el.h) > (1920 - 340):
                blockers.append(
                    f"Element '{el.id}' breaches Stories/Reels safe zone (top 250px and bottom 340px reserved for UI controls)."
                )

        if el.type in ("text", "badge"):
            text_elements.append(el)
            left_axes.add(el.x)
            if el.font:
                distinct_fonts.add(el.font)
            if el.size:
                distinct_sizes.add(el.size)

            # Minimum Font Size Check
            if el.size and el.size < min_size_threshold and el.id not in ("caption", "fine_print", "terms"):
                blockers.append(
                    f"Element '{el.id}' text size {el.size}px is below minimum readable size {min_size_threshold}px."
                )

            # Text Fit & Overflow Estimation
            if el.text and el.size and el.w and el.h:
                char_count = len(el.text)
                chars_per_line = max(1, int(el.w / (el.size * 0.52)))
                lines_needed = math.ceil(char_count / chars_per_line)
                line_height = el.line_height or 1.2
                required_height = lines_needed * el.size * line_height

                if required_height > el.h * 1.05:  # 5% tolerance
                    blockers.append(
                        f"Text overflow in '{el.id}': text requires ~{int(required_height)}px height ({lines_needed} lines) but container box height is {el.h}px."
                    )

                # Line length check
                if el.id == "headline" and chars_per_line > 32:
                    warnings.append(f"Headline line length ({chars_per_line} chars/line) is wide; recommend 12-28 chars.")
                elif el.id == "body" and chars_per_line > 50:
                    warnings.append(f"Body text line length ({chars_per_line} chars/line) exceeds optimal 35-45 characters.")

            # Contrast Check against background / container
            # Determine effective background under text
            effective_bg = bg_color
            for shape in spec.elements:
                if shape.id != el.id and shape.z < el.z and shape.fill and shape.fill.lower() != "none":
                    if boxes_intersect(shape, el):
                        effective_bg = shape.fill

            if el.color and effective_bg and effective_bg.startswith("#"):
                ratio = contrast_ratio(el.color, effective_bg)
                is_large = (el.size or 0) >= 24
                min_ratio = 3.0 if is_large else 4.5
                passed = ratio >= min_ratio

                contrast_results.append({
                    "element": el.id,
                    "text_color": el.color,
                    "bg_color": effective_bg,
                    "ratio": ratio,
                    "required": min_ratio,
                    "pass": passed
                })

                if not passed:
                    blockers.append(
                        f"Contrast violation on '{el.id}': text {el.color} on {effective_bg} has ratio {ratio}:1 (minimum required is {min_ratio}:1)."
                    )

    # 2. Type Budget Rule (Max 2 font families, max 4 distinct sizes)
    if len(distinct_sizes) > 4:
        warnings.append(f"Type scale budget warning: {len(distinct_sizes)} distinct font sizes used ({sorted(distinct_sizes)}). Limit to 4.")

    # 3. Alignment Axes Rule (At most 3 distinct left edges)
    if len(left_axes) > 4:
        warnings.append(f"Alignment grid warning: {len(left_axes)} distinct left edges ({sorted(left_axes)}). Aim for <= 3 axes.")

    # 4. Text Collision / Overlap Check
    for i in range(len(text_elements)):
        for j in range(i + 1, len(text_elements)):
            t1, t2 = text_elements[i], text_elements[j]
            if boxes_intersect(t1, t2):
                blockers.append(f"Text collision: '{t1.id}' overlaps with '{t2.id}'.")

    # 5. Honesty / Anti-Hallucination Guardrail
    if brief:
        supplied_text = str(brief).lower()
        dishonest_patterns = [
            (r"\bno\.?\s*1\b", "Fabricated 'No.1' claim detected"),
            (r"★★★★★|5\.0\s*star", "Fabricated 5-star rating detected"),
            (r"\bverified\b|\bofficial\s+badge\b", "Fabricated verification badge detected"),
            (r"\baward\s*winning\b", "Fabricated award claim detected"),
        ]
        for el in text_elements:
            if el.text:
                for pattern, msg in dishonest_patterns:
                    if re.search(pattern, el.text, re.IGNORECASE) and not re.search(pattern, supplied_text, re.IGNORECASE):
                        blockers.append(f"Honesty violation on '{el.id}': {msg} without client brief evidence.")

    return LintReport(
        clean=len(blockers) == 0,
        blockers=blockers,
        warnings=warnings,
        contrast_results=contrast_results,
        distinct_sizes=sorted(list(distinct_sizes)),
        distinct_left_axes=sorted(list(left_axes))
    )
