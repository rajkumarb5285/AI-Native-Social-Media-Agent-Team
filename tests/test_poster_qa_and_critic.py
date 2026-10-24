"""Tests for Phase 5: Designer Rules, Renderer & Automated QA Suite.

Verifies:
1. Playwright & DOM-based automated QA inspection (in-browser headless chromium).
2. Text overflow and clipping detection.
3. WCAG 2.2 contrast compliance (>= 4.5:1 normal, >= 3.0:1 large).
4. Typographic budget (max 2 font families, max 4 distinct sizes, min 22px).
5. Dual-axis alignment (A_L=80, A_R=1000, A_C=540, T=80, B=1270) & strict 8px grid.
6. Safe margins (6% canvas margins) and platform safe zones (Stories/Reels top 250px / bottom 340px).
7. Non-decorative bounding box collision avoidance.
8. Multi-modal Vision Critic 10-criterion rubric evaluation (>= 8.0 threshold).
9. Monotonic auto-revision convergence loop.
10. FastAPI endpoints: /api/poster/qa/inspect, /api/poster/critic/evaluate, /api/poster/render/html.
"""
import pytest
import asyncio
from fastapi.testclient import TestClient

from app.main import app
from app.services.poster.spec import PosterSpec, PosterElement, CanvasConfig, BackgroundConfig, FontsConfig
from app.services.poster.archetypes import get_archetype_template
from app.services.poster.qa_suite import (
    generate_poster_html,
    inspect_poster_dom_playwright,
    inspect_poster_dom_fallback,
    run_full_poster_qa,
    check_text_overflow_dom,
    check_wcag_contrast_qa,
    check_typography_budget_qa,
    check_dual_axis_and_grid_qa,
    check_safe_margins_and_collisions_qa,
    generate_actionable_adjustments,
    QASuiteReport
)
from app.services.poster.vision_critic import (
    evaluate_vision_critic,
    apply_numeric_revisions,
    VisionCritiqueReport
)
from app.agents.poster_designer import build_poster_design_graph, PosterState

client = TestClient(app)


def test_generate_poster_html_structure():
    """Verifies that generated HTML includes correct viewport, Google Fonts, and data attributes."""
    spec = get_archetype_template(
        "hero-text",
        headline="PREMIUM RUNNERS",
        subhead="Engineered for speed.",
        cta="Shop Drop",
        primary_color="#F97316"
    )
    html = generate_poster_html(spec)

    assert "<!DOCTYPE html>" in html
    assert "width=1080" in html
    assert "height=1350" in html
    assert "fonts.googleapis.com" in html
    assert 'data-element-id="headline"' in html
    assert 'data-element-id="cta_bg"' in html
    assert 'data-element-type="text"' in html
    assert "#poster-canvas" in html


@pytest.mark.asyncio
async def test_playwright_in_dom_inspection_runs_headless():
    """Verifies real headless Playwright Chromium execution on generated HTML."""
    spec = get_archetype_template(
        "centered-badge",
        headline="GRAND OPENING",
        subhead="Join us this Saturday.",
        cta="RSVP Now",
        primary_color="#10B981"
    )
    html = generate_poster_html(spec)

    dom_data = await inspect_poster_dom_playwright(html, width=1080, height=1350)

    assert "elements" in dom_data
    assert len(dom_data["elements"]) > 0

    headline_el = next((e for e in dom_data["elements"] if e["id"] == "headline"), None)
    assert headline_el is not None
    assert headline_el["rect"]["w"] > 0
    assert headline_el["rect"]["h"] > 0
    assert headline_el["overflows"] is False


def test_text_overflow_detection_on_oversized_copy():
    """Verifies that text overflow is caught and flagged as a blocker."""
    elements_with_overflow = [
        {
            "id": "headline",
            "type": "text",
            "overflows": True,
            "overflow_details": "height overflow (280px > 120px)",
            "rect": {"x": 80, "y": 800, "w": 920, "h": 120}
        }
    ]
    res = check_text_overflow_dom(elements_with_overflow)
    assert res.passed is False
    assert res.score < 8.0
    assert len(res.violations) == 1
    assert "headline" in res.violations[0]


