"""Unit tests for Poster Design Agent Foundation: Spec, Linter, and Renderer."""
import pytest
from app.services.poster.spec import (
    PosterSpec, CanvasConfig, BackgroundConfig, FontsConfig, PosterElement
)
from app.services.poster.linter import lint_poster_spec, contrast_ratio
from app.services.poster.renderer import render_poster_spec
from app.services.poster.archetypes import (
    create_hero_text_spec,
    create_centered_badge_spec,
    create_offer_burst_spec,
    create_quote_card_spec,
    get_archetype_template
)


def test_wcag_contrast_calculation():
    """Verify WCAG 2.2 contrast ratio math matches official standards."""
    # Black on white should be 21:1
    bw = contrast_ratio("#000000", "#FFFFFF")
    assert bw >= 20.0

    # White on dark navy
    navy = contrast_ratio("#FFFFFF", "#0B0F19")
    assert navy >= 14.0

    # Low contrast should fail
    low = contrast_ratio("#777777", "#888888")
    assert low < 3.0


def test_hero_text_archetype_lint_clean():
    """Verify default hero-text archetype passes all linter checks."""
    spec = create_hero_text_spec()
    report = lint_poster_spec(spec)
    assert report.clean is True
    assert len(report.blockers) == 0


def test_centered_badge_archetype_lint_clean():
    """Verify centered-badge festival archetype passes all linter checks."""
    spec = create_centered_badge_spec()
    report = lint_poster_spec(spec)
    assert report.clean is True
    assert len(report.blockers) == 0


def test_offer_burst_archetype_lint_clean():
    """Verify offer-burst archetype passes all linter checks."""
    spec = create_offer_burst_spec()
    report = lint_poster_spec(spec)
    assert report.clean is True
    assert len(report.blockers) == 0


def test_quote_card_archetype_lint_clean():
    """Verify quote-card archetype passes all linter checks."""
    spec = create_quote_card_spec()
    report = lint_poster_spec(spec)
    assert report.clean is True
    assert len(report.blockers) == 0


def test_linter_blocks_margin_violation():
    """Linter must block elements placed inside the 6% outer margin."""
    spec = create_hero_text_spec()
    # Breach left margin: x = 16 (margin is 64)
    spec.elements[0].x = 16
    report = lint_poster_spec(spec)
    assert report.clean is False
    assert any("outer margin" in b for b in report.blockers)


def test_linter_blocks_contrast_failure():
    """Linter must block text with insufficient WCAG contrast."""
    spec = create_hero_text_spec()
    # Set text color almost same as background
    spec.elements[1].color = "#1E293B"  # Dark gray on #0B0F19
    report = lint_poster_spec(spec)
    assert report.clean is False
    assert any("Contrast violation" in b for b in report.blockers)


def test_linter_blocks_text_collision():
    """Linter must block non-decorative elements that overlap."""
    spec = create_hero_text_spec()
    # Force headline and subhead to occupy the exact same rectangle
    spec.elements[1].y = 568
    spec.elements[1].h = 140
    report = lint_poster_spec(spec)
    assert report.clean is False
    assert any("Text collision" in b for b in report.blockers)


def test_linter_blocks_fabricated_honesty_claims():
    """Linter must block invented ratings or 'No.1' claims not in the brief."""
    spec = create_hero_text_spec()
    spec.elements[1].text = "We are the No.1 Rated Agency ★★★★★"
    report = lint_poster_spec(spec, brief={"headline": "Growth marketing"})
    assert report.clean is False
    assert any("Honesty violation" in b for b in report.blockers)


def test_deterministic_renderer_outputs_png_and_thumbnail():
    """Renderer must output valid PNG bytes, 200px thumbnail, and base64 strings."""
    spec = create_hero_text_spec()
    result = render_poster_spec(spec)

    assert result.width == 1080
    assert result.height == 1350
    assert len(result.png_bytes) > 1000
    assert len(result.thumbnail_bytes) > 500
    assert result.png_base64.startswith("data:image/png;base64,")
    assert result.thumbnail_base64.startswith("data:image/png;base64,")
    assert "<svg" in result.svg_content


