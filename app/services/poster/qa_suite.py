"""Playwright & DOM-based QA Suite for Production Poster Rendering.

Implements Phase 5 QA verification across:
1. Real in-DOM text overflow and clipping across dynamic headlines.
2. WCAG 2.2 contrast compliance (>= 4.5:1 for normal text, >= 3.0:1 for large text).
3. Font rendering and typographic budget (max 2 font families, max 4 distinct sizes, min 22px).
4. Dual-axis alignment (A_L=80, A_R=1000, A_C=540, T=80, B=1270).
5. Strict 8px base grid geometry across all coordinates and dimensions.
6. Safe margins (6% canvas margins) and platform safe zones (Stories/Reels top 250px / bottom 340px).
7. Non-decorative bounding box collision avoidance.
8. Automated actionable numeric adjustments for auto-revision loops.
"""
import math
import re
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.services.poster.spec import PosterSpec, PosterElement
from app.services.poster.linter import parse_hex_color, contrast_ratio, boxes_intersect


class QACheckResult(BaseModel):
    name: str
    passed: bool
    score: float = Field(ge=0.0, le=10.0)
    details: str
    violations: List[str] = Field(default_factory=list)
    measurements: Dict[str, Any] = Field(default_factory=dict)


class NumericAdjustment(BaseModel):
    element_id: str
    attribute: str  # x, y, w, h, size, color, fill
    current_value: Any
    suggested_value: Any
    reason: str


class QASuiteReport(BaseModel):
    passed: bool
    overall_score: float = Field(ge=0.0, le=10.0)
    clean: bool
    checks: Dict[str, QACheckResult] = Field(default_factory=dict)
    all_violations: List[str] = Field(default_factory=list)
    numeric_adjustments: List[NumericAdjustment] = Field(default_factory=list)
    dom_inspected: bool = False
    playwright_used: bool = False


def generate_poster_html(spec: PosterSpec) -> str:
    """Generates complete, self-contained HTML/CSS for a PosterSpec.
    
    Includes Google Web Fonts, responsive box sizing, absolute positioning,
    typography tokens, and data attributes for precision DOM inspection.
    """
    canvas = spec.canvas
    w = canvas.width
    h = canvas.height

    display_font = spec.fonts.display or "Playfair Display"
    text_font = spec.fonts.text or "Inter"

    # Background styling
    if spec.background.type == "gradient":
        bg_style = f"background: {spec.background.value};"
    elif spec.background.type == "image":
        bg_style = f"background-image: url('{spec.background.value}'); background-size: cover; background-position: center;"
    else:
        bg_style = f"background-color: {spec.background.value};"

    # Collect elements HTML
    elements_html: List[str] = []
    for el in sorted(spec.elements, key=lambda e: e.z):
        font_family = f"'{display_font}', serif" if el.font == "display" else f"'{text_font}', sans-serif"
        
        # Build style properties
        style_parts = [
            "position: absolute;",
            f"left: {el.x}px;",
            f"top: {el.y}px;",
            f"width: {el.w}px;",
            f"height: {el.h}px;",
            f"z-index: {el.z};",
            "box-sizing: border-box;",
        ]

        if el.radius:
            style_parts.append(f"border-radius: {el.radius}px;")

        if el.type in ("text", "badge"):
            style_parts.extend([
                f"font-family: {font_family};",
                f"font-size: {el.size or 32}px;",
                f"font-weight: {el.weight or 400};",
                f"line-height: {el.line_height or 1.2};",
                f"color: {el.color or '#FFFFFF'};",
                f"text-align: {el.align or 'left'};",
                f"letter-spacing: {el.letter_spacing or '0em'};",
                "overflow: hidden;",
                "word-break: break-word;",
            ])
            if el.transform == "uppercase":
                style_parts.append("text-transform: uppercase;")
            
            # Badge or pill background
            if el.fill and el.fill != "none":
                style_parts.append(f"background-color: {el.fill};")
            if el.stroke and el.stroke != "none" and el.stroke_width:
                style_parts.append(f"border: {el.stroke_width}px solid {el.stroke};")

            content = el.text or ""
            elements_html.append(
                f'<div data-element-id="{el.id}" data-element-type="{el.type}" class="poster-element poster-text" style="{" ".join(style_parts)}">'
                f'{content}'
                f'</div>'
            )

        elif el.type == "shape":
            if el.fill and el.fill != "none":
                style_parts.append(f"background-color: {el.fill};")
            if el.stroke and el.stroke != "none" and el.stroke_width:
                style_parts.append(f"border: {el.stroke_width}px solid {el.stroke};")
            elements_html.append(
                f'<div data-element-id="{el.id}" data-element-type="{el.type}" class="poster-element poster-shape" style="{" ".join(style_parts)}">'
                f'</div>'
            )

        elif el.type == "line":
            bg = el.fill or el.color or "#FFFFFF"
            style_parts.append(f"background-color: {bg};")
            elements_html.append(
                f'<div data-element-id="{el.id}" data-element-type="{el.type}" class="poster-element poster-line" style="{" ".join(style_parts)}">'
                f'</div>'
            )

        elif el.type in ("image", "logo"):
            if el.fill and el.fill != "none":
                style_parts.append(f"background-color: {el.fill};")
            content_img = f'<img src="{el.asset or ""}" style="width: 100%; height: 100%; object-fit: contain;" alt="{el.id}" />' if el.asset else ""
            elements_html.append(
                f'<div data-element-id="{el.id}" data-element-type="{el.type}" class="poster-element poster-image" style="{" ".join(style_parts)}">'
                f'{content_img}'
                f'</div>'
            )

    body_elements = "\n    ".join(elements_html)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width={w}, height={h}, initial-scale=1.0">
  <title>Poster Spec Render QA</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..900;1,9..144,400..900&family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:ital,wght@0,400..900;1,400..900&family=Montserrat:wght@400;600;700;800&family=Oswald:wght@500;700&display=swap" rel="stylesheet">
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
      -webkit-font-smoothing: antialiased;
    }}
    body {{
      width: {w}px;
      height: {h}px;
      overflow: hidden;
      display: flex;
      justify-content: center;
      align-items: center;
      background: #000;
    }}
    #poster-canvas {{
      position: relative;
      width: {w}px;
      height: {h}px;
      overflow: hidden;
      {bg_style}
    }}
    .poster-element {{
      user-select: none;
    }}
  </style>
