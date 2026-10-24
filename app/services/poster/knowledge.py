"""Phase 4: Poster Design Knowledge Base & Cultural Add-On.

Implements Section 4 & Section 8.2 of the Poster Design Agent specification:
- Atomic Rule Cards catalog (design rules, typography, grid, platform constraints)
- Prompt 8: Cultural and Festival motif dictionary with authentic motifs, palettes, and taboo checks
- 30 Curated Reference Briefs across industries and archetypes
- Keyword/semantic search interfaces for RAG integration into the LangGraph pipeline
"""
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class RuleCard(BaseModel):
    id: str
    category: str
    title: str
    rule: str
    rationale: str
    severity: str  # blocker | warning | recommendation


class CulturalFestivalRule(BaseModel):
    id: str
    name: str
    culture: str
    traditional_season: str
    authentic_motifs: List[str]
    palette: Dict[str, str]
    typography_recommendation: Dict[str, str]
    taboos: List[str]
    greeting_formats: List[str]


# ---------------------------------------------------------------------------
# Atomic Rule Cards (Section 4 & 6.3)
# ---------------------------------------------------------------------------

RULE_CARDS: List[RuleCard] = [
    RuleCard(
        id="RULE-CONTRAST-4.5",
        category="legibility",
        title="WCAG 2.2 AA Contrast Ratio",
        rule="Text on background must achieve at least 4.5:1 contrast ratio (3:1 for text 24px and larger).",
        rationale="Guarantees legibility on small phone screens under outdoor sunlight.",
        severity="blocker"
    ),
    RuleCard(
        id="RULE-GRID-8PX",
        category="alignment",
        title="8px Base Grid Multiples",
        rule="Every coordinate (x, y, w, h), margin, and padding must be an exact integer multiple of 8px.",
        rationale="Maintains proportional visual rhythm across all screen resolutions.",
        severity="blocker"
    ),
    RuleCard(
        id="RULE-MARGIN-6PCT",
        category="spacing",
        title="6% Outer Safe Margin",
        rule="No critical content may breach the 6% outer margin (64px on 1080px canvas).",
        rationale="Prevents visual tension and accidental clipping across different device bezels.",
        severity="blocker"
    ),
    RuleCard(
        id="RULE-STORIES-SAFE-ZONE",
        category="platform_fit",
        title="Instagram Stories & Reels Safe Zones",
        rule="On 9:16 canvases, keep critical text out of top 250px (profile UI) and bottom 340px (reply UI).",
        rationale="Platform overlays conceal headline or CTA if placed in extreme vertical edges.",
        severity="blocker"
    ),
    RuleCard(
        id="RULE-TYPE-BUDGET",
        category="typography",
        title="Strict Typographic Scale Budget",
        rule="Use at most 2 font families (1 display, 1 body) and at most 4 distinct font sizes.",
        rationale="Avoids visual clutter and establishes clear scanning hierarchy.",
        severity="blocker"
    ),
    RuleCard(
        id="RULE-HONESTY-ZERO-HALLUCINATION",
        category="honesty",
        title="Zero Hallucination Honesty Rule",
        rule="Never invent star ratings, reviews, discounts, dates, certifications, or partner logos not in the brief.",
        rationale="Prevents regulatory compliance liabilities and false advertising for businesses.",
        severity="blocker"
    ),
    RuleCard(
        id="RULE-COLOR-60-30-10",
        category="colour",
        title="60-30-10 Color Harmonization",
        rule="Palette: 60% dominant neutral/background, 30% structural surface, 10% high-contrast accent for CTA.",
        rationale="Ensures the eye lands immediately on the single call-to-action.",
        severity="warning"
    ),
    RuleCard(
        id="RULE-LINE-LENGTH-MEASURE",
        category="typography",
        title="Line Length Reading Comfort",
        rule="Headline lines 12-28 characters; body lines 35-45 characters. Never exceed 50 characters per line.",
        rationale="Optimizes ocular saccade speed on mobile displays.",
        severity="warning"
    )
]


# ---------------------------------------------------------------------------
# Prompt 8: Cultural and Festival Knowledge Pack
# ---------------------------------------------------------------------------

