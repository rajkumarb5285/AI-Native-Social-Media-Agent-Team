"""Creative Direction & Vertical Visual Language Catalog.

Defines the 14-vertical design taxonomy, typography pairings, color harmonies,
layout archetypes, and tone guidelines for the multi-tenant design pipeline.
Zero hardcoded defaults to coffee; strictly business-aware.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ColorPalette(BaseModel):
    primary: str = Field(..., description="Dominant brand accent color #RRGGBB")
    secondary: str = Field(..., description="Secondary supporting color #RRGGBB")
    accent: str = Field(..., description="High-visibility CTA or highlight color #RRGGBB")
    background: str = Field(..., description="Base canvas/background color #RRGGBB")
    surface: str = Field(..., description="Card, pill, or container color #RRGGBB")
    text_primary: str = Field(..., description="High-contrast text color #RRGGBB")
    text_muted: str = Field(..., description="Secondary/meta text color #RRGGBB")


class TypographyPairing(BaseModel):
    display_font: str = Field(..., description="Display / headline font family")
    body_font: str = Field(..., description="Body / UI text font family")
    headline_style: str = Field(default="bold", description="e.g. bold, condensed, serif, tracking")
    body_style: str = Field(default="clean", description="e.g. clean, grotesque, humanist")


class CreativeDirection(BaseModel):
    vertical: str = Field(..., description="Industry vertical key (e.g. sneakers_streetwear, salon_spa)")
    vertical_name: str = Field(..., description="Human-readable vertical title")
    style_family: str = Field(..., description="Design archetype/style family")
    palette: ColorPalette = Field(..., description="Primary color harmony")
    palette_options: List[ColorPalette] = Field(default_factory=list, description="Alternative curated harmonies")
    typography: TypographyPairing = Field(..., description="Curated font pairing")
    ranked_archetypes: List[str] = Field(default_factory=list, description="Ranked layout archetypes")
    imagery_strategy: str = Field(..., description="Guidelines for hero photography or graphics")
    shapes_patterns: List[str] = Field(default_factory=list, description="Allowed graphic motifs and accents")
    copy_tone: str = Field(..., description="Voice and tone direction")
    claims_policy: str = Field(default="standard", description="Rules on claims, superlatives, and disclaimers")
    brand_keywords: List[str] = Field(default_factory=list, description="Vertical-specific stylistic tags")
    disallowed_terms: List[str] = Field(default_factory=list, description="Forbidden cross-industry contaminated terms")
    custom_rules: List[str] = Field(default_factory=list, description="Specific layout and typography rules")
    sample_headlines: List[str] = Field(default_factory=list, description="Contextual headline suggestions")
    sample_ctas: List[str] = Field(default_factory=list, description="Contextual call-to-actions")


# ---------------------------------------------------------------------------
# 14-Vertical Visual Catalog
# ---------------------------------------------------------------------------

VERTICAL_CATALOG: Dict[str, Dict[str, Any]] = {
    "sneakers_streetwear": {
        "vertical_name": "Sneakers & Streetwear",
        "style_family": "streetwear_bold",
        "palette": {
            "primary": "#FF3366",       # Electric neon punch
            "secondary": "#00F0FF",     # Cyan contrast
            "accent": "#FFE600",        # Cyber yellow
            "background": "#0D0D11",    # Ultra-deep midnight
            "surface": "#1A1A24",
            "text_primary": "#FFFFFF",
            "text_muted": "#8A8D9E"
        },
        "palette_options": [
            {
                "primary": "#FF5500", "secondary": "#222222", "accent": "#FFFFFF",
                "background": "#0A0A0A", "surface": "#1F1F1F", "text_primary": "#FFFFFF", "text_muted": "#888888"
            },
            {
                "primary": "#E2E8F0", "secondary": "#475569", "accent": "#00FF66",
                "background": "#0F172A", "surface": "#1E293B", "text_primary": "#F8FAFC", "text_muted": "#94A3B8"
            }
        ],
        "typography": {
            "display_font": "Syne",
            "body_font": "Inter",
            "headline_style": "bold geometric uppercase",
            "body_style": "compact modern grotesque"
        },
        "ranked_archetypes": ["split-image-text", "hero-text", "offer-burst", "centered-badge"],
        "imagery_strategy": "product_cutout_dynamic_shadow_floating",
        "shapes_patterns": ["diagonal_slashes", "technical_crosshairs", "halftone_dots", "barcode_accents"],
        "copy_tone": "punchy, urgent, drop-centric, confident, concise",
        "claims_policy": "authenticity_verified_no_generic_fluff",
        "brand_keywords": ["drop", "silhouette", "colorway", "sole", "kicks", "limited edition", "grail"],
        "disallowed_terms": [
            "coffee", "brew", "beans", "barista", "espresso", "latte", "cappuccino", "roastery",
            "cold brew", "pour-over", "single-origin", "tasting session", "artisan selection",
            "slow pour", "organic roast", "clinic", "dental", "teeth"
        ],
        "custom_rules": [
            "Never use cursive or delicate serif typography.",
            "Display shoe silhouette on transparent or atmospheric cutout background.",
            "Badge emphasizes DROP DATE or EDITION NUMBER."
        ],
        "sample_headlines": ["The Next Drop", "Elevated Soles", "Strictly Authentic", "New Silhouette"],
        "sample_ctas": ["Shop The Drop", "Get Access", "View Collection"]
    },

    "salon_spa": {
        "vertical_name": "Salon, Spa & Beauty",
        "style_family": "editorial_minimal_refined",
        "palette": {
            "primary": "#C29B7F",       # Warm champagne terracotta
            "secondary": "#EED8C9",     # Soft blush silk
            "accent": "#9E6D52",        # Rich bronze
            "background": "#141110",    # Velvet obsidian
            "surface": "#231F1C",
            "text_primary": "#FAF6F0",
            "text_muted": "#B5A89E"
        },
        "palette_options": [
            {
                "primary": "#D4AF37", "secondary": "#F3E5AB", "accent": "#AA7C11",
                "background": "#0F1412", "surface": "#1B2420", "text_primary": "#F9F6F0", "text_muted": "#A2B3A8"
            }
        ],
        "typography": {
            "display_font": "Playfair Display",
            "body_font": "Inter",
            "headline_style": "delicate high-contrast serif italic",
            "body_style": "airy tracking humanist sans"
        },
        "ranked_archetypes": ["quote-card", "split-image-text", "centered-badge", "hero-text"],
        "imagery_strategy": "soft_focus_ambient_glow_macro_hair_skin",
        "shapes_patterns": ["hairline_borders", "subtle_arch_frames", "clean_oval_pills"],
        "copy_tone": "serene, rejuvenating, pampering, luxurious, mindful",
        "claims_policy": "experiential_wellness_licensed_stylists",
        "brand_keywords": ["radiance", "glow", "renewal", "bespoke styling", "ritual", "rejuvenate"],
        "disallowed_terms": [
            "coffee", "brew", "beans", "barista", "espresso", "single-origin", "cold brew",
            "streetwear", "kicks", "sneaker", "sole", "engine", "horsepower", "dental surgery"
        ],
        "custom_rules": [
            "High tracking on eyebrow and subline (+0.12em).",
            "Ample breathing room; never clutter canvas.",
            "Badge acts as quiet certification or service name."
        ],
        "sample_headlines": ["Pure Renewal", "Artisan Radiance", "Bespoke Styling", "Mindful Beauty"],
        "sample_ctas": ["Book Appointment", "Reserve Session", "View Services"]
    },

    "clinic_healthcare": {
        "vertical_name": "Clinic, Dental & Healthcare",
        "style_family": "clinical_pristine_authoritative",
        "palette": {
            "primary": "#0284C7",       # Trust medical azure
            "secondary": "#38BDF8",     # Cyan light
            "accent": "#0D9488",        # Clean clinical teal
            "background": "#08131F",    # Deep reassuring navy
            "surface": "#0F2338",
            "text_primary": "#F0F9FF",
            "text_muted": "#94A3B8"
        },
        "palette_options": [
            {
                "primary": "#059669", "secondary": "#34D399", "accent": "#10B981",
                "background": "#061A14", "surface": "#0C2E24", "text_primary": "#ECFDF5", "text_muted": "#86EFAC"
            }
        ],
        "typography": {
            "display_font": "Plus Jakarta Sans",
            "body_font": "Inter",
            "headline_style": "authoritative geometric sans bold",
            "body_style": "legible high-contrast neutral sans"
        },
        "ranked_archetypes": ["hero-text", "centered-badge", "split-image-text", "offer-burst"],
        "imagery_strategy": "pristine_sanitary_modern_equipment_warm_practitioner",
        "shapes_patterns": ["soft_cross_accents", "shield_nodes", "pill_badges", "grid_lines"],
        "copy_tone": "reassuring, authoritative, evidence-backed, transparent, warm",
        "claims_policy": "strict_medical_truth_zero_false_guarantees",
        "brand_keywords": ["expert care", "precision", "certified", "smile", "wellness", "trusted doctors"],
        "disallowed_terms": [
            "coffee", "brew", "roast", "espresso", "single-origin", "cold brew", "barista",
            "streetwear", "drop", "kicks", "sneakers", "sneaker", "miracle cure", "instant fix"
        ],
        "custom_rules": [
            "Zero unverified medical claims; factual descriptions only.",
            "Colors must adhere strictly to AAA/AA contrast for patients.",
            "Display provider credentials or clinic location clearly in footer."
        ],
        "sample_headlines": ["Confident Smiles", "Expert Family Care", "Precision Medicine", "Trusted Health"],
        "sample_ctas": ["Schedule Visit", "Book Consultation", "Contact Clinic"]
    },

    "real_estate": {
        "vertical_name": "Real Estate & Architecture",
        "style_family": "architectural_monolithic_prestige",
        "palette": {
            "primary": "#D4AF37",       # Warm architectural gold
            "secondary": "#64748B",     # Slate stone
            "accent": "#E2E8F0",        # Architectural concrete
            "background": "#0B0F17",    # Onyx foundation
            "surface": "#161D2A",
            "text_primary": "#F8FAFC",
            "text_muted": "#94A3B8"
        },
        "palette_options": [
            {
                "primary": "#1E293B", "secondary": "#475569", "accent": "#0284C7",
                "background": "#0A0D14", "surface": "#151B27", "text_primary": "#FFFFFF", "text_muted": "#94A3B8"
            }
        ],
        "typography": {
            "display_font": "Cinzel",
            "body_font": "Inter",
            "headline_style": "classical proportions spaced caps",
            "body_style": "structured crisp sans"
        },
        "ranked_archetypes": ["split-image-text", "hero-text", "centered-badge", "quote-card"],
        "imagery_strategy": "wide_angle_golden_hour_modern_facade_interiors",
        "shapes_patterns": ["architectural_floorplan_lines", "thin_golden_rules", "corner_brackets"],
        "copy_tone": "prestigious, visionary, discerning, permanent, aspirational",
        "claims_policy": "disclaimer_ready_accurate_property_spec",
        "brand_keywords": ["residence", "estate", "panoramic", "penthouse", "sanctuary", "architecture"],
        "disallowed_terms": [
            "coffee", "beans", "brew", "barista", "espresso", "latte", "single-origin",
            "sneakers", "kicks", "drop", "teeth", "molar"
        ],
        "custom_rules": [
            "Always include location or district indicator in eyebrow.",
            "Images must show clean vertical lines without distortion.",
            "Badge highlights private viewing or property tier."
        ],
        "sample_headlines": ["Modern Sanctuary", "Bespoke Living", "Elevated Living", "Prime Residence"],
        "sample_ctas": ["Schedule Private Tour", "Inquire Now", "View Floorplans"]
    },

    "cafe_coffee": {
        "vertical_name": "Cafe, Roastery & Artisan Food",
        "style_family": "warm_artisan_craft",
        "palette": {
            "primary": "#E8890C",       # Amber flame
            "secondary": "#D97706",     # Caramel
            "accent": "#F59E0B",        # Honey crema
            "background": "#120A06",    # Deep roasted walnut
            "surface": "#1E120A",
            "text_primary": "#FDF6ED",
            "text_muted": "#B59E8C"
        },
        "palette_options": [
            {
                "primary": "#A16207", "secondary": "#78350F", "accent": "#CA8A04",
                "background": "#0F0B08", "surface": "#1C140F", "text_primary": "#FEF3C7", "text_muted": "#A1887F"
            }
        ],
        "typography": {
            "display_font": "Fraunces",
            "body_font": "Inter",
            "headline_style": "warm organic serif with personality",
            "body_style": "clean humanist sans"
        },
        "ranked_archetypes": ["split-image-text", "centered-badge", "hero-text", "quote-card"],
        "imagery_strategy": "rich_warm_depth_single_glass_or_pour_with_crema",
        "shapes_patterns": ["coffee_steam_subtle", "roasted_bean_contour", "warm_inset_rules"],
        "copy_tone": "sensory, crafted, unhurried, warm, hospitable",
        "claims_policy": "origin_honest_flavor_profile_accurate",
        "brand_keywords": ["single-origin", "roast", "pour", "brew", "harvest", "aroma", "notes"],
        "disallowed_terms": [
            "teeth", "dental", "clinic", "sneakers", "kicks", "engine", "software", "saas"
        ],
        "custom_rules": [
            "Curved steam accents permitted only for hot coffee.",
            "Use warm amber scrim transitions at 40% canvas height.",
            "Badge displays tasting session, origin, or harvest note."
        ],
        "sample_headlines": ["One Origin", "Slow Crafted", "Morning Ritual", "Artisan Roast"],
        "sample_ctas": ["Reserve a Seat", "Order Beans", "Visit Cafe"]
    },

    "gym_fitness": {
        "vertical_name": "Gym, Fitness & Athletics",
        "style_family": "dynamic_kinetic_high_power",
        "palette": {
            "primary": "#E11D48",       # Intense crimson charge
            "secondary": "#FB7185",     # Energy coral
            "accent": "#22C55E",        # Sprint lime
            "background": "#09090B",    # Pitch carbon
            "surface": "#18181B",
            "text_primary": "#FAFAFA",
            "text_muted": "#A1A1AA"
        },
        "palette_options": [
            {
                "primary": "#EAB308", "secondary": "#CA8A04", "accent": "#FFFFFF",
                "background": "#0A0A0A", "surface": "#1A1A1A", "text_primary": "#FFFFFF", "text_muted": "#737373"
            }
        ],
        "typography": {
            "display_font": "Oswald",
            "body_font": "Inter",
            "headline_style": "condensed impactful heavy sans caps",
            "body_style": "athletic clean grotesque"
        },
        "ranked_archetypes": ["offer-burst", "hero-text", "split-image-text", "centered-badge"],
        "imagery_strategy": "dynamic_sweat_and_iron_high_contrast_action",
        "shapes_patterns": ["speed_chevrons", "repetition_slashes", "power_bars", "sharp_badges"],
        "copy_tone": "disciplined, motivating, relentless, empowering, direct",
        "claims_policy": "realistic_training_standards_no_fictional_loss",
        "brand_keywords": ["unbreakable", "strength", "endurance", "transform", "reps", "coach"],
        "disallowed_terms": [
            "coffee", "brew", "beans", "barista", "latte", "single-origin",
            "relaxing spa", "manicure", "pedicure", "magic pill"
        ],
        "custom_rules": [
            "Headlines are concise, punchy and set in condensed capitals.",
            "High energetic contrast with deep black backgrounds.",
            "Badge highlights trial pass or membership tier."
        ],
        "sample_headlines": ["Built Strong", "Break Barriers", "Every Single Rep", "Day One Starts"],
        "sample_ctas": ["Claim Free Pass", "Join The Gym", "Start Training"]
    },

    "boutique_fashion": {
        "vertical_name": "Boutique & Designer Fashion",
        "style_family": "high_fashion_editorial_vogue",
        "palette": {
            "primary": "#E5E5E5",       # Raw silk
            "secondary": "#A3A3A3",     # Silver thread
            "accent": "#D4AF37",        # Fine bullion
            "background": "#0A0A0A",    # Studio black
            "surface": "#171717",
            "text_primary": "#FFFFFF",
            "text_muted": "#737373"
        },
        "palette_options": [
            {
                "primary": "#BE185D", "secondary": "#F43F5E", "accent": "#FDE047",
                "background": "#0F0710", "surface": "#1E0D22", "text_primary": "#FFF1F2", "text_muted": "#FDA4AF"
            }
        ],
        "typography": {
            "display_font": "Bodoni Moda",
            "body_font": "Inter",
            "headline_style": "ultra-modern high contrast didone",
            "body_style": "minimalist tracking sans"
        },
        "ranked_archetypes": ["split-image-text", "hero-text", "quote-card", "centered-badge"],
        "imagery_strategy": "runway_studio_lighting_sharp_drape_silhouette",
        "shapes_patterns": ["hairline_geometry", "asymmetric_margins", "minimalist_rulers"],
        "copy_tone": "understated, avant-garde, refined, poetic, confident",
        "claims_policy": "curated_material_craftsmanship_statement",
        "brand_keywords": ["capsule", "atelier", "silhouette", "curated", "couture", "autumn"],
        "disallowed_terms": [
            "coffee", "brew", "roast", "beans", "barista", "espresso", "teeth", "clinic"
        ],
        "custom_rules": [
            "Extreme optical kerning and margin alignment.",
            "Photo covers full bleed with delicate text overlays.",
            "Badge indicates seasonal edition or atelier origin."
        ],
        "sample_headlines": ["The Autumn Edit", "Atelier Series", "Pure Form", "Modern Silhouette"],
        "sample_ctas": ["Explore Edit", "Shop Collection", "View Lookbook"]
    },

    "jewelry_luxury": {
        "vertical_name": "Jewelry, Watches & Luxury",
        "style_family": "opulent_precision_luxury",
        "palette": {
            "primary": "#D4AF37",       # 18K Yellow gold
            "secondary": "#E5DCC5",     # Champagne brilliance
            "accent": "#FFFFFF",        # Diamond refraction
            "background": "#05070A",    # Vault sapphire-black
            "surface": "#0E131C",
            "text_primary": "#F8FAFC",
            "text_muted": "#94A3B8"
        },
        "palette_options": [
            {
                "primary": "#B76E79", "secondary": "#F3C5C5", "accent": "#FFFFFF",
                "background": "#0D0A0B", "surface": "#1A1416", "text_primary": "#FFF0F2", "text_muted": "#D8A3AA"
            }
        ],
        "typography": {
            "display_font": "Cinzel",
            "body_font": "Inter",
            "headline_style": "regal classical Roman capitals",
            "body_style": "precision engineered sans"
        },
        "ranked_archetypes": ["centered-badge", "split-image-text", "hero-text", "quote-card"],
        "imagery_strategy": "macro_facet_refraction_sharp_metallic_reflection",
        "shapes_patterns": ["diamond_polygons", "gold_hairline_frames", "concentric_bezels"],
        "copy_tone": "timeless, heirloom, sovereign, exacting, precious",
        "claims_policy": "hallmark_and_gemstone_clarity_adherence",
        "brand_keywords": ["heirloom", "chronograph", "brilliance", "carat", "bespoke", "timeless"],
        "disallowed_terms": [
            "coffee", "brew", "beans", "barista", "latte", "sneaker", "kicks", "cheap", "sale"
        ],
        "custom_rules": [
            "Use subtle specular gold gradients.",
            "Ensure macro photography focal point is razor sharp.",
            "Badge marks carat weight, limited edition number, or master atelier."
        ],
        "sample_headlines": ["Timeless Radiance", "Master Crafted", "Eternal Precision", "Pure Brilliance"],
        "sample_ctas": ["Inquire Atelier", "Book Consultation", "Explore Timepieces"]
    },

    "education_tutoring": {
        "vertical_name": "Education, Tutoring & Academies",
        "style_family": "scholarly_inspiring_empowering",
        "palette": {
            "primary": "#2563EB",       # Academic royal blue
            "secondary": "#F59E0B",     # Wisdom amber
            "accent": "#10B981",        # Achievement emerald
            "background": "#0B1120",    # Oxford night
            "surface": "#151F36",
            "text_primary": "#F8FAFC",
            "text_muted": "#94A3B8"
        },
        "palette_options": [
            {
                "primary": "#7C3AED", "secondary": "#C084FC", "accent": "#FACC15",
                "background": "#0F0A1E", "surface": "#1C1438", "text_primary": "#FAF5FF", "text_muted": "#D8B4FE"
            }
        ],
        "typography": {
            "display_font": "Plus Jakarta Sans",
            "body_font": "Inter",
            "headline_style": "inspiring clean sans bold",
            "body_style": "accessible friendly humanist sans"
        },
        "ranked_archetypes": ["hero-text", "offer-burst", "split-image-text", "centered-badge"],
        "imagery_strategy": "engaged_learner_modern_classroom_focused_study",
        "shapes_patterns": ["growth_graphs", "open_book_motifs", "achievement_stars", "bracketed_callouts"],
        "copy_tone": "encouraging, credible, transformative, structured, ambitious",
        "claims_policy": "verified_syllabus_measurable_progress_no_guaranteed_marks",
        "brand_keywords": ["mastery", "curriculum", "mentorship", "unlock potential", "academic", "cohort"],
        "disallowed_terms": [
            "coffee", "brew", "beans", "barista", "latte", "sneakers", "nightclub"
        ],
        "custom_rules": [
            "Highlight cohort start date or enrollment window.",
            "Badges show grade level, test tier, or certification.",
            "Copy must clearly state course topic."
        ],
        "sample_headlines": ["Unlock Mastery", "Learn From Experts", "Fall Cohort Open", "Accelerate Growth"],
        "sample_ctas": ["Enroll Today", "Download Syllabus", "Book Free Trial"]
    },

    "tech_saas": {
        "vertical_name": "Tech, SaaS & Developer Tools",
        "style_family": "cyber_infrastructure_modular",
        "palette": {
            "primary": "#6366F1",       # Indigo vector
            "secondary": "#A855F7",     # Purple gradient
            "accent": "#06B6D4",        # Cyber cyan
            "background": "#080B14",    # Terminal black
            "surface": "#111827",
            "text_primary": "#F9FAFB",
            "text_muted": "#9CA3AF"
        },
        "palette_options": [
            {
                "primary": "#10B981", "secondary": "#059669", "accent": "#3B82F6",
                "background": "#06120E", "surface": "#0D251D", "text_primary": "#ECFDF5", "text_muted": "#6EE7B7"
            }
        ],
        "typography": {
            "display_font": "Space Grotesk",
            "body_font": "Inter",
            "headline_style": "monospaced modern tech sans",
            "body_style": "clean documentation sans"
        },
        "ranked_archetypes": ["hero-text", "split-image-text", "offer-burst", "quote-card"],
        "imagery_strategy": "3d_vector_glassmorphic_cubes_dark_ui_telemetry",
        "shapes_patterns": ["matrix_grid_dots", "circuit_traces", "monospaced_code_tags", "terminal_prompts"],
        "copy_tone": "developer-first, crisp, high-velocity, modular, precise",
        "claims_policy": "benchmark_tested_sla_transparent",
        "brand_keywords": ["infrastructure", "deploy", "real-time", "api", "automated", "scalable"],
        "disallowed_terms": [
            "coffee", "brew", "roast", "beans", "barista", "hair salon", "pedicure"
        ],
        "custom_rules": [
            "Monospace accents for metrics or eyebrows.",
            "Accents feature glowing 1px border lines.",
            "Badge showcases version tag, release note, or speed metric."
        ],
        "sample_headlines": ["Ship 10x Faster", "Zero Downtime", "Next-Gen Engine", "Autonomous Scale"],
        "sample_ctas": ["Start Free Trial", "Read The Docs", "Deploy Now"]
    },

    "auto_detail": {
        "vertical_name": "Automotive & Auto Detailing",
        "style_family": "precision_gloss_aerodynamic",
        "palette": {
            "primary": "#EF4444",       # Tachometer red
            "secondary": "#F97316",     # Combustion orange
            "accent": "#38BDF8",        # Ceramic reflections
            "background": "#0A0B0E",    # Carbon chassis
            "surface": "#161922",
            "text_primary": "#F8FAFC",
            "text_muted": "#8A92A6"
        },
        "palette_options": [
            {
                "primary": "#3B82F6", "secondary": "#1D4ED8", "accent": "#60A5FA",
                "background": "#080C14", "surface": "#101828", "text_primary": "#F1F5F9", "text_muted": "#94A3B8"
            }
        ],
        "typography": {
            "display_font": "Oswald",
            "body_font": "Inter",
            "headline_style": "condensed high-speed sans bold",
            "body_style": "engineered legible sans"
        },
        "ranked_archetypes": ["split-image-text", "hero-text", "offer-burst", "centered-badge"],
        "imagery_strategy": "mirror_gloss_paint_water_beading_dramatic_headlight",
        "shapes_patterns": ["speedometer_arcs", "carbon_weave_textures", "hexagonal_mesh"],
        "copy_tone": "meticulous, high-octane, protective, flawless, commanding",
        "claims_policy": "coating_warranty_accredited_applicators",
        "brand_keywords": ["ceramic", "paint protection", "mirror finish", "restoration", "flawless", "hydrophobic"],
        "disallowed_terms": [
            "coffee", "brew", "beans", "barista", "latte", "single-origin", "teeth", "clinic"
        ],
        "custom_rules": [
            "Photography must emphasize paint reflections and water beading.",
            "Badge highlights warranty term (e.g. 5-Year Protection).",
            "Strong contrast between dark carbon background and red/ceramic accents."
        ],
        "sample_headlines": ["Mirror Finish", "Ceramic Shield", "Flawless Detail", "Ultimate Protection"],
        "sample_ctas": ["Book Detailing", "Get A Quote", "Protect Your Car"]
    },

    "travel_hospitality": {
        "vertical_name": "Travel, Resorts & Hospitality",
        "style_family": "tropical_horizon_wanderlust",
        "palette": {
            "primary": "#0EA5E9",       # Aegean azure
            "secondary": "#14B8A6",     # Tropical lagoon
            "accent": "#F59E0B",        # Golden sunset
            "background": "#0A141D",    # Deep ocean night
            "surface": "#132333",
            "text_primary": "#F0F9FF",
            "text_muted": "#93C5FD"
        },
        "palette_options": [
            {
                "primary": "#E11D48", "secondary": "#FB923C", "accent": "#FACC15",
                "background": "#14090E", "surface": "#26131C", "text_primary": "#FFF1F2", "text_muted": "#FDA4AF"
            }
        ],
        "typography": {
            "display_font": "Playfair Display",
            "body_font": "Inter",
            "headline_style": "evocative editorial serif italic",
            "body_style": "welcoming spacious sans"
        },
        "ranked_archetypes": ["split-image-text", "quote-card", "centered-badge", "hero-text"],
        "imagery_strategy": "sweeping_sunlit_coastal_villa_or_mountain_panorama",
        "shapes_patterns": ["horizon_lines", "sun_burst_arcs", "compass_accents", "stamp_borders"],
        "copy_tone": "unhurried, evocative, scenic, rejuvenating, unforgettable",
        "claims_policy": "accurate_amenities_all_inclusive_clarity",
        "brand_keywords": ["escape", "sanctuary", "horizon", "bespoke retreat", "island", "journey"],
        "disallowed_terms": [
            "coffee", "brew", "beans", "barista", "espresso", "teeth", "dentist", "car repair"
        ],
        "custom_rules": [
            "Scenic full-bleed horizon imagery.",
            "Eyebrow highlights location/destination name.",
            "Badge showcases seasonal booking window or luxury tier."
        ],
        "sample_headlines": ["Endless Horizon", "Island Sanctuary", "Unwind in Luxury", "The Great Escape"],
        "sample_ctas": ["Book Your Stay", "Explore Villas", "Plan Your Trip"]
    },

    "event_wedding": {
        "vertical_name": "Events, Weddings & Celebrations",
        "style_family": "romantic_celebratory_splendor",
        "palette": {
            "primary": "#E2B1B1",       # Champagne rose
            "secondary": "#C89595",     # Dusty blossom
            "accent": "#D4AF37",        # Vintage gilded gold
            "background": "#120B0D",    # Velvet midnight plum
            "surface": "#201418",
            "text_primary": "#FFF5F5",
            "text_muted": "#D6BCBC"
        },
        "palette_options": [
            {
                "primary": "#D4AF37", "secondary": "#F3E5AB", "accent": "#FFFFFF",
                "background": "#0D0C0A", "surface": "#1A1814", "text_primary": "#FAF8F5", "text_muted": "#B8B0A0"
            }
        ],
        "typography": {
            "display_font": "Playfair Display",
            "body_font": "Inter",
            "headline_style": "romantic high-contrast serif italic",
            "body_style": "delicate tracking humanist sans"
        },
        "ranked_archetypes": ["centered-badge", "quote-card", "split-image-text", "hero-text"],
        "imagery_strategy": "golden_hour_candlelight_floral_champagne_intimate",
        "shapes_patterns": ["delicate_botanical_filigree", "interlocking_rings", "scalloped_ribbons"],
        "copy_tone": "joyous, heartfelt, unforgettable, magical, intimate",
        "claims_policy": "venue_capacity_and_date_honesty",
        "brand_keywords": ["unforgettable", "celebration", "vows", "reception", "magic", "forever"],
        "disallowed_terms": [
            "coffee", "brew", "beans", "barista", "espresso", "teeth", "clinic", "oil change"
        ],
        "custom_rules": [
            "Delicate romantic framing and warm candlelight tones.",
            "Display date or venue capacity tastefully.",
            "Badge marks limited dates or exclusive packages."
        ],
        "sample_headlines": ["A Day Forever", "Unforgettable Moments", "Bespoke Celebrations", "Pure Romance"],
        "sample_ctas": ["Reserve Date", "Book Venue Tour", "Inquire Packages"]
    },

    "local_services": {
        "vertical_name": "Local Services, Trade & Repair",
        "style_family": "honest_craft_dependable",
        "palette": {
            "primary": "#2563EB",       # Reliable navy blue
            "secondary": "#F59E0B",     # Safety amber
            "accent": "#10B981",        # Verified green
            "background": "#0B1120",    # Solid steel night
            "surface": "#151F36",
            "text_primary": "#F8FAFC",
            "text_muted": "#94A3B8"
        },
        "palette_options": [
            {
                "primary": "#F97316", "secondary": "#EA580C", "accent": "#3B82F6",
                "background": "#0C0A09", "surface": "#1C1917", "text_primary": "#FAFAF9", "text_muted": "#A8A29E"
            }
        ],
        "typography": {
            "display_font": "Plus Jakarta Sans",
            "body_font": "Inter",
            "headline_style": "clean direct sans bold",
            "body_style": "solid high-contrast sans"
        },
        "ranked_archetypes": ["hero-text", "offer-burst", "centered-badge", "split-image-text"],
        "imagery_strategy": "licensed_technician_clean_uniform_real_tools_on_site",
        "shapes_patterns": ["shield_badges", "check_marks", "striped_caution_rules", "star_ratings"],
        "copy_tone": "dependable, transparent, swift, honest, community-first",
        "claims_policy": "licensed_insured_pricing_upfront",
        "brand_keywords": ["licensed", "insured", "24/7 emergency", "guaranteed", "on-time", "certified"],
        "disallowed_terms": [
            "coffee", "brew", "beans", "barista", "latte", "single-origin", "runway", "couture"
        ],
        "custom_rules": [
            "Prominently display phone number and service guarantee.",
            "Badge showcases 24/7 service or 5-star rating.",
            "Zero marketing fluff; focus on speed, reliability, and pricing."
        ],
        "sample_headlines": ["On Time Every Time", "Certified Experts", "Fast Local Service", "Done Right"],
        "sample_ctas": ["Call For Service", "Get Free Estimate", "Book Appointment"]
    }
}


# ---------------------------------------------------------------------------
# Vertical Resolution & Classification
# ---------------------------------------------------------------------------

def resolve_vertical(
    industry_primary: str,
    industry_sub: str = "",
    business_name: str = "",
    offerings_text: str = ""
) -> str:
    """Classifies incoming business signals into one of the 14 core verticals.
    Guarantees that non-coffee businesses NEVER resolve to cafe_coffee.
    """
    signals = f"{industry_primary} {industry_sub} {business_name} {offerings_text}".lower()

    # Priority 1: Sneakers & Streetwear
    if any(k in signals for k in ("sneaker", "streetwear", "kicks", "footwear", "shoes", "hypebeast", "colorway")):
        return "sneakers_streetwear"

    # Priority 2: Dental, Medical & Clinic
    if any(k in signals for k in ("clinic", "dental", "dentist", "doctor", "health", "medical", "orthodont", "teeth", "smile", "pharma")):
        return "clinic_healthcare"

    # Priority 3: Salon, Spa & Beauty
    if any(k in signals for k in ("salon", "spa", "hair", "barber", "nails", "beauty", "esthetics", "facial", "massage", "skincare")):
        return "salon_spa"

    # Priority 4: Gym & Fitness
    if any(k in signals for k in ("gym", "fitness", "crossfit", "trainer", "workout", "pilates", "yoga", "boxing", "athletic")):
        return "gym_fitness"

    # Priority 5: Real Estate
    if any(k in signals for k in ("real estate", "realtor", "property", "broker", "realty", "homes", "condo", "architect", "penthouse")):
        return "real_estate"

    # Priority 6: Jewelry & Luxury
    if any(k in signals for k in ("jewelry", "jeweller", "watches", "diamond", "gold", "gemstone", "luxury watch")):
        return "jewelry_luxury"

    # Priority 7: Automotive & Detailing
    if any(k in signals for k in ("auto", "detailing", "mechanic", "car wash", "motors", "dealership", "ceramic coating", "paint protection")):
        return "auto_detail"

    # Priority 8: Boutique & Fashion
    if any(k in signals for k in ("boutique", "fashion", "apparel", "clothing", "couture", "designer wear", "garment", "outfit")):
        return "boutique_fashion"

    # Priority 9: Education & Tutoring
    if any(k in signals for k in ("education", "tutoring", "tutor", "academy", "school", "course", "learning", "coaching", "classes")):
        return "education_tutoring"

    # Priority 10: Tech & SaaS
    if any(k in signals for k in ("software", "saas", "tech", "ai", "cloud", "developer", "platform", "app", "startup", "code")):
        return "tech_saas"

    # Priority 11: Travel & Hospitality
    if any(k in signals for k in ("travel", "hotel", "resort", "tour", "hospitality", "vacation", "villa", "getaway")):
        return "travel_hospitality"

    # Priority 12: Events & Weddings
    if any(k in signals for k in ("wedding", "events", "celebration", "party", "venue", "catering", "banquet")):
        return "event_wedding"

    # Priority 13: Local Trade & Services
    if any(k in signals for k in ("plumbing", "electrician", "hvac", "roofing", "contractor", "cleaning", "pest control", "locksmith", "handyman")):
        return "local_services"

    # Priority 14: Coffee & Cafe (ONLY if explicit coffee signals exist!)
    if any(k in signals for k in ("coffee", "cafe", "roaster", "roastery", "espresso", "latte", "cold brew", "pour-over", "tea room")):
        return "cafe_coffee"

    # Default fallback: safe modern local services, NEVER coffee
    return "local_services"


def build_creative_direction(
    vertical_key: str,
    business_name: str = "",
    custom_primary_color: Optional[str] = None,
    custom_secondary_color: Optional[str] = None,
    custom_accent_color: Optional[str] = None,
    custom_bg_color: Optional[str] = None,
    custom_display_font: Optional[str] = None,
    custom_body_font: Optional[str] = None,
    custom_tone: Optional[str] = None
) -> CreativeDirection:
    """Builds a rich CreativeDirection specification for a business, overlaying
    custom client branding if provided, while maintaining rigorous design harmony.
    """
    raw_cat = VERTICAL_CATALOG.get(vertical_key, VERTICAL_CATALOG["local_services"])

    # Base palette
    base_p = raw_cat["palette"]
    palette = ColorPalette(
        primary=custom_primary_color or base_p["primary"],
        secondary=custom_secondary_color or base_p["secondary"],
        accent=custom_accent_color or base_p["accent"],
        background=custom_bg_color or base_p["background"],
        surface=base_p["surface"],
        text_primary=base_p["text_primary"],
        text_muted=base_p["text_muted"]
    )

    palette_options = [
        ColorPalette(**opt) for opt in raw_cat.get("palette_options", [])
    ]

    # Typography
    base_typo = raw_cat["typography"]
    typography = TypographyPairing(
        display_font=custom_display_font or base_typo["display_font"],
        body_font=custom_body_font or base_typo["body_font"],
        headline_style=base_typo["headline_style"],
        body_style=base_typo["body_style"]
    )

    # Contextual sample headlines with business name if available
    sample_headlines = list(raw_cat.get("sample_headlines", []))
    if business_name:
        sample_headlines.insert(0, f"{business_name} Signature")

    return CreativeDirection(
        vertical=vertical_key,
        vertical_name=raw_cat["vertical_name"],
        style_family=raw_cat["style_family"],
        palette=palette,
        palette_options=palette_options,
        typography=typography,
        ranked_archetypes=raw_cat.get("ranked_archetypes", ["hero-text", "split-image-text"]),
        imagery_strategy=raw_cat.get("imagery_strategy", "clean_product_hero"),
        shapes_patterns=raw_cat.get("shapes_patterns", []),
        copy_tone=custom_tone or raw_cat.get("copy_tone", "professional, engaging, clear"),
        claims_policy=raw_cat.get("claims_policy", "standard"),
        brand_keywords=raw_cat.get("brand_keywords", []),
        disallowed_terms=raw_cat.get("disallowed_terms", []),
        custom_rules=raw_cat.get("custom_rules", []),
        sample_headlines=sample_headlines,
        sample_ctas=raw_cat.get("sample_ctas", ["Learn More", "Get Started"])
    )