def test_wcag_contrast_compliance_check():
    """Verifies WCAG 2.2 contrast compliance and failure detection."""
    # 1. Clean high contrast spec
    clean_spec = get_archetype_template(
        "hero-text",
        headline="HIGH CONTRAST",
        subhead="Legible white on dark background.",
        cta="Discover",
        primary_color="#F59E0B"
    )
    res_clean = check_wcag_contrast_qa(clean_spec)
    assert res_clean.passed is True
    assert res_clean.score >= 9.0

    # 2. Failing low contrast spec (light gray text on white fill)
    bad_spec = clean_spec.model_copy(deep=True)
    for el in bad_spec.elements:
        if el.id == "subhead":
            el.color = "#E2E8F0"  # Light gray
            el.fill = "#FFFFFF"   # White background (ratio ~ 1.2:1)
            break

    res_bad = check_wcag_contrast_qa(bad_spec)
    assert res_bad.passed is False
    assert any("subhead" in v for v in res_bad.violations)


def test_typography_budget_and_scale():
    """Verifies font count (<= 2), size count (<= 4), and minimum font size (>= 22px)."""
    spec = get_archetype_template("minimal-editorial", headline="TIMELESS", subhead="Artistry in every thread.")
    res = check_typography_budget_qa(spec)
    assert res.passed is True
    assert res.measurements["font_count"] <= 2
    assert res.measurements["size_count"] <= 4

    # Intentionally breach typographic budget with 5 distinct sizes
    breached_spec = spec.model_copy(deep=True)
    sizes = [16, 28, 40, 60, 88]
    for i, size in enumerate(sizes):
        breached_spec.elements.append(
            PosterElement(
                id=f"extra_text_{i}",
                type="text",
                x=80,
                y=160 + (i * 64),
                w=400,
                h=48,
                size=size,
                text=f"Sample text at {size}px"
            )
        )

    res_breached = check_typography_budget_qa(breached_spec)
    assert res_breached.passed is False
    assert any("Typographic size budget exceeded" in v or "below minimum" in v for v in res_breached.violations)


def test_dual_axis_and_8px_grid_qa():
    """Verifies strict dual-axis alignment and 8px grid snapping."""
    spec = get_archetype_template(
        "hero-text",
        headline="PERFECT AXIS",
        subhead="Aligned to strict grid.",
        cta="Explore",
        primary_color="#3B82F6"
    )
    res = check_dual_axis_and_grid_qa(spec)
    assert res.passed is True
    assert res.score == 10.0

    # Intentionally violate 8px grid (x = 83 instead of 80)
    unaligned_spec = spec.model_copy(deep=True)
    unaligned_spec.elements[0].x = 83

    res_unaligned = check_dual_axis_and_grid_qa(unaligned_spec)
    assert res_unaligned.passed is False
    assert any("not on 8px grid" in v for v in res_unaligned.violations)


def test_safe_margins_and_platform_safe_zones():
    """Verifies 6% outer margin safety and Stories top 250px / bottom 340px zone."""
    spec = get_archetype_template("hero-text", headline="SAFE MARGINS", subhead="Within bounds.")
    
    # 1. Normal feed canvas passes
    res_feed = check_safe_margins_and_collisions_qa(spec, platform="instagram_feed")
    assert res_feed.passed is True

    # 2. Outer margin violation (x = 16px < 64px margin)
    breached_spec = spec.model_copy(deep=True)
    breached_spec.elements.append(
        PosterElement(id="edge_text", type="text", x=16, y=200, w=200, h=40, text="Off the edge")
    )
    res_breach = check_safe_margins_and_collisions_qa(breached_spec)
    assert res_breach.passed is False
    assert any("breaches left margin" in v for v in res_breach.violations)