CULTURAL_FESTIVALS: Dict[str, CulturalFestivalRule] = {
    "diwali": CulturalFestivalRule(
        id="diwali",
        name="Diwali (Deepavali)",
        culture="Indian / Hindu / Jain / Sikh",
        traditional_season="October - November",
        authentic_motifs=["diya (oil lamp)", "warm rangoli patterns", "marigold flowers", "gold foil sparks"],
        palette={
            "background": "#0B0712",
            "surface": "#2B1638",
            "primary": "#FFF7ED",
            "muted": "#FBBF24",
            "accent": "#F59E0B"
        },
        typography_recommendation={"display": "Playfair Display", "text": "Inter"},
        taboos=[
            "Never use sacred deity images as cut-outs for discount percentage badges.",
            "Do not depict meat, poultry, or alcohol alongside auspicious Diwali blessings.",
            "Avoid neon techno-futuristic colors; prefer rich saffron, amber, crimson, and gold."
        ],
        greeting_formats=["Happy Diwali", "Shubh Deepavali", "Wishing You Joy & Prosperity"]
    ),
    "holi": CulturalFestivalRule(
        id="holi",
        name="Holi (Festival of Colors)",
        culture="Indian / Hindu",
        traditional_season="March",
        authentic_motifs=["dry gulal powder clouds", "pichkari (water canon)", "gujiya sweets", "vibrant color splash"],
        palette={
            "background": "#0F172A",
            "surface": "#1E293B",
            "primary": "#FFFFFF",
            "muted": "#38BDF8",
            "accent": "#EC4899"
        },
        typography_recommendation={"display": "Poppins", "text": "Inter"},
        taboos=[
            "Do not show dark grim shadows; Holi is joyful and chromatic.",
            "Maintain high contrast text readability over color splash overlays using solid panels."
        ],
        greeting_formats=["Happy Holi", "Rang Barse", "Colors of Joy & Friendship"]
    ),
    "eid": CulturalFestivalRule(
        id="eid",
        name="Eid al-Fitr / Eid al-Adha",
        culture="Islamic",
        traditional_season="Varies by Lunar Calendar",
        authentic_motifs=["crescent moon (hilal)", "eight-point star", "fanoos lantern", "arabesque geometric lattice"],
        palette={
            "background": "#041C15",
            "surface": "#0C3B2E",
            "primary": "#F8FAFC",
            "muted": "#6EE7B7",
            "accent": "#D4AF37"
        },
        typography_recommendation={"display": "DM Serif Display", "text": "DM Sans"},
        taboos=[
            "Never depict human or animal figures as sacred religious elements.",
            "Strictly avoid any alcohol, pork, or gambling references.",
            "Keep motifs graceful and modest; respect sacred calligraphy."
        ],
        greeting_formats=["Eid Mubarak", "Blessed Eid", "Kullu 'am wa antum bi-khayr"]
    ),
    "christmas": CulturalFestivalRule(
        id="christmas",
        name="Christmas & Holiday Season",
        culture="Western / Global",
        traditional_season="December",
        authentic_motifs=["pine needles", "minimalist gold stars", "holly berries", "winter glow", "snow frost"],
        palette={
            "background": "#0A1813",
            "surface": "#142820",
            "primary": "#F8FAFC",
            "muted": "#86EFAC",
            "accent": "#DC2626"
        },
        typography_recommendation={"display": "Playfair Display", "text": "Inter"},
        taboos=[
            "Avoid overly loud cartoonish clip art for premium brand announcements.",
            "Keep red and green pairings balanced with dark emerald and gold to avoid visual vibration."
        ],
        greeting_formats=["Merry Christmas", "Season's Greetings", "Warm Holiday Wishes"]
    ),
    "new_year": CulturalFestivalRule(
        id="new_year",
        name="New Year Countdown",
        culture="Global",
        traditional_season="December 31 - January 1",
        authentic_motifs=["countdown clock", "champagne gold confetti", "geometric radiance", "sleek ribbon"],
        palette={
            "background": "#09090B",
            "surface": "#18181B",
            "primary": "#FAFAFA",
            "muted": "#A1A1AA",
            "accent": "#EAB308"
        },
        typography_recommendation={"display": "Bebas Neue", "text": "Inter"},
        taboos=[
            "Do not clutter with multiple competing countdown years.",
            "Ensure the primary resolution or sale benefit is the clear focal point."
        ],
        greeting_formats=["Happy New Year", "Welcome 2027", "New Beginnings"]
    ),
    "pongal_onam": CulturalFestivalRule(
        id="pongal_onam",
        name="Pongal / Onam Harvest Festivals",
        culture="South Indian",
        traditional_season="January (Pongal) / August-September (Onam)",
        authentic_motifs=["earthen clay pot with overflowing milk", "sugarcane stalks", "pookkalam floral carpet", "banana leaf"],
        palette={
            "background": "#140A04",
            "surface": "#291509",
            "primary": "#FEF3C7",
            "muted": "#FCD34D",
            "accent": "#EA580C"
        },
        typography_recommendation={"display": "DM Serif Display", "text": "Inter"},
        taboos=[
            "Do not mix North Indian Diwali firecrackers with South Indian harvest serenity.",
            "Portray harvest motifs with agricultural dignity and warmth."
        ],
        greeting_formats=["Happy Pongal", "Iniya Pongal Nalvazhthukkal", "Happy Onam"]
    )
}