</head>
<body>
  <div id="poster-canvas">
    {body_elements}
  </div>
</body>
</html>"""


async def inspect_poster_dom_playwright(html: str, width: int = 1080, height: int = 1350) -> Dict[str, Any]:
    """Inspects rendered poster DOM using headless Playwright Chromium.
    
    Extracts computed layout bounds, font metrics, text overflow, and rendered styles.
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.set_content(html, wait_until="load")
            
            try:
                await page.evaluate("document.fonts.ready")
            except Exception:
                pass

            eval_script = """() => {
                const elements = Array.from(document.querySelectorAll('[data-element-id]')).map(el => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    const isText = el.getAttribute('data-element-type') === 'text' || el.getAttribute('data-element-type') === 'badge';
                    const scrollW = el.scrollWidth;
                    const clientW = el.clientWidth;
                    const scrollH = el.scrollHeight;
                    const clientH = el.clientHeight;
                    
                    const overflowsH = scrollH > clientH + 4;
                    const overflowsW = scrollW > clientW + 4;
                    
                    return {
                        id: el.getAttribute('data-element-id'),
                        type: el.getAttribute('data-element-type'),
                        rect: {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            w: Math.round(rect.width),
                            h: Math.round(rect.height),
                            right: Math.round(rect.right),
                            bottom: Math.round(rect.bottom)
                        },
                        scroll: { scrollWidth: scrollW, clientWidth: clientW, scrollHeight: scrollH, clientHeight: clientH },
                        overflows: isText && (overflowsH || overflowsW),
                        overflow_details: overflowsH ? `height overflow (${scrollH}px > ${clientH}px)` : (overflowsW ? `width overflow (${scrollW}px > ${clientW}px)` : 'none'),
                        style: {
                            fontFamily: style.fontFamily,
                            fontSize: parseFloat(style.fontSize) || 0,
                            fontWeight: style.fontWeight,
                            lineHeight: style.lineHeight,
                            color: style.color,
                            backgroundColor: style.backgroundColor
                        },
                        text: el.innerText || ''
                    };
                });
                return { elements, canvasWidth: document.getElementById('poster-canvas')?.clientWidth || 1080 };
            }"""
            
            result = await page.evaluate(eval_script)
            return result
        finally:
            await browser.close()


