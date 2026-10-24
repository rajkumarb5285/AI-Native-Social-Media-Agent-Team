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