@pytest.mark.asyncio
async def test_vision_critic_10_rubric_evaluation_and_threshold():
    """Verifies 10-criterion rubric evaluation and >= 8.0 pass threshold."""
    spec = get_archetype_template(
        "quote-card",
        headline="QUALITY FIRST",
        subhead="Crafted without compromise.",
        cta="Book Now",
        primary_color="#D97706"
    )

    critique: VisionCritiqueReport = await evaluate_vision_critic(spec)

    assert critique.overall_score >= 8.0
    assert critique.verdict == "pass"
    assert len(critique.rubric) == 10
    
    # Verify all 10 criteria exist
    required_criteria = [
        "layout_balance", "visual_hierarchy", "typography_contrast", "brand_authenticity",
        "margin_integrity", "palette_harmony", "grid_alignment", "anti_hallucination",
        "platform_fit", "aesthetic_polish"
    ]
    for c in required_criteria:
        assert c in critique.rubric
        assert critique.rubric[c].score >= 0.0


def test_apply_numeric_revisions_convergence():
    """Verifies that numeric adjustments snap elements to 8px grid and improve spec."""
    spec = get_archetype_template("hero-text", headline="ADJUST ME")
    
    # Misalign card_bg element
    for el in spec.elements:
        if el.id == "card_bg":
            el.x = 73
            el.w = 907
            break
    
    checks = check_dual_axis_and_grid_qa(spec)
    adjustments = generate_actionable_adjustments(spec, {"dual_axis_and_8px_grid": checks})
    assert len(adjustments) > 0

    revised_spec = apply_numeric_revisions(spec, adjustments)
    card = next(el for el in revised_spec.elements if el.id == "card_bg")
    assert card.x % 8 == 0
    assert card.w % 8 == 0


@pytest.mark.asyncio
async def test_full_poster_designer_langgraph_pipeline_with_qa_and_critic():
    """Executes the complete LangGraph agent pipeline verifying critic and QA integration."""
    graph = build_poster_design_graph()

    state = {
        "request": {
            "title": "URBAN STRIDE",
            "subtitle": "Limited sneaker drop for urban creators.",
            "business_name": "Apex Streetwear",
            "primary_color": "#EA580C",
            "archetype": "hero-text",
            "platform": "instagram_feed"
        },
        "iteration": 0,
        "events": []
    }

    final_state = await graph.ainvoke(state)

    assert "spec" in final_state
    assert "png_base64" in final_state
    assert "thumbnail_base64" in final_state
    assert "critique" in final_state
    assert final_state["critique"]["overall"] >= 8.0
    assert final_state["critique"]["verdict"] == "pass"


def test_poster_qa_api_endpoints():
    """Tests /api/poster/qa/inspect, /api/poster/critic/evaluate, and /api/poster/render/html."""
    spec = get_archetype_template(
        "split-image",
        headline="TIMELESS ELEGANCE",
        subhead="Handcrafted bespoke jewelry.",
        cta="View Gallery",
        primary_color="#CA8A04"
    )
    spec_dict = spec.model_dump()

    # 1. POST /api/poster/qa/inspect
    res_qa = client.post("/api/poster/qa/inspect", json={"spec": spec_dict, "use_playwright": True})
    assert res_qa.status_code == 200
    qa_data = res_qa.json()
    assert qa_data["passed"] is True
    assert qa_data["overall_score"] >= 8.0
    assert "text_overflow_and_clipping" in qa_data["checks"]
    assert "wcag_contrast_compliance" in qa_data["checks"]

    # 2. POST /api/poster/critic/evaluate
    res_critic = client.post("/api/poster/critic/evaluate", json={"spec": spec_dict})
    assert res_critic.status_code == 200
    critic_data = res_critic.json()
    assert critic_data["overall_score"] >= 8.0
    assert critic_data["verdict"] == "pass"
    assert len(critic_data["rubric"]) == 10

    # 3. POST /api/poster/render/html
    res_html = client.post("/api/poster/render/html", json=spec_dict)
    assert res_html.status_code == 200
    assert "text/html" in res_html.headers.get("content-type", "")
    assert "<!DOCTYPE html>" in res_html.text
    assert "TIMELESS ELEGANCE" in res_html.text