def inspect_poster_dom_fallback(spec: PosterSpec) -> Dict[str, Any]:
    """Pure Python fallback DOM inspector when headless browser is not required or in unit test mode."""
    elements = []
    for el in spec.elements:
        is_text = el.type in ("text", "badge")
        overflows = False
        overflow_details = "none"

        if is_text and el.text:
            text_len = len(el.text)
            font_size = el.size or 32
            chars_per_line = max(1, int(el.w / (font_size * 0.52)))
            est_lines = math.ceil(text_len / chars_per_line)
            line_height = int(font_size * (el.line_height or 1.2))
            est_total_h = est_lines * line_height

            if est_total_h > el.h + 8:
                overflows = True
                overflow_details = f"estimated height overflow ({est_total_h}px > {el.h}px for {text_len} chars)"

        elements.append({
            "id": el.id,
            "type": el.type,
            "rect": {
                "x": el.x,
                "y": el.y,
                "w": el.w,
                "h": el.h,
                "right": el.x + el.w,
                "bottom": el.y + el.h
            },
            "scroll": {"scrollWidth": el.w, "clientWidth": el.w, "scrollHeight": el.h, "clientHeight": el.h},
            "overflows": overflows,
            "overflow_details": overflow_details,
            "style": {
                "fontFamily": spec.fonts.display if el.font == "display" else spec.fonts.text,
                "fontSize": el.size or 32,
                "fontWeight": str(el.weight or 400),
                "lineHeight": str(el.line_height or 1.2),
                "color": el.color or "#FFFFFF",
                "backgroundColor": el.fill or ""
            },
            "text": el.text or ""
        })

    return {"elements": elements, "canvasWidth": spec.canvas.width}


def check_text_overflow_dom(elements_data: List[Dict[str, Any]]) -> QACheckResult:
    """Verifies that no text element clips or overflows its container bounding box."""
    violations = []
    overflow_count = 0

    for item in elements_data:
        if item.get("overflows"):
            overflow_count += 1
            violations.append(
                f"Element '{item['id']}' has text clipping/overflow: {item.get('overflow_details')}"
            )

    passed = (overflow_count == 0)
    score = 10.0 if passed else max(0.0, 10.0 - (overflow_count * 3.5))

    return QACheckResult(
        name="text_overflow_and_clipping",
        passed=passed,
        score=score,
        details="All dynamic copy fits within container bounding boxes without overflow" if passed else f"{overflow_count} elements clipped/overflowed",
        violations=violations,
        measurements={"overflow_count": overflow_count}
    )


def check_wcag_contrast_qa(spec: PosterSpec) -> QACheckResult:
    """Validates WCAG 2.2 contrast compliance (>= 4.5:1 normal, >= 3.0:1 large)."""
    violations = []
    tested = 0
    canvas_bg = spec.background.value if spec.background.type == "solid" else "#0B0F19"
    contrast_results = []

    for el in spec.elements:
        if el.type in ("text", "badge") and el.text:
            tested += 1
            text_color = el.color or "#FFFFFF"
            bg = el.fill if (el.fill and el.fill != "none") else canvas_bg
            
            # If element doesn't have an explicit fill, look for a background shape underneath
            if not el.fill or el.fill == "none":
                for bg_el in sorted(spec.elements, key=lambda e: e.z, reverse=True):
                    if bg_el.z < el.z and bg_el.type == "shape" and bg_el.fill and bg_el.fill != "none":
                        if boxes_intersect(el, bg_el):
                            bg = bg_el.fill
                            break

            ratio = contrast_ratio(text_color, bg)
            is_large = (el.size or 32) >= 32
            min_ratio = 3.0 if is_large else 4.5

            contrast_results.append({
                "id": el.id,
                "text_color": text_color,
                "bg_color": bg,
                "ratio": ratio,
                "required": min_ratio,
                "passed": ratio >= min_ratio
            })

            if ratio < min_ratio:
                violations.append(
                    f"Contrast failure on '{el.id}': {text_color} on {bg} is {ratio}:1 (required >={min_ratio}:1)"
                )

    passed = (len(violations) == 0)
    score = 10.0 if passed else max(0.0, 10.0 - (len(violations) * 2.5))

    return QACheckResult(
        name="wcag_contrast_compliance",
        passed=passed,
        score=score,
        details=f"All {tested} text elements meet WCAG 2.2 contrast thresholds" if passed else f"{len(violations)} contrast violations found",
        violations=violations,
        measurements={"contrast_results": contrast_results, "tested_elements": tested}
    )