def test_get_archetype_template_helper():
    """Verify template selector maps genres to the correct archetype."""
    fest = get_archetype_template("festival", "Happy Diwali", "Celebration offer")
    assert fest.focal_element == "badge_circle"

    offer = get_archetype_template("offer", "Huge Summer Sale")
    assert offer.focal_element == "burst_text"

    quote = get_archetype_template("quote", "Outstanding work and results")
    assert quote.focal_element == "quote_text"


@pytest.mark.asyncio
async def test_poster_design_langgraph_pipeline_execution():
    """Verify Poster Design Agent LangGraph pipeline executes all nodes end-to-end."""
    from app.agents.poster_designer import poster_design_agent

    initial_state = {
        "request": {
            "title": "Grand Diwali Gold Festival",
            "subtitle": "Flat 25% Off Making Charges on Diamond Jewellery",
            "business_name": "Royal Jewellers",
            "cta": "Visit Showroom",
            "primary_color": "#F59E0B"
        }
    }

    final_state = await poster_design_agent.ainvoke(initial_state)

    assert "png_base64" in final_state
    assert final_state["png_base64"].startswith("data:image/png;base64,")
    assert "spec" in final_state
    assert "critique" in final_state
    assert final_state["critique"]["overall"] >= 8.0
    assert final_state["lint"]["clean"] is True


def test_phase_4_knowledge_rule_cards_and_cultural_festivals():
    """Verify Phase 4 atomic rule cards and cultural festival dictionary."""
    from app.services.poster.knowledge import (
        search_rule_cards, get_cultural_rules, get_reference_briefs_by_type
    )

    # Search rule cards
    contrast_rules = search_rule_cards("contrast WCAG")
    assert len(contrast_rules) > 0
    assert any(r.id == "RULE-CONTRAST-4.5" for r in contrast_rules)

    # Cultural festival rules for Diwali
    diwali = get_cultural_rules("Diwali Dhamaka")
    assert diwali is not None
    assert diwali.name == "Diwali (Deepavali)"
    assert any("diya" in m for m in diwali.authentic_motifs)
    assert len(diwali.taboos) > 0

    # Reference briefs
    briefs = get_reference_briefs_by_type("offer_promo")
    assert len(briefs) > 0


def test_phase_5_background_prompt_and_scrim_compositor():
    """Verify Phase 5 negative-space background prompt and scrim compositing."""
    from app.services.poster.image_gen import (
        formulate_background_prompt, apply_scrim_overlay
    )
    from app.services.poster.spec import OverlayScrim
    from PIL import Image

    # Negative-space prompt formulation
    res = formulate_background_prompt(
        concept="Luxury watch product poster",
        archetype="hero-text",
        subject="mechanical chronograph",
        tone="minimalist elegance"
    )
    assert "text" in res.negative_prompt
    assert "words" in res.negative_prompt
    assert "clean" in res.positive_prompt.lower()

    # Scrim overlay
    canvas = Image.new("RGB", (200, 200), (255, 255, 255))
    scrim = OverlayScrim(enabled=True, type="solid", color="#000000", opacity=0.5)
    composited = apply_scrim_overlay(canvas, scrim)
    # The middle pixel should be darkened
    r, g, b = composited.getpixel((100, 100))
    assert r < 200 and g < 200 and b < 200


def test_phase_6_telemetry_and_learning_loop(tmp_path):
    """Verify Phase 6 telemetry logging, human sign-off, and fine-tuning dataset export."""
    from app.services.poster.telemetry import (
        log_poster_generation, record_human_feedback, export_training_dataset
    )

    test_db = str(tmp_path / "test_agent_runs.db")

    run_id = log_poster_generation(
        brief={"headline": "Special Offer"},
        archetype="hero-text",
        initial_spec={"elements": []},
        final_spec={"elements": [{"id": "headline", "x": 64, "y": 64}]},
        scores={"overall": 8.8, "hierarchy": 9},
        iterations=1,
        verdict="pass",
        db_path=test_db
    )
    assert run_id.startswith("post_")

    # Record human approval
    success = record_human_feedback(run_id, "approved", db_path=test_db)
    assert success is True

    # Export dataset
    dataset = export_training_dataset(db_path=test_db, min_score=8.0, only_approved=True)
    assert len(dataset) == 1
    assert dataset[0]["id"] == run_id
    assert dataset[0]["human_status"] == "approved"


