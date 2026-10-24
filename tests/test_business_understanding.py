"""Comprehensive automated test suite for Phase 3: Business Understanding & Creative Direction.

Verifies:
1. 14-Vertical taxonomy resolution (sneakers, salon, clinic, real estate, gym, tech, etc.).
2. Zero coffee cross-contamination for non-coffee businesses.
3. Dynamic CreativeDirection generation respecting custom brand tokens and guardrails.
4. Lexical and visual contamination guard detecting and cleaning inappropriate terms and motifs.
5. Poster rendering for non-coffee businesses with 0 steam or coffee copy injection.
6. API endpoints GET /api/creative-direction and POST /api/creative-direction/regenerate.
"""
import pytest
from app.services.creative_direction import (
    resolve_vertical,
    build_creative_direction,
    VERTICAL_CATALOG
)
from app.agents.business_understanding import BusinessUnderstandingAgent, analyze_business_profile
from app.services.poster.contamination_guard import (
    check_copy_contamination,
    clean_copy_of_contamination,
    validate_poster_spec_contamination
)
from app.services.poster.renderer import render_poster_spec
from app.services.poster.archetypes import get_archetype_template
from app.agents.poster_designer import tighten_poster_copy


def test_14_vertical_resolution_taxonomy():
    """Verify that diverse industries resolve strictly to their matching vertical, never coffee."""
    test_cases = [
        ("Retail", "Sneakers", "Kicks Vault", "sneakers_streetwear"),
        ("Beauty", "Hair & Nails", "Luxe Glow Salon", "salon_spa"),
        ("Healthcare", "Dental Care", "Metro Smiles Dental Clinic", "clinic_healthcare"),
        ("Real Estate", "Luxury Homes", "Vanguard Realty Group", "real_estate"),
        ("Fitness", "Crossfit", "Iron Titan Gym & Athletics", "gym_fitness"),
        ("Fashion", "Designer Boutique", "Aura Couture Atelier", "boutique_fashion"),
        ("Jewelry", "Watches", "Crown Jewelers & Chronographs", "jewelry_luxury"),
        ("Education", "Tutoring", "Apex Learning Academy", "education_tutoring"),
        ("Technology", "Cloud SaaS", "VectorFlow Developer Tools", "tech_saas"),
        ("Automotive", "Detailing", "Ceramic Pro Auto Finish", "auto_detail"),
        ("Hospitality", "Resort", "Azure Island Villas & Travel", "travel_hospitality"),
        ("Events", "Weddings", "Royal Blossom Wedding Venues", "event_wedding"),
        ("Services", "Plumbing", "Reliable 24/7 Home Plumbing", "local_services"),
        ("Food & Beverage", "Roastery", "Artisan Coffee Roasters", "cafe_coffee")
    ]

    for prim, sub, name, expected_vert in test_cases:
        res = resolve_vertical(prim, sub, name)
        assert res == expected_vert, f"Expected {expected_vert} for {name}, got {res}"

    # General / Ambiguous businesses must NEVER default to coffee
    assert resolve_vertical("General Consulting", "", "Summit Partners") != "cafe_coffee"
    assert resolve_vertical("", "", "Modern Solutions") == "local_services"


def test_sneaker_store_creative_direction_generation():
    """Verify that a sneaker business receives bold streetwear styling and zero coffee leakage."""
    profile = {
        "business_name": "Apex Kicks",
        "industry_primary": "Retail",
        "industry_sub": "Sneakers & Streetwear",
        "category": "Sneakers",
        "primary_color": "#FF3366",
        "personality_json": {"tone": "urgent, drop-centric, bold"}
    }
    offerings = [{"name": "Retro High OG", "description": "Limited silhouette drop"}]

    cd = analyze_business_profile(profile, offerings)
    assert cd.vertical == "sneakers_streetwear"
    assert cd.style_family == "streetwear_bold"
    assert cd.typography.display_font == "Syne"
    assert "drop" in cd.brand_keywords
    assert "coffee" in cd.disallowed_terms
    assert "espresso" in cd.disallowed_terms
    assert "single-origin" in cd.disallowed_terms
    assert cd.palette.primary == "#FF3366"


def test_dental_clinic_creative_direction_generation():
    """Verify that a clinic business receives clinical authority and strict medical truth policy."""
    profile = {
        "business_name": "Family Smiles Dental",
        "industry_primary": "Healthcare",
        "industry_sub": "Dental Clinic",
        "primary_color": "#0284C7"
    }

    cd = analyze_business_profile(profile)
    assert cd.vertical == "clinic_healthcare"
    assert cd.style_family == "clinical_pristine_authoritative"
    assert cd.claims_policy == "strict_medical_truth_zero_false_guarantees"
    assert "coffee" in cd.disallowed_terms
    assert "sneaker" in cd.disallowed_terms