def check_typography_budget_qa(spec: PosterSpec) -> QACheckResult:
    """Enforces typographic budget: max 2 font families, max 4 distinct sizes, min 22px."""
    violations = []
    sizes = set()
    fonts = set()
    scale = spec.canvas.scale or 1.0
    min_size_threshold = int(22 * scale)

    for el in spec.elements:
        if el.type in ("text", "badge") and el.text:
            if el.size:
                sizes.add(el.size)
                if el.size < min_size_threshold:
                    violations.append(
                        f"Element '{el.id}' font size {el.size}px is below minimum {min_size_threshold}px threshold"
                    )
            font_name = spec.fonts.display if el.font == "display" else spec.fonts.text
            fonts.add(font_name)

    if len(sizes) > 4:
        violations.append(f"Typographic size budget exceeded: {len(sizes)} distinct sizes used (max allowed 4: {sorted(list(sizes))})")

    if len(fonts) > 2:
        violations.append(f"Font family budget exceeded: {len(fonts)} distinct families used (max allowed 2: {fonts})")

    passed = (len(violations) == 0)
    score = 10.0 if passed else max(0.0, 10.0 - (len(violations) * 3.0))

    return QACheckResult(
        name="typography_budget_and_scale",
        passed=passed,
        score=score,
        details=f"Typography budget verified: {len(fonts)} fonts, {len(sizes)} sizes" if passed else "; ".join(violations),
        violations=violations,
        measurements={"font_count": len(fonts), "fonts": list(fonts), "size_count": len(sizes), "sizes": sorted(list(sizes))}
    )


def check_dual_axis_and_grid_qa(spec: PosterSpec) -> QACheckResult:
    """Verifies strict dual-axis alignment and 8px base grid geometry."""
    violations = []
    margin = spec.canvas.margin or 64
    w = spec.canvas.width
    h = spec.canvas.height
    
    A_L = 80 if margin == 80 else margin
    A_R = w - A_L
    A_C = w // 2
    T = A_L
    B = h - A_L

    allowed_left = {A_L, A_L - 3, margin, margin - 3}
    allowed_right = {A_R, w - margin}

    for el in spec.elements:
        # Check 8px grid snapping (headline allows -3px optical offset; centered elements allow 4px center-rounding tolerance)
        is_headline = (el.id == "headline")
        is_centered = (el.align == "center" or abs(el.x + (el.w / 2.0) - A_C) <= 4)
        x_tolerance = 4 if is_centered else (3 if is_headline else 0)

        if (el.x + x_tolerance) % 8 != 0 and (el.x - x_tolerance) % 8 != 0 and el.x % 8 != 0:
            violations.append(f"Element '{el.id}' x coordinate {el.x} is not on 8px grid")
        if el.y % 8 != 0:
            violations.append(f"Element '{el.id}' y coordinate {el.y} is not on 8px grid")
        if el.w % 8 != 0:
            violations.append(f"Element '{el.id}' width {el.w} is not a multiple of 8")
        if el.type != "line" and el.h % 8 != 0:
            violations.append(f"Element '{el.id}' height {el.h} is not a multiple of 8")


        # Top-level primary axis alignment checks
        if el.id in ("logo", "rule") and not el.decorative:
            if el.align == "left" and el.x not in allowed_left:
                violations.append(f"Element '{el.id}' left edge {el.x} does not snap to Left Axis ({allowed_left})")
        
        if el.id in ("badge", "showcase_badge", "handle", "footer_meta"):
            if el.align == "right" and (el.x + el.w) not in allowed_right:
                violations.append(f"Element '{el.id}' right edge {el.x + el.w} does not snap to Right Axis ({allowed_right})")

    passed = (len(violations) == 0)
    score = 10.0 if passed else max(0.0, 10.0 - (len(violations) * 1.5))

    return QACheckResult(
        name="dual_axis_and_8px_grid",
        passed=passed,
        score=score,
        details="Dual-axis alignment and 8px grid strictly respected" if passed else f"{len(violations)} alignment/grid discrepancies",
        violations=violations,
        measurements={"axes": {"A_L": A_L, "A_R": A_R, "A_C": A_C, "T": T, "B": B}}
    )


