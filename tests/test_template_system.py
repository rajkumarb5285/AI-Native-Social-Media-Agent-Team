"""Comprehensive Test Suite for Phase 4: 30 Templates & Diversified Template Selector.

Verifies:
1. Catalog Completeness: exactly 10 archetypes, 3 variants each = 30 templates total.
2. Linter Cleanliness: all 30 templates generate valid, WCAG-compliant, 8px-grid PosterSpecs without blockers.
3. Diverse Candidate Selection: top 3 candidates strictly span 3 different archetypes.
4. Repetition Penalty: recent_archetypes are strongly penalized to prevent consecutive repetition.
5. Client Photo Prioritization: has_client_photos=True boosts cutout-ready templates.
6. Vertical Sensitivity: sneaker store vs dental clinic vs coffee shop receive distinct candidates.
7. API Endpoints: /api/poster/templates, /api/poster/archetypes, /api/poster/candidates.
"""
import pytest
from starlette.testclient import TestClient

from app.main import app
from app.services.poster.templates_catalog import (
    TEMPLATES_CATALOG, ARCHETYPES_CATALOG, TEMPLATE_BY_ID, TEMPLATES_BY_ARCHETYPE
)
from app.services.poster.archetypes import get_archetype_template
from app.services.poster.linter import lint_poster_spec
from app.services.poster.template_selector import template_selector, TemplateSelector


def test_30_templates_catalog_completeness():
    """Verify that exactly 30 templates exist across 10 archetypes with 3 variants each."""
    assert len(TEMPLATES_CATALOG) == 30
    assert len(ARCHETYPES_CATALOG) == 10

    # Verify each archetype has exactly 3 variants
    for arch_id, arch_meta in ARCHETYPES_CATALOG.items():
        variants = arch_meta["variants"]
        assert len(variants) == 3, f"Archetype {arch_id} must have 3 variants, found {len(variants)}"
        matching_templates = TEMPLATES_BY_ARCHETYPE.get(arch_id, [])
        assert len(matching_templates) == 3, f"Archetype {arch_id} missing templates"


def test_all_30_templates_compile_and_pass_lint():
    """Verify that every one of the 30 templates produces a lint-clean PosterSpec."""
    for template in TEMPLATES_CATALOG:
        spec = get_archetype_template(
            archetype=template.id,
            headline=f"Premium Innovation for {template.name}",
            subhead="Crafted with architectural precision and verified quality standards.",
            primary_color=template.preview_palette.get("primary", "#6366F1"),
            bg_color=template.preview_palette.get("bg", "#0B0F19"),
            cta="Explore Now",
            business_name="Acme Enterprise"
        )
        assert spec is not None
        report = lint_poster_spec(spec)
        assert report.clean is True, (
            f"Template {template.id} ({template.archetype}) failed linter with blockers: {report.blockers}"
        )


def test_template_selector_scoring_and_diversity():
    """Verify that select_candidates returns top 3 candidates from 3 DIFFERENT archetypes."""
    candidates = template_selector.select_candidates(
        vertical="sneakers_streetwear",
        goal="product_launch",
        has_client_photos=True,
        recent_archetypes=[]
    )
    assert len(candidates) == 3

    # Diversity rule: Candidate archetypes must be unique
    archetypes = [c.archetype for c in candidates]
    assert len(set(archetypes)) == 3, f"Candidates must span 3 distinct archetypes, got {archetypes}"

    # Scores must be ordered descending
    assert candidates[0].score >= candidates[1].score >= candidates[2].score


def test_diversity_enforcement_penalizes_recent_archetypes():
    """Verify that recent archetypes are penalized to prevent consecutive repetition."""
    # When product-cutout was just published
    candidates_with_history = template_selector.select_candidates(
        vertical="sneakers_streetwear",
        goal="product_launch",
        has_client_photos=True,
        recent_archetypes=["product-cutout"]
    )

    # Product cutout should NOT be the top candidate due to -50 repetition penalty
    assert candidates_with_history[0].archetype != "product-cutout"


def test_client_photos_priority_boosts_cutout_templates():
    """Verify that having client photos prioritizes cutout-ready templates."""
    candidates_with_photos = template_selector.select_candidates(
        vertical="sneakers_streetwear",
        goal="product_launch",
        has_client_photos=True,
        recent_archetypes=[]
    )
    # The top candidate should support photo cutouts
    assert candidates_with_photos[0].supports_photo_cutout is True
    assert candidates_with_photos[0].archetype in ("product-cutout", "split-image-text")


def test_vertical_sensitivity_selection():
    """Verify that different verticals receive tailored candidates."""
    sneaker_candidates = template_selector.select_candidates(
        vertical="sneakers_streetwear",
        goal="brand_awareness"
    )
    clinic_candidates = template_selector.select_candidates(
        vertical="clinic_healthcare",
        goal="brand_awareness"
    )

    sneaker_archetypes = {c.archetype for c in sneaker_candidates}
    clinic_archetypes = {c.archetype for c in clinic_candidates}

    # Healthcare clinic should prioritize clinical proof / editorial, not hype cutouts
    assert "stats-metric" in clinic_archetypes or "quote-card" in clinic_archetypes or "minimal-editorial" in clinic_archetypes
    # Sneaker store and healthcare clinic shouldn't have identical candidate lists
    assert sneaker_candidates[0].template_id != clinic_candidates[0].template_id


def test_template_api_endpoints():
    """Verify HTTP endpoints for templates, archetypes, and candidates."""
    client = TestClient(app)

    # 1. GET /api/poster/templates
    t_resp = client.get("/api/poster/templates")
    assert t_resp.status_code == 200
    t_data = t_resp.json()
    assert t_data["count"] == 30
    assert len(t_data["templates"]) == 30

    # 2. GET /api/poster/archetypes
    a_resp = client.get("/api/poster/archetypes")
    assert a_resp.status_code == 200
    a_data = a_resp.json()
    assert a_data["count"] == 10
    arch_ids = [a["id"] for a in a_data["archetypes"]]
    assert "product-cutout" in arch_ids
    assert "grid-multi-item" in arch_ids
    assert "stats-metric" in arch_ids

    # 3. POST /api/poster/candidates
    c_resp = client.post("/api/poster/candidates", json={
        "vertical": "gym_fitness",
        "goal": "promotion",
        "has_client_photos": True,
        "recent_archetypes": ["offer-burst"]
    })
    assert c_resp.status_code == 200
    c_data = c_resp.json()
    assert c_data["count"] == 3
    cand_archetypes = [c["archetype"] for c in c_data["candidates"]]
    assert len(set(cand_archetypes)) == 3
    # Offer burst should not be candidate #1 because it was recently used
    assert cand_archetypes[0] != "offer-burst"