def test_contamination_guard_lexical_checks():
    """Verify contamination guard detects cross-industry contaminated words and cleans them."""
    # 1. Sneaker vertical containing coffee words
    bad_sneaker_copy = "Exclusive drop with single-origin cold brew aroma"
    is_clean, violations = check_copy_contamination(bad_sneaker_copy, "sneakers_streetwear")
    assert is_clean is False
    assert any("cold brew" in v or "single-origin" in v for v in violations)

    cleaned = clean_copy_of_contamination(bad_sneaker_copy, "sneakers_streetwear", fallback="Exclusive drop")
    assert "cold brew" not in cleaned.lower()
    assert "single-origin" not in cleaned.lower()
    assert "Exclusive drop" in cleaned

    # 2. Dental vertical containing sneaker words
    bad_dental_copy = "Get your fresh kicks and orthodontic smile drop"
    is_clean, violations = check_copy_contamination(bad_dental_copy, "clinic_healthcare")
    assert is_clean is False
    assert any("kicks" in v or "drop" in v for v in violations)

    # 3. Coffee vertical allows coffee words
    good_coffee_copy = "Single-origin cold brew roasted slow"
    is_clean, violations = check_copy_contamination(good_coffee_copy, "cafe_coffee")
    assert is_clean is True


def test_contamination_guard_spec_validation():
    """Verify contamination guard flags invalid shapes/patterns like coffee steam on non-coffee designs."""
    bad_sneaker_spec = {
        "elements": [
            {"id": "headline", "text": "Limited Sneaker Drop"},
            {"id": "subhead", "text": "A guided single-origin tasting"}
        ],
        "patterns": ["coffee_steam", "diagonal_slashes"]
    }
    is_clean, violations = validate_poster_spec_contamination(bad_sneaker_spec, "sneakers_streetwear")
    assert is_clean is False
    assert any("single-origin" in v for v in violations)
    assert any("coffee_steam" in v or "coffee motif" in v for v in violations)


def test_poster_tightening_and_rendering_for_sneaker_store():
    """Verify that a sneaker store poster never renders coffee copy or steam lines."""
    b_name = "Kicks Vault"
    raw_brief = {
        "headline": "The Next Silhouette Drop Is Here Today",
        "subhead": "",
        "cta": "",
        "eyebrow": "",
        "badge": ""
    }

    tightened = tighten_poster_copy(raw_brief, business_name=b_name)
    assert "COLD BREW" not in tightened["eyebrow"]
    assert "TASTING" not in tightened["badge"]
    assert "single-origin" not in tightened["subhead"].lower()
    assert tightened["cta"] == "Learn More"

    # Render template spec
    spec = get_archetype_template(
        archetype="hero-text",
        headline=tightened["headline"],
        subhead=tightened["subhead"],
        primary_color="#FF3366",
        business_name=b_name
    )
    result = render_poster_spec(spec)
    assert result.png_base64 is not None
    assert len(result.png_base64) > 100


def test_creative_direction_api_endpoints(tmp_path):
    """Verify GET /api/creative-direction and POST /api/creative-direction/regenerate."""
    from starlette.testclient import TestClient
    from app.main import app
    from app.db.migrations import run_migrations
    from app.security.auth import create_jwt, AuthenticatedUser
    import app.main as app_main

    old_db = app_main.DB_PATH
    try:
        test_db = str(tmp_path / "test_cd_api.db")
        run_migrations(test_db)
        app_main.DB_PATH = test_db

        client = TestClient(app)

        # 1. Unauthenticated request rejected
        resp = client.get("/api/creative-direction")
        assert resp.status_code == 401

        # 2. Authenticated user without profile gets 404
        user = AuthenticatedUser(user_id="user_cd_test", email="cd_test@brand.local", tenant_id="cd_test_tenant")
        token = create_jwt(user)
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.get("/api/creative-direction", headers=headers)
        assert resp.status_code == 404

        # 3. Save a salon profile
        profile_data = {
            "business_name": "Velvet & Silk Spa",
            "industry_primary": "Beauty & Wellness",
            "industry_sub": "Salon & Day Spa",
            "category": "Spa",
            "primary_color": "#C29B7F",
            "personality_json": {"tone": "serene, mindful luxury"}
        }
        save_resp = client.post("/api/profile", json=profile_data, headers=headers)
        assert save_resp.status_code == 200
        assert "creative_direction" in save_resp.json()["profile"]

        # 4. GET /api/creative-direction returns salon direction
        cd_resp = client.get("/api/creative-direction", headers=headers)
        assert cd_resp.status_code == 200
        cd_data = cd_resp.json()
        assert cd_data["vertical"] == "salon_spa"
        assert cd_data["style_family"] == "editorial_minimal_refined"
        assert "coffee" in cd_data["disallowed_terms"]

        # 5. POST /api/creative-direction/regenerate works
        regen_resp = client.post("/api/creative-direction/regenerate", headers=headers)
        assert regen_resp.status_code == 200
        assert regen_resp.json()["creative_direction"]["vertical"] == "salon_spa"
    finally:
        app_main.DB_PATH = old_db