def check_safe_margins_and_collisions_qa(spec: PosterSpec, platform: Optional[str] = None) -> QACheckResult:
    """Verifies 6% outer margin safety, Stories/Reels safe zones, and non-decorative overlaps."""
    violations = []
    margin = spec.canvas.margin or 64
    w = spec.canvas.width
    h = spec.canvas.height
    is_story = platform in ("instagram_stories", "instagram_reels", "tiktok", "story")

    non_decorative: List[PosterElement] = []

    for el in spec.elements:
        if not el.decorative:
            non_decorative.append(el)

            # Check outer margins
            if el.x < margin:
                violations.append(f"Element '{el.id}' breaches left margin at x={el.x} (min {margin})")
            if el.x + el.w > w - margin:
                violations.append(f"Element '{el.id}' breaches right margin at x+w={el.x + el.w} (max {w - margin})")
            if el.y < margin:
                violations.append(f"Element '{el.id}' breaches top margin at y={el.y} (min {margin})")
            if el.y + el.h > h - margin:
                violations.append(f"Element '{el.id}' breaches bottom margin at y+h={el.y + el.h} (max {h - margin})")

            # Check platform safe zones (Stories/Reels top 250px, bottom 340px)
            if is_story:
                if el.y < 250 and el.id not in ("status_bar", "header_scrim"):
                    violations.append(f"Element '{el.id}' breaches story top safe zone (y={el.y} < 250px)")
                if el.y + el.h > (h - 340) and el.id not in ("bottom_scrim", "footer_blur"):
                    violations.append(f"Element '{el.id}' breaches story bottom safe zone (y+h={el.y + el.h} > {h - 340}px)")

    # Bounding Box Collisions
    for i in range(len(non_decorative)):
        for j in range(i + 1, len(non_decorative)):
            e1 = non_decorative[i]
            e2 = non_decorative[j]

            # Allow parent/child text inside button/badge container
            if (e1.id.startswith(e2.id) or e2.id.startswith(e1.id) or
                ("cta_text" in (e1.id, e2.id) and "cta_bg" in (e1.id, e2.id)) or
                ("badge" in (e1.id, e2.id) and "badge_bg" in (e1.id, e2.id))):
                continue

            if boxes_intersect(e1, e2):
                violations.append(f"Collision detected: non-decorative elements '{e1.id}' and '{e2.id}' overlap")

    passed = (len(violations) == 0)
    score = 10.0 if passed else max(0.0, 10.0 - (len(violations) * 2.5))

    return QACheckResult(
        name="safe_margins_and_collisions",
        passed=passed,
        score=score,
        details="Safe margins intact and zero bounding box collisions" if passed else f"{len(violations)} margin or collision breaches",
        violations=violations,
        measurements={"non_decorative_count": len(non_decorative)}
    )