def test_poster_v3_copy_validator_and_smart_typography():
    """Verify Poster v3 strict copy validation and curly apostrophe preservation."""
    from app.services.poster.spec import PosterCopy, smart_typography
    import pytest

    # Smart typography
    res = smart_typography("Rajkumar's Coffee Studio")
    assert "Rajkumar’s" in res
    assert "’" in res

    # Valid copy
    valid_copy = PosterCopy(
        eyebrow="SINGLE-ORIGIN COLD BREW",
        headline="One origin. One slow pour.",
        subline="A guided tasting at Rajkumar’s Coffee Studio",
        cta="Reserve a seat",
        badge="TASTING SESSION"
    )
    assert valid_copy.cta == "Reserve a seat"

    # Reject headline > 6 words
    with pytest.raises(ValueError, match="headline > 6 words"):
        PosterCopy(
            eyebrow="TAG",
            headline="Experience the Future of Coffee at Rajkumar's Coffee Studio",
            subline="Short subline",
            cta="Reserve seat",
            badge="BADGE"
        )

    # Reject subline > 44 characters or containing '!'
    with pytest.raises(ValueError, match="subline too long"):
        PosterCopy(
            eyebrow="TAG",
            headline="Cold Brew",
            subline="Sip the future of coffee at Rajkumar's Coffee Studio with visionary thinking and craftsmanship",
            cta="Reserve",
            badge="BADGE"
        )

    # Reject CTA > 3 words
    with pytest.raises(ValueError, match="cta > 3 words"):
        PosterCopy(
            eyebrow="TAG",
            headline="Cold Brew",
            subline="A guided tasting session.",
            cta="Reserve your tasting seat today",
            badge="BADGE"
        )

    # Reject unverified claims
    with pytest.raises(ValueError, match="unverified claim"):
        PosterCopy(
            eyebrow="TAG",
            headline="Cold Brew",
            subline="Limited spots available for tasting",
            cta="Book Now",
            badge="BADGE"
        )


def test_poster_v3_coffee_poster_alignment_and_geometry():
    """Verify coffee poster renders with Poster v3 Alignment Masterclass geometry and 0 QA errors."""
    from app.agents.poster_designer import tighten_poster_copy
    from app.services.poster.archetypes import get_archetype_template
    from app.services.poster.renderer import render_poster_spec

    # User's input that previously failed
    raw_title = "Experience the Future of Coffee: Single Origin Cold Brew at Rajkumar's Coffee"
    raw_subtitle = "Sip the future of coffee! At Rajkumar's Coffee Studio we blend visionary thinking with the meticulous art of single"
    raw_cta = "Reserve your tasting seat today - limited spots available."
    b_name = "Rajkumar's Coffee Studio"

    # Step 1: Tighten copy
    tightened = tighten_poster_copy({
        "headline": raw_title,
        "subhead": raw_subtitle,
        "cta": raw_cta,
        "eyebrow": "SINGLE-ORIGIN COLD BREW",
        "badge": "TASTING SESSION"
    }, business_name=b_name)

    assert len(tightened["headline"].split()) <= 6
    assert len(tightened["subhead"]) <= 44
    assert len(tightened["cta"].split()) <= 3
    assert "’" in tightened["subhead"]
    assert "!" not in tightened["subhead"]

    # Step 2: Render spec
    spec = get_archetype_template(
        archetype="hero-text",
        headline=tightened["headline"],
        subhead=tightened["subhead"],
        primary_color="#E8890C",
        cta=tightened["cta"],
        business_name=b_name
    )

    result = render_poster_spec(spec)
    assert result.width == 1080
    assert result.height == 1350
    assert result.measurements.get("status") == "poster_v3_alignment_masterclass_passed"
    assert len(result.measurements.get("qa_errors", [])) == 0
    assert result.measurements.get("header_midline_y") == 104
    assert result.measurements.get("footer_midline_y") == 1230


