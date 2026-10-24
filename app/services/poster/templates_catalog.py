"""Catalog of 30 Parametric Templates across 10 Layout Archetypes.

Implements Phase 4 of the Production Build Instructions:
- 10 Layout Archetypes (Hero Text, Split Image + Text, Centered Badge, Offer Burst,
  Quote Card, Product Cutout, Grid Multi-Item, Event Ticket, Stats & Metric, Minimal Editorial)
- 3 distinct parametric variants per archetype = 30 templates total.
- Client photo cutout awareness, vertical affinity, and goal scoring metadata.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TemplateDefinition(BaseModel):
    id: str
    name: str
    archetype: str
    variant: str
    description: str
    focal_element: str
    best_for_verticals: List[str]
    best_for_goals: List[str]
    supports_photo_cutout: bool = False
    requires_imagery: bool = False
    preview_palette: Dict[str, str] = Field(default_factory=dict)


# The 10 Layout Archetypes definitions
ARCHETYPES_CATALOG: Dict[str, Dict[str, Any]] = {
    "hero-text": {
        "id": "hero-text",
        "name": "Hero Text (Typographic)",
        "description": "Bold headline dominance, minimal clutter, strong messaging focus.",
        "focal": "headline",
        "best_for": "Brand announcements, vision statements, SaaS launches, thought leadership",
        "variants": ["hero-bold-minimal", "hero-diagonal-slant", "hero-framed-card"]
    },
    "split-image-text": {
        "id": "split-image-text",
        "name": "Split Image + Text",
        "description": "Balanced dual-zone composition pairing photographic proof with high-contrast text.",
        "focal": "photo",
        "best_for": "Culinary, dining, hospitality, real estate, salon treatments",
        "variants": ["split-50-50-vertical", "split-60-40-horizontal", "split-asymmetric-diagonal"]
    },
    "centered-badge": {
        "id": "centered-badge",
        "name": "Centered Badge (Celebration)",
        "description": "Symmetrical heritage medallion, emblem, or festive frame focal point.",
        "focal": "badge_circle",
        "best_for": "Cultural festivals, brand anniversaries, awards, grand openings",
        "variants": ["badge-heritage-seal", "badge-neon-pill", "badge-festive-arch"]
    },
    "offer-burst": {
        "id": "offer-burst",
        "name": "Offer Burst (Promotion)",
        "description": "High-urgency promotional badges, large percentage discounts, and commercial CTAs.",
        "focal": "burst_text",
        "best_for": "Flash sales, seasonal discounts, weekend drops, limited promotions",
        "variants": ["offer-explosive-tag", "offer-sticker-peel", "offer-geometric-flash"]
    },
    "quote-card": {
        "id": "quote-card",
        "name": "Quote Card (Social Proof)",
        "description": "Verified testimonials, client reviews, 5-star ratings, and executive statements.",
        "focal": "quote_text",
        "best_for": "Client testimonials, reviews, social proof, case studies, authority building",
        "variants": ["quote-editorial-serif", "quote-chat-bubble", "quote-glass-card"]
    },
    "product-cutout": {
        "id": "product-cutout",
        "name": "Product Cutout (Spotlight)",
        "description": "Centrally floating product with transparency, radiant backdrop, and feature highlights.",
        "focal": "product_hero",
        "best_for": "Sneakers, streetwear, cosmetics, luxury jewelry, hardware, packaged goods",
        "variants": ["product-floating-shadow", "product-neon-glow", "product-pedestal-stage"]
    },
    "grid-multi-item": {
        "id": "grid-multi-item",
        "name": "Grid Multi-Item (Showcase)",
        "description": "Structured multi-item quadrant or 3-card collection display for catalogues and before/after.",
        "focal": "grid_container",
        "best_for": "Lookbooks, service menus, seasonal collections, before/after dental/salon comparisons",
        "variants": ["grid-3-item-showcase", "grid-4-lookbook", "grid-2x2-comparison"]
    },
    "event-ticket": {
        "id": "event-ticket",
        "name": "Event Ticket (Invitation)",
        "description": "Distinctive ticket stub, calendar badge, venue schedule, and attendee pass formatting.",
        "focal": "date_block",
        "best_for": "Conferences, workshops, masterclasses, pop-ups, launch parties",
        "variants": ["event-stub-punch", "event-vip-metallic", "event-boarding-pass"]
    },
    "stats-metric": {
        "id": "stats-metric",
        "name": "Stats & Metric (Proof Point)",
        "description": "Oversized statistical callouts, growth indicators, percentage claims, and clinical results.",
        "focal": "stat_number",
        "best_for": "Clinic patient outcomes, SaaS growth numbers, gym transformations, auto detailing longevity",
        "variants": ["stats-giant-number", "stats-progress-ring", "stats-comparative-bar"]
    },
    "minimal-editorial": {
        "id": "minimal-editorial",
        "name": "Minimal Editorial (Luxury)",
        "description": "Vogue/Monograph inspired ultra-generous margins, refined serif typography, and quiet luxury.",
        "focal": "headline",
        "best_for": "High-fashion, luxury spas, aesthetic clinics, architectural real estate, fine jewelry",
        "variants": ["editorial-high-fashion", "editorial-swiss-grid", "editorial-gallery-frame"]
    }
}


# 30 Parametric Templates (3 per archetype)
TEMPLATES_CATALOG: List[TemplateDefinition] = [
    # 1. Hero Text Archetype
    TemplateDefinition(
        id="hero-bold-minimal",
        name="Bold Minimalist Hero",
        archetype="hero-text",
        variant="bold_minimal",
        description="Massive display typography with clean 8px padding and high-contrast color accents.",
        focal_element="headline",
        best_for_verticals=["tech_saas", "gym_fitness", "sneakers_streetwear", "education_tutoring"],
        best_for_goals=["brand_awareness", "product_launch", "general_update"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#6366F1", "bg": "#0B0F19"}
    ),
    TemplateDefinition(
        id="hero-diagonal-slant",
        name="Diagonal Kinetic Hero",
        archetype="hero-text",
        variant="diagonal_slant",
        description="Dynamic diagonal accent polygon behind bold angled announcement typography.",
        focal_element="headline",
        best_for_verticals=["gym_fitness", "auto_detail", "sneakers_streetwear", "tech_saas"],
        best_for_goals=["product_launch", "promotion", "brand_awareness"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#F59E0B", "bg": "#0D1117"}
    ),
    TemplateDefinition(
        id="hero-framed-card",
        name="Framed Architectural Hero",
        archetype="hero-text",
        variant="framed_card",
        description="Structured inner framed card with double-border container and elegant subhead placement.",
        focal_element="headline",
        best_for_verticals=["real_estate", "education_tutoring", "tech_saas", "local_services"],
        best_for_goals=["brand_awareness", "educational", "announcement"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#3B82F6", "bg": "#0F172A"}
    ),

    # 2. Split Image + Text Archetype
    TemplateDefinition(
        id="split-50-50-vertical",
        name="Classic 50/50 Split Showcase",
        archetype="split-image-text",
        variant="50_50_vertical",
        description="Clean vertical split with high-res photography on top and brand typography on bottom.",
        focal_element="photo",
        best_for_verticals=["cafe_coffee", "travel_hospitality", "salon_spa", "real_estate", "event_wedding"],
        best_for_goals=["brand_awareness", "product_launch", "promotion"],
        supports_photo_cutout=True,
        requires_imagery=True,
        preview_palette={"primary": "#E8890C", "bg": "#120A06"}
    ),
    TemplateDefinition(
        id="split-60-40-horizontal",
        name="Horizon 60/40 Split Panel",
        archetype="split-image-text",
        variant="60_40_horizontal",
        description="60% immersive photography horizon paired with a 40% solid color card and primary CTA.",
        focal_element="photo",
        best_for_verticals=["real_estate", "auto_detail", "travel_hospitality", "cafe_coffee"],
        best_for_goals=["promotion", "brand_awareness"],
        supports_photo_cutout=True,
        requires_imagery=True,
        preview_palette={"primary": "#10B981", "bg": "#06281E"}
    ),
    TemplateDefinition(
        id="split-asymmetric-diagonal",
        name="Asymmetric Diagonal Cut Split",
        archetype="split-image-text",
        variant="asymmetric_diagonal",
        description="Modern angled divider cutting through photography to create a dynamic action posture.",
        focal_element="photo",
        best_for_verticals=["sneakers_streetwear", "gym_fitness", "auto_detail", "boutique_fashion"],
        best_for_goals=["product_launch", "promotion"],
        supports_photo_cutout=True,
        requires_imagery=True,
        preview_palette={"primary": "#EF4444", "bg": "#111827"}
    ),

    # 3. Centered Badge Archetype
    TemplateDefinition(
        id="badge-heritage-seal",
        name="Royal Heritage Medallion",
        archetype="centered-badge",
        variant="heritage_seal",
        description="Symmetrical circular medallion with decorative concentric rings and regal typography.",
        focal_element="badge_circle",
        best_for_verticals=["jewelry_luxury", "cafe_coffee", "event_wedding", "boutique_fashion"],
        best_for_goals=["cultural_festival", "milestone", "brand_awareness"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#EAB308", "bg": "#0B0712"}
    ),
    TemplateDefinition(
        id="badge-neon-pill",
        name="Cyber Neon Pill Badge",
        archetype="centered-badge",
        variant="neon_pill",
        description="High-voltage luminous capsule badge with rounded geometry and intense contrast.",
        focal_element="badge_circle",
        best_for_verticals=["tech_saas", "sneakers_streetwear", "gym_fitness"],
        best_for_goals=["product_launch", "announcement"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#06B6D4", "bg": "#030712"}
    ),
    TemplateDefinition(
        id="badge-festive-arch",
        name="Festive Architectural Arch",
        archetype="centered-badge",
        variant="festive_arch",
        description="Culturally inspired archway framing auspicious greetings and festive season offers.",
        focal_element="badge_circle",
        best_for_verticals=["event_wedding", "jewelry_luxury", "salon_spa", "travel_hospitality"],
        best_for_goals=["cultural_festival", "milestone", "seasonal_greeting"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#F59E0B", "bg": "#1C102E"}
    ),

    # 4. Offer Burst Archetype
    TemplateDefinition(
        id="offer-explosive-tag",
        name="Explosive Discount Tag",
        archetype="offer-burst",
        variant="explosive_tag",
        description="Faceted high-urgency burst badge displaying prominent discount percentages.",
        focal_element="burst_text",
        best_for_verticals=["sneakers_streetwear", "boutique_fashion", "auto_detail", "local_services"],
        best_for_goals=["promotion", "flash_sale", "clearance"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#EF4444", "bg": "#0A0A0A"}
    ),
    TemplateDefinition(
        id="offer-sticker-peel",
        name="Angled Sticker Peel",
        archetype="offer-burst",
        variant="sticker_peel",
        description="Modern skewed promotional sticker with drop-shadow effect and clear coupon CTA.",
        focal_element="burst_text",
        best_for_verticals=["boutique_fashion", "cafe_coffee", "gym_fitness", "salon_spa"],
        best_for_goals=["promotion", "special_offer"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#EC4899", "bg": "#18181B"}
    ),
    TemplateDefinition(
        id="offer-geometric-flash",
        name="Diagonal Flash Banner",
        archetype="offer-burst",
        variant="geometric_flash",
        description="Bold diagonal strike-through ribbon with maximum color contrast and scarcity messaging.",
        focal_element="burst_text",
        best_for_verticals=["sneakers_streetwear", "gym_fitness", "tech_saas"],
        best_for_goals=["promotion", "flash_sale"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#F97316", "bg": "#09090B"}
    ),

    # 5. Quote Card Archetype
    TemplateDefinition(
        id="quote-editorial-serif",
        name="Editorial Serif Quotation",
        archetype="quote-card",
        variant="editorial_serif",
        description="Oversized glyph quotation marks with high-end editorial serif statement copy.",
        focal_element="quote_text",
        best_for_verticals=["clinic_healthcare", "salon_spa", "jewelry_luxury", "real_estate"],
        best_for_goals=["social_proof", "review", "brand_authority"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#10B981", "bg": "#06281E"}
    ),
    TemplateDefinition(
        id="quote-chat-bubble",
        name="Client Voice Chat Bubble",
        archetype="quote-card",
        variant="chat_bubble",
        description="Modern conversational bubble with verified 5-star rating stars and verified badge.",
        focal_element="quote_text",
        best_for_verticals=["local_services", "auto_detail", "education_tutoring", "tech_saas"],
        best_for_goals=["social_proof", "customer_review"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#3B82F6", "bg": "#0B1528"}
    ),
    TemplateDefinition(
        id="quote-glass-card",
        name="Frosted Glassmorphism Testimonial",
        archetype="quote-card",
        variant="glass_card",
        description="Refined translucent glass card with subtle border glow resting on deep atmospheric backdrop.",
        focal_element="quote_text",
        best_for_verticals=["salon_spa", "clinic_healthcare", "tech_saas", "boutique_fashion"],
        best_for_goals=["social_proof", "client_spotlight"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#8B5CF6", "bg": "#0F0B1E"}
    ),

    # 6. Product Cutout Archetype (NEW)
    TemplateDefinition(
        id="product-floating-shadow",
        name="Floating Product with Depth Shadow",
        archetype="product-cutout",
        variant="floating_shadow",
        description="Client product cutout floating centered with realistic soft contact shadow and feature callouts.",
        focal_element="product_hero",
        best_for_verticals=["sneakers_streetwear", "boutique_fashion", "jewelry_luxury", "auto_detail"],
        best_for_goals=["product_launch", "new_arrival", "featured_product"],
        supports_photo_cutout=True,
        requires_imagery=True,
        preview_palette={"primary": "#EF4444", "bg": "#0F172A"}
    ),
    TemplateDefinition(
        id="product-neon-glow",
        name="Radiant Neon Halo Cutout",
        archetype="product-cutout",
        variant="neon_glow",
        description="Vibrant colored rim glow contouring the product silhouette against deep moody backdrop.",
        focal_element="product_hero",
        best_for_verticals=["sneakers_streetwear", "gym_fitness", "tech_saas"],
        best_for_goals=["product_launch", "drop_announcement"],
        supports_photo_cutout=True,
        requires_imagery=True,
        preview_palette={"primary": "#06B6D4", "bg": "#020617"}
    ),
    TemplateDefinition(
        id="product-pedestal-stage",
        name="Architectural Pedestal Podium",
        archetype="product-cutout",
        variant="pedestal_stage",
        description="Minimalist 3D pedestal stage anchoring the product with luxury museum presentation.",
        focal_element="product_hero",
        best_for_verticals=["jewelry_luxury", "boutique_fashion", "salon_spa", "cafe_coffee"],
        best_for_goals=["product_launch", "collection_highlight"],
        supports_photo_cutout=True,
        requires_imagery=True,
        preview_palette={"primary": "#D97706", "bg": "#1C1917"}
    ),

    # 7. Grid Multi-Item Archetype (NEW)
    TemplateDefinition(
        id="grid-3-item-showcase",
        name="3-Item Horizontal Showcase",
        archetype="grid-multi-item",
        variant="3_item_showcase",
        description="Three balanced service or product cards arranged horizontally with individual tags.",
        focal_element="grid_container",
        best_for_verticals=["salon_spa", "clinic_healthcare", "cafe_coffee", "local_services"],
        best_for_goals=["menu_highlights", "service_offerings", "collection_overview"],
        supports_photo_cutout=True,
        preview_palette={"primary": "#059669", "bg": "#062018"}
    ),
    TemplateDefinition(
        id="grid-4-lookbook",
        name="4-Quadrant Lookbook Grid",
        archetype="grid-multi-item",
        variant="4_lookbook",
        description="2x2 grid quadrant showing 4 coordinated items or lifestyle scenes from a seasonal collection.",
        focal_element="grid_container",
        best_for_verticals=["boutique_fashion", "sneakers_streetwear", "real_estate", "travel_hospitality"],
        best_for_goals=["lookbook", "collection_launch", "portfolio"],
        supports_photo_cutout=True,
        preview_palette={"primary": "#8B5CF6", "bg": "#110D1F"}
    ),
    TemplateDefinition(
        id="grid-2x2-comparison",
        name="Before & After Transformation",
        archetype="grid-multi-item",
        variant="2x2_comparison",
        description="Side-by-side or stacked transformation panels highlighting verified client results.",
        focal_element="grid_container",
        best_for_verticals=["clinic_healthcare", "salon_spa", "auto_detail", "gym_fitness"],
        best_for_goals=["before_after", "case_study", "social_proof"],
        supports_photo_cutout=True,
        preview_palette={"primary": "#2563EB", "bg": "#0B1528"}
    ),

    # 8. Event Ticket Archetype
    TemplateDefinition(
        id="event-stub-punch",
        name="Perforated Stub Ticket Pass",
        archetype="event-ticket",
        variant="stub_punch",
        description="Authentic perforated concert ticket with cutout semicircles and bold calendar block.",
        focal_element="date_block",
        best_for_verticals=["event_wedding", "education_tutoring", "cafe_coffee", "tech_saas"],
        best_for_goals=["event_rsvp", "workshop", "masterclass"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#3B82F6", "bg": "#050B18"}
    ),
    TemplateDefinition(
        id="event-vip-metallic",
        name="VIP Metallic Hologram Pass",
        archetype="event-ticket",
        variant="vip_metallic",
        description="Exclusive black card pass with metallic foil border accents and numbered access tiers.",
        focal_element="date_block",
        best_for_verticals=["jewelry_luxury", "boutique_fashion", "real_estate", "tech_saas"],
        best_for_goals=["exclusive_event", "vip_access", "launch_party"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#F59E0B", "bg": "#0C0A09"}
    ),
    TemplateDefinition(
        id="event-boarding-pass",
        name="Minimal Boarding Pass Card",
        archetype="event-ticket",
        variant="boarding_pass",
        description="Air travel and airport lounge aesthetic with flight/time blocks and barcode accent.",
        focal_element="date_block",
        best_for_verticals=["travel_hospitality", "tech_saas", "education_tutoring"],
        best_for_goals=["event_rsvp", "conference", "retreat"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#0D9488", "bg": "#042F2E"}
    ),

    # 9. Stats & Metric Archetype (NEW)
    TemplateDefinition(
        id="stats-giant-number",
        name="Giant Number Milestone",
        archetype="stats-metric",
        variant="giant_number",
        description="Heroic oversized numeral (e.g. 99%, 10,000+, 4.9★) providing immediate empirical proof.",
        focal_element="stat_number",
        best_for_verticals=["clinic_healthcare", "tech_saas", "education_tutoring", "gym_fitness"],
        best_for_goals=["milestone", "social_proof", "performance_metrics"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#10B981", "bg": "#06221A"}
    ),
    TemplateDefinition(
        id="stats-progress-ring",
        name="Progress Circular Gauge Metric",
        archetype="stats-metric",
        variant="progress_ring",
        description="Circular radial progress dial visually proving client success or milestone completion.",
        focal_element="stat_number",
        best_for_verticals=["gym_fitness", "auto_detail", "clinic_healthcare", "tech_saas"],
        best_for_goals=["performance_metrics", "milestone", "case_study"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#F59E0B", "bg": "#181204"}
    ),
    TemplateDefinition(
        id="stats-comparative-bar",
        name="Comparative Tier Metric Bar",
        archetype="stats-metric",
        variant="comparative_bar",
        description="High-contrast metrics comparison bars contrasting your standard against industry averages.",
        focal_element="stat_number",
        best_for_verticals=["tech_saas", "local_services", "auto_detail", "real_estate"],
        best_for_goals=["competitive_advantage", "performance_metrics", "educational"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#6366F1", "bg": "#0D1127"}
    ),

    # 10. Minimal Editorial Archetype
    TemplateDefinition(
        id="editorial-high-fashion",
        name="Vogue Editorial Cover",
        archetype="minimal-editorial",
        variant="high_fashion",
        description="High-fashion oversized serif typography with extreme whitespace and museum elegance.",
        focal_element="headline",
        best_for_verticals=["boutique_fashion", "jewelry_luxury", "salon_spa", "travel_hospitality"],
        best_for_goals=["brand_awareness", "collection_launch", "luxury_branding"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#F5F5F4", "bg": "#0C0A09"}
    ),
    TemplateDefinition(
        id="editorial-swiss-grid",
        name="Modernist Swiss Grid",
        archetype="minimal-editorial",
        variant="swiss_grid",
        description="Strict International Typographic Style with hairline rules, clean sans typography, and mathematical margins.",
        focal_element="headline",
        best_for_verticals=["tech_saas", "real_estate", "clinic_healthcare", "education_tutoring"],
        best_for_goals=["brand_awareness", "educational", "announcement"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#E2E8F0", "bg": "#0F172A"}
    ),
    TemplateDefinition(
        id="editorial-gallery-frame",
        name="Museum Gallery Fine Frame",
        archetype="minimal-editorial",
        variant="gallery_frame",
        description="Fine double-matted museum frame enclosing delicate central copy and luxury brand signature.",
        focal_element="headline",
        best_for_verticals=["jewelry_luxury", "event_wedding", "salon_spa", "real_estate"],
        best_for_goals=["brand_awareness", "exclusive_invitation", "milestone"],
        supports_photo_cutout=False,
        preview_palette={"primary": "#D4AF37", "bg": "#120E08"}
    ),
]

# Quick lookup indexes
TEMPLATE_BY_ID: Dict[str, TemplateDefinition] = {t.id: t for t in TEMPLATES_CATALOG}
TEMPLATES_BY_ARCHETYPE: Dict[str, List[TemplateDefinition]] = {}
for t in TEMPLATES_CATALOG:
    TEMPLATES_BY_ARCHETYPE.setdefault(t.archetype, []).append(t)


def get_template_definition(template_id: str) -> Optional[TemplateDefinition]:
    """Retrieves template metadata by ID, fallback to None if not found."""
    return TEMPLATE_BY_ID.get(template_id)


def list_templates_for_archetype(archetype_id: str) -> List[TemplateDefinition]:
    """Returns the 3 parametric variants belonging to the specified layout archetype."""
    return TEMPLATES_BY_ARCHETYPE.get(archetype_id, [])