def generate_actionable_adjustments(spec: PosterSpec, check_results: Dict[str, QACheckResult]) -> List[NumericAdjustment]:
    """Generates deterministic numeric adjustments to fix failing QA checks during auto-revision."""
    adjustments: List[NumericAdjustment] = []

    # 1. 8px grid snapping adjustments
    for el in spec.elements:
        if el.x % 8 != 0 and not (el.id == "headline" and (el.x + 3) % 8 == 0):
            snapped = int(round(el.x / 8.0) * 8)
            adjustments.append(NumericAdjustment(
                element_id=el.id, attribute="x", current_value=el.x, suggested_value=snapped,
                reason="Snap to 8px base grid"
            ))
        if el.y % 8 != 0:
            snapped = int(round(el.y / 8.0) * 8)
            adjustments.append(NumericAdjustment(
                element_id=el.id, attribute="y", current_value=el.y, suggested_value=snapped,
                reason="Snap to 8px base grid"
            ))
        if el.w % 8 != 0:
            snapped = int(round(el.w / 8.0) * 8)
            adjustments.append(NumericAdjustment(
                element_id=el.id, attribute="w", current_value=el.w, suggested_value=snapped,
                reason="Snap width to 8px base grid"
            ))
        if el.h % 8 != 0:
            snapped = int(round(el.h / 8.0) * 8)
            adjustments.append(NumericAdjustment(
                element_id=el.id, attribute="h", current_value=el.h, suggested_value=snapped,
                reason="Snap height to 8px base grid"
            ))

    # 2. Contrast adjustments
    contrast_check = check_results.get("wcag_contrast_compliance")
    if contrast_check and not contrast_check.passed:
        for res in contrast_check.measurements.get("contrast_results", []):
            if not res.get("passed"):
                el_id = res.get("id")
                target_color = "#0F172A" if parse_hex_color(res.get("bg_color", "#FFFFFF"))[0] > 180 else "#FFFFFF"
                adjustments.append(NumericAdjustment(
                    element_id=el_id,
                    attribute="color",
                    current_value=res.get("text_color"),
                    suggested_value=target_color,
                    reason=f"Increase contrast from {res.get('ratio')}:1 to > 4.5:1"
                ))

    # 3. Overflow adjustments
    overflow_check = check_results.get("text_overflow_and_clipping")
    if overflow_check and not overflow_check.passed:
        for v in overflow_check.violations:
            match = re.search(r"Element '([^']+)'", v)
            if match:
                el_id = match.group(1)
                for el in spec.elements:
                    if el.id == el_id:
                        new_h = int(round((el.h + 40) / 8.0) * 8)
                        adjustments.append(NumericAdjustment(
                            element_id=el_id,
                            attribute="h",
                            current_value=el.h,
                            suggested_value=new_h,
                            reason="Expand container height to resolve text overflow"
                        ))

    return adjustments


async def run_full_poster_qa(
    spec: PosterSpec,
    brief: Optional[Dict[str, Any]] = None,
    platform: Optional[str] = None,
    use_playwright: bool = True
) -> QASuiteReport:
    """Runs the complete QA Suite against a poster specification.
    
    Attempts Playwright headless DOM inspection first; gracefully falls back to
    deterministic mathematical DOM evaluator if Playwright is unavailable.
    """
    html = generate_poster_html(spec)
    playwright_success = False
    dom_data: Dict[str, Any] = {}

    if use_playwright:
        try:
            dom_data = await inspect_poster_dom_playwright(html, width=spec.canvas.width, height=spec.canvas.height)
            playwright_success = True
        except Exception:
            dom_data = inspect_poster_dom_fallback(spec)
    else:
        dom_data = inspect_poster_dom_fallback(spec)

    elements_data = dom_data.get("elements", [])

    overflow_res = check_text_overflow_dom(elements_data)
    contrast_res = check_wcag_contrast_qa(spec)
    typography_res = check_typography_budget_qa(spec)
    dual_axis_res = check_dual_axis_and_grid_qa(spec)
    margins_res = check_safe_margins_and_collisions_qa(spec, platform=platform)

    checks = {
        "text_overflow_and_clipping": overflow_res,
        "wcag_contrast_compliance": contrast_res,
        "typography_budget_and_scale": typography_res,
        "dual_axis_and_8px_grid": dual_axis_res,
        "safe_margins_and_collisions": margins_res
    }

    all_violations: List[str] = []
    for c in checks.values():
        all_violations.extend(c.violations)

    weights = {
        "text_overflow_and_clipping": 0.25,
        "wcag_contrast_compliance": 0.25,
        "typography_budget_and_scale": 0.15,
        "dual_axis_and_8px_grid": 0.15,
        "safe_margins_and_collisions": 0.20
    }

    overall_score = round(sum(checks[k].score * weights[k] for k in weights), 1)
    clean = (len(all_violations) == 0)
    passed = clean and overall_score >= 8.0

    adjustments = generate_actionable_adjustments(spec, checks)

    return QASuiteReport(
        passed=passed,
        overall_score=overall_score,
        clean=clean,
        checks=checks,
        all_violations=all_violations,
        numeric_adjustments=adjustments,
        dom_inspected=True,
        playwright_used=playwright_success
    )