# ---------------------------------------------------------------------------
# 30 Curated Reference Briefs Library (Section 8.2)
# ---------------------------------------------------------------------------

REFERENCE_BRIEFS: List[Dict[str, Any]] = [
    {
        "id": "REF-01",
        "industry": "Jewelry & Luxury",
        "poster_type": "offer_promo",
        "recommended_archetype": "centered-badge",
        "headline": "Akshaya Tritiya Gold Festival",
        "subhead": "Flat 30% Off Making Charges on Diamond Suites",
        "cta": "Explore Collection",
        "palette": {"background": "#0D0A14", "primary": "#FAF5FF", "accent": "#EAB308"}
    },
    {
        "id": "REF-02",
        "industry": "Gourmet Dining",
        "poster_type": "product_showcase",
        "recommended_archetype": "split-image-text",
        "headline": "Artisanal Truffle Pasta",
        "subhead": "Handcrafted Tagliolini with Aged Parmigiano Reggiano",
        "cta": "Reserve Table",
        "palette": {"background": "#1A100B", "primary": "#FFF7ED", "accent": "#F97316"}
    },
    {
        "id": "REF-03",
        "industry": "Executive Coaching",
        "poster_type": "testimonial_quote",
        "recommended_archetype": "quote-card",
        "headline": "Leadership in the Age of Autonomy",
        "subhead": "The single best decision we made for executive scale.",
        "cta": "Read Case Study",
        "palette": {"background": "#0B0F19", "primary": "#F8FAFC", "accent": "#6366F1"}
    },
    {
        "id": "REF-04",
        "industry": "SaaS & AI",
        "poster_type": "general_announcement",
        "recommended_archetype": "hero-text",
        "headline": "Deploy Agent Teams in Minutes",
        "subhead": "Autonomous social pipelines with built-in human governance.",
        "cta": "Start Free Trial",
        "palette": {"background": "#030712", "primary": "#F9FAFB", "accent": "#3B82F6"}
    },
    {
        "id": "REF-05",
        "industry": "Retail & Fashion",
        "poster_type": "offer_promo",
        "recommended_archetype": "offer-burst",
        "headline": "Mid-Season Clearance Sale",
        "subhead": "Up to 50% Off Designer Apparel this Weekend Only",
        "cta": "Shop Now",
        "palette": {"background": "#0A0A0A", "primary": "#FFFFFF", "accent": "#EF4444"}
    },
    {
        "id": "REF-06",
        "industry": "Tech Conference",
        "poster_type": "event_announcement",
        "recommended_archetype": "event-ticket",
        "headline": "Global AI Summit 2026",
        "subhead": "November 14-16 • Moscone Center San Francisco",
        "cta": "Register Today",
        "palette": {"background": "#050814", "primary": "#F8FAFC", "accent": "#10B981"}
    },
    {
        "id": "REF-07",
        "industry": "Architectural Design",
        "poster_type": "general_announcement",
        "recommended_archetype": "minimal-editorial",
        "headline": "Form Follows Quietude",
        "subhead": "Residential sanctuaries designed for natural light and silence.",
        "cta": "View Monograph",
        "palette": {"background": "#F5F5F4", "primary": "#1C1917", "accent": "#57534E"}
    }
]


# ---------------------------------------------------------------------------
# Search and Retrieval Utilities
# ---------------------------------------------------------------------------

def search_rule_cards(query: str) -> List[RuleCard]:
    """Retrieves relevant rule cards matching query terms."""
    q_terms = [t.lower() for t in query.split() if len(t) > 2]
    if not q_terms:
        return RULE_CARDS[:4]

    matched = []
    for card in RULE_CARDS:
        card_text = f"{card.id} {card.category} {card.title} {card.rule} {card.rationale}".lower()
        if any(term in card_text for term in q_terms):
            matched.append(card)
    return matched if matched else RULE_CARDS[:3]


def get_cultural_rules(occasion_or_text: str) -> Optional[CulturalFestivalRule]:
    """Matches text against authentic cultural festival dictionaries."""
    text_lower = occasion_or_text.lower()
    for key, fest in CULTURAL_FESTIVALS.items():
        if key in text_lower or any(m in text_lower for m in [fest.name.lower(), fest.culture.lower()]):
            return fest
    return None


def get_reference_briefs_by_type(poster_type: str) -> List[Dict[str, Any]]:
    """Returns curated reference briefs by poster type or archetype."""
    p_lower = poster_type.lower()
    matched = [r for r in REFERENCE_BRIEFS if p_lower in r["poster_type"] or p_lower in r["recommended_archetype"]]
    return matched if matched else REFERENCE_BRIEFS[:2]
