"""The 7 Layout Archetypes for Poster Design Agent.

Direct implementation of Section 4.5 (Layout archetypes) of the Poster Design pack:
1. hero-text (bold announcements, software/AI, vision)
2. split-image-text (food & dining, culinary, products, physical spaces)
3. centered-badge (festivals, brand anniversaries, grand openings)
4. offer-burst (flash sales, high-urgency discounts)
5. quote-card (testimonials, thought leadership, reviews)
6. event-ticket (workshops, conferences, summits, dates)
7. minimal-editorial (luxury boutique, architecture, refined aesthetics)
"""
from typing import Dict, Any, Optional
from .spec import PosterSpec, CanvasConfig, BackgroundConfig, FontsConfig, PosterElement, OverlayScrim, SelfCheck


from .linter import contrast_ratio


def _contrast_cta_color(bg_hex: str) -> str:
    """Returns #FFFFFF or #0F172A depending on which has better WCAG contrast on bg_hex."""
    try:
        return "#FFFFFF" if contrast_ratio(bg_hex, "#FFFFFF") >= 3.0 else "#0F172A"
    except Exception:
        return "#FFFFFF"


def create_hero_text_spec(
    headline: str = "Empower Your Brand with Autonomous AI Agents",
    eyebrow: str = "NEXT-GENERATION MARKETING",
    subhead: str = "Continuous market research, creative campaigns, and automated publishing.",
    cta: str = "Start Free Trial",
    contact: str = "nexus.studio | @nexusstudio",
    primary_color: str = "#6366F1",
    bg_color: str = "#0B0F19",
    surface_color: str = "#1E293B"
) -> PosterSpec:
    """Archetype 1: hero-text. Zone map: eyebrow 6-10%, headline 14-44%, shape 46-72%, subhead 74-82%, CTA 86-93%."""
    cta_color = _contrast_cta_color(primary_color)
    return PosterSpec(
        canvas=CanvasConfig(width=1080, height=1350, scale=1.0, margin=64),
        background=BackgroundConfig(type="gradient", value=f"{bg_color} -> #030712"),
        fonts=FontsConfig(display="Playfair Display", text="Inter"),
        reading_order=["eyebrow", "headline", "card_bg", "subhead", "cta_bg", "cta_text", "contact"],
        focal_element="headline",
        elements=[
            PosterElement(
                id="eyebrow",
                type="text",
                z=3,
                x=64,
                y=96,
                w=952,
                h=40,
                text=eyebrow,
                font="text",
                weight=700,
                size=28,
                color=primary_color,
                transform="uppercase",
                letter_spacing="0.08em"
            ),
            PosterElement(
                id="headline",
                type="text",
                z=3,
                x=64,
                y=160,
                w=952,
                h=320,
                text=headline,
                font="display",
                weight=800,
                size=76,
                line_height=1.1,
                color="#F8FAFC"
            ),
            PosterElement(
                id="card_bg",
                type="shape",
                z=1,
                x=64,
                y=520,
                w=952,
                h=400,
                radius=24,
                fill=surface_color,
                stroke=primary_color,
                stroke_width=2,
                decorative=True
            ),
            PosterElement(
                id="subhead",
                type="text",
                z=3,
                x=104,
                y=568,
                w=872,
                h=144,
                text=subhead,
                font="text",
                weight=400,
                size=36,
                line_height=1.4,
                color="#E2E8F0"
            ),
            PosterElement(
                id="cta_bg",
                type="shape",
                z=2,
                x=64,
                y=1160,
                w=416,
                h=88,
                radius=44,
                fill=primary_color
            ),

            PosterElement(
                id="cta_text",
                type="text",
                z=3,
                x=64,
                y=1160,
                w=416,
                h=88,
                text=f"{cta} →",
                font="text",
                weight=700,
                size=32,
                line_height=2.7,
                align="center",
                color=cta_color
            ),
            PosterElement(
                id="contact",
                type="text",
                z=3,
                x=520,
                y=1184,
                w=496,
                h=48,
                text=contact,
                font="text",
                weight=500,
                size=28,
                align="right",
                color="#94A3B8"
            ),
        ]
    )


def create_split_image_text_spec(
    headline: str = "Step Into Artistry.\nCrafted With Vision.",
    category: str = "FEATURED COLLECTION",
    subhead: str = "Engineered for style, comfort, and bold performance.",
    cta: str = "Shop Collection",
    business_name: str = "Your Brand",
    primary_color: str = "#6366F1",
    bg_color: str = "#0F172A"
) -> PosterSpec:
    """Archetype 2: Full-Bleed Hero Image + Overlay Text (Part 3 Corrected Spec)."""
    return PosterSpec(
        canvas=CanvasConfig(width=1080, height=1350, scale=1.0, margin=80),
        background=BackgroundConfig(type="solid", value=bg_color),
        fonts=FontsConfig(display="Fraunces", text="Inter"),
        reading_order=["category_tag", "showcase_badge_bg", "showcase_badge", "headline", "subhead", "cta_bg", "cta_text", "business_name"],
        focal_element="headline",
        elements=[
            PosterElement(
                id="category_tag",
                type="text",
                z=3,
                x=80,
                y=80,
                w=640,
                h=40,
                text=category,
                font="text",
                weight=700,
                size=26,
                color=primary_color,
                letter_spacing="0.12em"
            ),
            PosterElement(
                id="showcase_badge_bg",
                type="shape",
                z=2,
                x=760,
                y=80,
                w=240,
                h=48,
                radius=24,
                fill=primary_color,
                decorative=True
            ),
            PosterElement(
                id="showcase_badge",
                type="text",
                z=3,
                x=760,
                y=80,
                w=240,
                h=48,
                text="✦ FEATURED",
                font="text",
                size=24,
                weight=700,
                align="center",
                color=_contrast_cta_color(primary_color)
            ),
            PosterElement(
                id="headline",
                type="text",
                z=3,
                x=80,
                y=864,
                w=920,
                h=216,
                text=headline,
                font="display",
                weight=700,
                size=64,
                line_height=1.12,
                color="#FFF1DF"
            ),
            PosterElement(
                id="subhead",
                type="text",
                z=3,
                x=80,
                y=1088,
                w=920,
                h=96,
                text=subhead,
                font="text",
                weight=400,
                size=32,
                line_height=1.4,
                color="#CDB9A3"
            ),
            PosterElement(
                id="cta_bg",
                type="shape",
                z=2,
                x=80,
                y=1184,
                w=360,
                h=80,
                radius=40,
                fill=primary_color
            ),
            PosterElement(
                id="cta_text",
                type="text",
                z=3,
                x=80,
                y=1184,
                w=360,
                h=80,
                text=cta,
                font="text",
                weight=700,
                size=32,
                line_height=2.5,
                align="center",
                color=_contrast_cta_color(primary_color)
            ),
            PosterElement(
                id="business_name",
                type="text",
                z=3,
                x=560,
                y=1208,
                w=440,
                h=48,
                text=business_name,
                font="text",
                weight=600,
                size=26,
                align="right",
                color="#CDB9A3"
            ),
        ]
    )



def create_centered_badge_spec(
    headline: str = "Auspicious Celebration & Festive Greetings",
    eyebrow: str = "FESTIVAL CELEBRATION",
    badge_title: str = "HAPPY CELEBRATION",
    subhead: str = "May this season bring radiant prosperity, joy, and peace to your family.",
    cta: str = "Celebrate With Us",
    business_name: str = "Royal Heritage Co.",
    primary_color: str = "#EAB308",
    bg_color: str = "#0B0712"
) -> PosterSpec:
    """Archetype 3: centered-badge. Best for celebrations, festivals and grand openings."""
    return PosterSpec(
        canvas=CanvasConfig(width=1080, height=1350, scale=1.0, margin=64),
        background=BackgroundConfig(type="gradient", value=f"{bg_color} -> #1E102E"),
        fonts=FontsConfig(display="Playfair Display", text="Inter"),
        reading_order=["eyebrow", "badge_circle", "headline", "subhead", "cta_bg", "cta_text"],
        focal_element="badge_circle",
        elements=[
            PosterElement(
                id="eyebrow",
                type="text",
                z=3,
                x=64,
                y=96,
                w=952,
                h=40,
                text=eyebrow,
                font="text",
                weight=700,
                size=28,
                align="center",
                color=primary_color,
                transform="uppercase",
                letter_spacing="0.08em"
            ),
            PosterElement(
                id="badge_circle",
                type="shape",
                z=1,
                x=240,
                y=180,
                w=600,
                h=440,
                radius=40,
                fill="#231435",
                stroke=primary_color,
                stroke_width=3
            ),
            PosterElement(
                id="badge_inner_title",
                type="text",
                z=3,
                x=280,
                y=340,
                w=520,
                h=120,
                text=badge_title,
                font="display",
                weight=800,
                size=52,
                align="center",
                color="#FEF3C7"
            ),
            PosterElement(
                id="headline",
                type="text",
                z=3,
                x=64,
                y=680,
                w=952,
                h=180,
                text=headline,
                font="display",
                weight=700,
                size=64,
                line_height=1.15,
                align="center",
                color="#FFFBEB"
            ),
            PosterElement(
                id="subhead",
                type="text",
                z=3,
                x=96,
                y=890,
                w=888,
                h=140,
                text=subhead,
                font="text",
                weight=400,
                size=32,
                line_height=1.4,
                align="center",
                color="#E9D5FF"
            ),
            PosterElement(
                id="cta_bg",
                type="shape",
                z=2,
                x=340,
                y=1160,
                w=400,
                h=88,
                radius=44,
                fill=primary_color
            ),
            PosterElement(
                id="cta_text",
                type="text",
                z=3,
                x=340,
                y=1160,
                w=400,
                h=88,
                text=cta,
                font="text",
                weight=700,
                size=32,
                line_height=2.7,
                align="center",
                color="#000000"
            ),
        ]
    )


def create_offer_burst_spec(
    headline: str = "Flat 50% Off Everything This Weekend",
    offer_value: str = "50% OFF",
    subhead: str = "Upgrade your business workspace today. No promo code needed.",
    cta: str = "Claim Offer Now",
    fine_print: str = "Valid through Sunday midnight. Terms apply.",
    primary_color: str = "#EF4444",
    bg_color: str = "#0A0A0A"
) -> PosterSpec:
    """Archetype 4: offer-burst. Giant offer value in display-xl."""
    burst_text_color = _contrast_cta_color(primary_color)
    return PosterSpec(
        canvas=CanvasConfig(width=1080, height=1350, scale=1.0, margin=64),
        background=BackgroundConfig(type="gradient", value=f"{bg_color} -> #1C0A0A"),
        fonts=FontsConfig(display="Playfair Display", text="Inter"),
        reading_order=["eyebrow", "burst_bg", "burst_text", "headline", "subhead", "cta_bg", "cta_text", "fine_print"],
        focal_element="burst_text",
        elements=[
            PosterElement(
                id="eyebrow",
                type="text",
                z=3,
                x=64,
                y=96,
                w=952,
                h=40,
                text="FLASH SALE • LIMITED WINDOW",
                font="text",
                weight=700,
                size=28,
                color="#FCA5A5",
                transform="uppercase",
                letter_spacing="0.08em"
            ),
            PosterElement(
                id="burst_bg",
                type="shape",
                z=1,
                x=64,
                y=168,
                w=952,
                h=344,
                radius=32,
                fill=primary_color
            ),
            PosterElement(
                id="burst_text",
                type="text",
                z=3,
                x=64,
                y=232,
                w=952,
                h=200,
                text=offer_value,
                font="display",
                weight=900,
                size=136,
                align="center",
                color=burst_text_color
            ),
            PosterElement(
                id="headline",
                type="text",
                z=3,
                x=64,
                y=560,
                w=952,
                h=224,
                text=headline,
                font="display",
                weight=800,
                size=72,
                line_height=1.1,
                color="#F8FAFC"
            ),
            PosterElement(
                id="subhead",
                type="text",
                z=3,
                x=64,
                y=824,
                w=952,
                h=144,
                text=subhead,
                font="text",
                weight=400,
                size=32,
                line_height=1.4,
                color="#CBD5E1"
            ),
            PosterElement(
                id="cta_bg",
                type="shape",
                z=2,
                x=64,
                y=1120,
                w=440,
                h=88,
                radius=44,
                fill=primary_color
            ),
            PosterElement(
                id="cta_text",
                type="text",
                z=3,
                x=64,
                y=1120,
                w=440,
                h=88,
                text=f"{cta} →",
                font="text",
                weight=700,
                size=32,
                line_height=2.7,
                align="center",
                color=burst_text_color
            ),
            PosterElement(
                id="fine_print",
                type="text",
                z=3,
                x=64,
                y=1240,
                w=952,
                h=32,
                text=fine_print,
                font="text",
                weight=400,
                size=24,
                color="#94A3B8"
            ),
        ]
    )


def create_quote_card_spec(
    quote: str = "Nexus Studio replaced three manual marketing agencies and cut our campaign turnaround time by 80%.",
    attribution: str = "Aarav Sharma — Head of Growth, Retail Ventures",
    eyebrow: str = "CLIENT TESTIMONIAL",
    primary_color: str = "#10B981",
    bg_color: str = "#06281E"
) -> PosterSpec:
    """Archetype 5: quote-card. Oversized quotes with verified attribution."""
    return PosterSpec(
        canvas=CanvasConfig(width=1080, height=1350, scale=1.0, margin=64),
        background=BackgroundConfig(type="gradient", value=f"{bg_color} -> #02140F"),
        fonts=FontsConfig(display="Playfair Display", text="Inter"),
        reading_order=["eyebrow", "quote_mark", "quote_text", "divider", "attribution"],
        focal_element="quote_text",
        elements=[
            PosterElement(
                id="eyebrow",
                type="text",
                z=3,
                x=64,
                y=96,
                w=952,
                h=40,
                text=f"★★★★★ • {eyebrow}",
                font="text",
                weight=700,
                size=28,
                color="#A7F3D0",
                transform="uppercase",
                letter_spacing="0.08em"
            ),
            PosterElement(
                id="quote_mark",
                type="text",
                z=1,
                x=64,
                y=160,
                w=200,
                h=160,
                text="“",
                font="display",
                weight=900,
                size=120,
                line_height=1.0,
                color=primary_color
            ),
            PosterElement(
                id="quote_text",
                type="text",
                z=3,
                x=64,
                y=336,
                w=952,
                h=544,
                text=quote,
                font="display",
                weight=600,
                size=57,
                line_height=1.3,
                color="#ECFDF5"
            ),
            PosterElement(
                id="divider",
                type="line",
                z=2,
                x=64,
                y=960,
                w=320,
                h=8,
                stroke=primary_color,
                stroke_width=4
            ),
            PosterElement(
                id="attribution",
                type="text",
                z=3,
                x=64,
                y=1000,
                w=952,
                h=96,
                text=attribution,
                font="text",
                weight=500,
                size=32,
                line_height=1.35,
                color="#D1FAE5"
            ),
        ]
    )


def create_event_ticket_spec(
    headline: str = "Global Artificial Intelligence Summit 2026",
    eyebrow: str = "KEYNOTE CONFERENCE",
    date_badge: str = "NOV 14-16",
    venue: str = "Moscone Convention Center • San Francisco, CA",
    cta: str = "Reserve Delegate Pass",
    primary_color: str = "#3B82F6",
    bg_color: str = "#050B18"
) -> PosterSpec:
    """Archetype 6: event-ticket. Prominent date ticket block with venue schedule."""
    ticket_text_color = _contrast_cta_color(primary_color)
    return PosterSpec(
        canvas=CanvasConfig(width=1080, height=1350, scale=1.0, margin=64),
        background=BackgroundConfig(type="gradient", value=f"{bg_color} -> #0A1329"),
        fonts=FontsConfig(display="Playfair Display", text="Inter"),
        reading_order=["eyebrow", "date_block", "date_text", "headline", "venue", "ticket_divider", "cta_bg", "cta_text"],
        focal_element="date_block",
        elements=[
            PosterElement(
                id="eyebrow",
                type="text",
                z=3,
                x=64,
                y=96,
                w=952,
                h=40,
                text=f"✦ {eyebrow}",
                font="text",
                weight=700,
                size=28,
                color=primary_color,
                letter_spacing="0.08em"
            ),
            PosterElement(
                id="date_block",
                type="shape",
                z=1,
                x=64,
                y=160,
                w=440,
                h=144,
                radius=24,
                fill=primary_color
            ),
            PosterElement(
                id="date_text",
                type="text",
                z=3,
                x=64,
                y=192,
                w=440,
                h=80,
                text=date_badge,
                font="display",
                weight=900,
                size=48,
                align="center",
                color=ticket_text_color
            ),
            PosterElement(
                id="headline",
                type="text",
                z=3,
                x=64,
                y=360,
                w=952,
                h=336,
                text=headline,
                font="display",
                weight=800,
                size=72,
                line_height=1.12,
                color="#F8FAFC"
            ),
            PosterElement(
                id="venue",
                type="text",
                z=3,
                x=64,
                y=736,
                w=952,
                h=120,
                text=f"📍 {venue}",
                font="text",
                weight=500,
                size=32,
                line_height=1.4,
                color="#93C5FD"
            ),
            PosterElement(
                id="ticket_divider",
                type="line",
                z=2,
                x=64,
                y=936,
                w=952,
                h=8,
                stroke="#1E3A8A",
                stroke_width=2
            ),
            PosterElement(
                id="cta_bg",
                type="shape",
                z=2,
                x=64,
                y=1120,
                w=480,
                h=88,
                radius=44,
                fill=primary_color
            ),
            PosterElement(
                id="cta_text",
                type="text",
                z=3,
                x=64,
                y=1120,
                w=480,
                h=88,
                text=f"{cta} →",
                font="text",
                weight=700,
                size=32,
                line_height=2.7,
                align="center",
                color=ticket_text_color
            ),
        ]
    )


def create_minimal_editorial_spec(
    headline: str = "Silence is the Ultimate Luxury",
    subhead: str = "Architectural sanctuaries designed for serenity, space, and natural light.",
    cta: str = "Discover Monograph",
    brand_signature: str = "ATELIER NORDIC",
    primary_color: str = "#78716C",
    bg_color: str = "#F5F5F4"
) -> PosterSpec:
    """Archetype 7: minimal-editorial. Expansive whitespace, quiet luxury."""
    try:
        is_dark = contrast_ratio(bg_color, "#0F172A") < contrast_ratio(bg_color, "#FFFFFF")
    except Exception:
        is_dark = False
    text_color = "#FAFAF9" if is_dark else "#1C1917"
    muted_color = "#D6D3D1" if is_dark else "#44403C"
    try:
        sig_color = primary_color if contrast_ratio(bg_color, primary_color) >= 3.0 else text_color
    except Exception:
        sig_color = text_color

    return PosterSpec(
        canvas=CanvasConfig(width=1080, height=1350, scale=1.0, margin=64),
        background=BackgroundConfig(type="solid", value=bg_color),
        fonts=FontsConfig(display="Playfair Display", text="Inter"),
        reading_order=["brand_signature", "headline", "editorial_line", "subhead", "cta_text"],
        focal_element="headline",
        elements=[
            PosterElement(
                id="brand_signature",
                type="text",
                z=3,
                x=64,
                y=120,
                w=952,
                h=40,
                text=brand_signature,
                font="text",
                weight=600,
                size=24,
                color=sig_color,
                letter_spacing="0.12em"
            ),
            PosterElement(
                id="headline",
                type="text",
                z=3,
                x=64,
                y=384,
                w=952,
                h=384,
                text=headline,
                font="display",
                weight=500,
                size=72,
                line_height=1.15,
                color=text_color
            ),
            PosterElement(
                id="editorial_line",
                type="line",
                z=2,
                x=64,
                y=824,
                w=160,
                h=8,
                stroke=sig_color,
                stroke_width=2
            ),
            PosterElement(
                id="subhead",
                type="text",
                z=3,
                x=64,
                y=864,
                w=760,
                h=144,
                text=subhead,
                font="text",
                weight=400,
                size=32,
                line_height=1.5,
                color=muted_color
            ),
            PosterElement(
                id="cta_text",
                type="text",
                z=3,
                x=64,
                y=1160,
                w=440,
                h=64,
                text=f"{cta} —",
                font="text",
                weight=600,
                size=32,
                color=text_color
            ),
        ]
    )


def create_product_cutout_spec(
    headline: str = "Engineered for Velocity and Agility",
    eyebrow: str = "FEATURED COLLECTION",
    subhead: str = "Ultra-responsive precision architecture crafted for daily excellence.",
    cta: str = "Explore Collection",
    product_name: str = "Signature Series",
    primary_color: str = "#EF4444",
    bg_color: str = "#0F172A",
    variant: str = "floating_shadow"
) -> PosterSpec:
    """Archetype 6: product-cutout. Focal point is the cutout product centered on stage."""
    v = variant.lower().replace("-", "_")
    cta_color = _contrast_cta_color(primary_color)

    # Common base configuration
    canvas = CanvasConfig(width=1080, height=1350, scale=1.0, margin=64)
    fonts = FontsConfig(display="Space Grotesk", text="Inter")
    elements = [
        PosterElement(
            id="eyebrow",
            type="text",
            z=3,
            x=64,
            y=96,
            w=952,
            h=40,
            text=f"✦ {eyebrow.upper()}",
            font="text",
            weight=700,
            size=28,
            color=primary_color,
            letter_spacing="0.08em"
        ),
        PosterElement(
            id="headline",
            type="text",
            z=3,
            x=64,
            y=160,
            w=952,
            h=232,
            text=headline,
            font="display",
            weight=800,
            size=64,
            line_height=1.12,
            color="#F8FAFC"
        )
    ]

    if v == "neon_glow":
        elements.extend([
            PosterElement(
                id="halo_ring",
                type="shape",
                z=1,
                x=200,
                y=416,
                w=680,
                h=464,
                radius=40,
                fill="#1E293B",
                stroke=primary_color,
                stroke_width=4,
                decorative=True
            ),
            PosterElement(
                id="product_hero",
                type="shape",
                z=2,
                x=240,
                y=440,
                w=600,
                h=416,
                radius=24,
                fill="#334155",
                stroke=primary_color,
                stroke_width=2
            ),
        ])
    elif v == "pedestal_stage":
        elements.extend([
            PosterElement(
                id="pedestal_base",
                type="shape",
                z=1,
                x=160,
                y=768,
                w=760,
                h=112,
                radius=16,
                fill="#1E293B",
                stroke=primary_color,
                stroke_width=2,
                decorative=True
            ),
            PosterElement(
                id="product_hero",
                type="shape",
                z=2,
                x=240,
                y=416,
                w=600,
                h=384,
                radius=24,
                fill="#334155"
            ),
        ])
    else:  # floating_shadow (default)
        elements.extend([
            PosterElement(
                id="stage_shadow",
                type="shape",
                z=1,
                x=120,
                y=416,
                w=840,
                h=472,
                radius=32,
                fill="#1E293B",
                stroke=primary_color,
                stroke_width=2,
                decorative=True
            ),
            PosterElement(
                id="product_hero",
                type="shape",
                z=2,
                x=184,
                y=440,
                w=712,
                h=424,
                radius=24,
                fill="#334155"
            ),
        ])

    elements.extend([
        PosterElement(
            id="subhead",
            type="text",
            z=3,
            x=64,
            y=920,
            w=952,
            h=144,
            text=subhead,
            font="text",
            weight=400,
            size=32,
            line_height=1.4,
            color="#CBD5E1"
        ),
        PosterElement(
            id="cta_bg",
            type="shape",
            z=2,
            x=64,
            y=1144,
            w=400,
            h=88,
            radius=44,
            fill=primary_color
        ),
        PosterElement(
            id="cta_text",
            type="text",
            z=3,
            x=64,
            y=1144,
            w=400,
            h=88,
            text=f"{cta} →",
            font="text",
            weight=700,
            size=32,
            line_height=2.7,
            align="center",
            color=cta_color
        ),
        PosterElement(
            id="product_badge",
            type="text",
            z=3,
            x=520,
            y=1168,
            w=496,
            h=48,
            text=f"✦ {product_name.upper()}",
            font="text",
            weight=600,
            size=28,
            align="right",
            color="#94A3B8"
        )
    ])

    return PosterSpec(
        canvas=canvas,
        background=BackgroundConfig(type="gradient", value=f"{bg_color} -> #030712"),
        fonts=fonts,
        reading_order=["eyebrow", "headline", "product_hero", "subhead", "cta_bg", "cta_text", "product_badge"],
        focal_element="product_hero",
        elements=elements
    )


def create_grid_multi_item_spec(
    headline: str = "Our Signature Collection & Services",
    eyebrow: str = "SERVICE MENU & SPECIALTIES",
    subhead: str = "Curated offerings and specialized solutions tailored to your unique lifestyle.",
    cta: str = "Explore Offerings",
    business_name: str = "Prime Studio",
    primary_color: str = "#059669",
    bg_color: str = "#062018",
    variant: str = "3_item_showcase"
) -> PosterSpec:
    """Archetype 7: grid-multi-item. Multi-card quadrant or 3-column collection."""
    v = variant.lower().replace("-", "_")
    cta_color = _contrast_cta_color(primary_color)

    canvas = CanvasConfig(width=1080, height=1350, scale=1.0, margin=64)
    fonts = FontsConfig(display="Playfair Display", text="Inter")
    elements = [
        PosterElement(
            id="eyebrow",
            type="text",
            z=3,
            x=64,
            y=96,
            w=952,
            h=40,
            text=f"✦ {eyebrow.upper()}",
            font="text",
            weight=700,
            size=28,
            color=primary_color,
            letter_spacing="0.08em"
        ),
        PosterElement(
            id="headline",
            type="text",
            z=3,
            x=64,
            y=160,
            w=952,
            h=160,
            text=headline,
            font="display",
            weight=800,
            size=64,
            line_height=1.12,
            color="#F8FAFC"
        ),
        PosterElement(
            id="subhead",
            type="text",
            z=3,
            x=64,
            y=344,
            w=952,
            h=96,
            text=subhead,
            font="text",
            weight=400,
            size=32,
            line_height=1.4,
            color="#CBD5E1"
        ),
        PosterElement(
            id="grid_container",
            type="shape",
            z=1,
            x=64,
            y=464,
            w=952,
            h=616,
            radius=24,
            fill="#0F2D23",
            stroke=primary_color,
            stroke_width=2,
            decorative=True
        )
    ]

    if v == "4_lookbook":
        # 2x2 grid
        elements.extend([
            PosterElement(id="tile_1", type="shape", z=2, x=96, y=496, w=424, h=264, radius=16, fill="#081C15", stroke=primary_color, stroke_width=1),
            PosterElement(id="tile_2", type="shape", z=2, x=560, y=496, w=424, h=264, radius=16, fill="#081C15", stroke=primary_color, stroke_width=1),
            PosterElement(id="tile_3", type="shape", z=2, x=96, y=784, w=424, h=264, radius=16, fill="#081C15", stroke=primary_color, stroke_width=1),
            PosterElement(id="tile_4", type="shape", z=2, x=560, y=784, w=424, h=264, radius=16, fill="#081C15", stroke=primary_color, stroke_width=1),
        ])
    elif v == "2x2_comparison":
        # Dual transformation panels (Before & After)
        elements.extend([
            PosterElement(id="tile_before", type="shape", z=2, x=96, y=496, w=424, h=552, radius=16, fill="#081C15", stroke="#334155", stroke_width=2),
            PosterElement(id="tile_after", type="shape", z=2, x=560, y=496, w=424, h=552, radius=16, fill="#081C15", stroke=primary_color, stroke_width=3),
        ])
    else:  # 3_item_showcase (default)
        elements.extend([
            PosterElement(id="tile_1", type="shape", z=2, x=96, y=496, w=272, h=552, radius=16, fill="#081C15", stroke=primary_color, stroke_width=1),
            PosterElement(id="tile_2", type="shape", z=2, x=404, y=496, w=272, h=552, radius=16, fill="#081C15", stroke=primary_color, stroke_width=1),
            PosterElement(id="tile_3", type="shape", z=2, x=712, y=496, w=272, h=552, radius=16, fill="#081C15", stroke=primary_color, stroke_width=1),
        ])

    elements.extend([
        PosterElement(
            id="cta_bg",
            type="shape",
            z=2,
            x=340,
            y=1144,
            w=400,
            h=88,
            radius=44,
            fill=primary_color
        ),
        PosterElement(
            id="cta_text",
            type="text",
            z=3,
            x=340,
            y=1144,
            w=400,
            h=88,
            text=f"{cta} →",
            font="text",
            weight=700,
            size=32,
            line_height=2.7,
            align="center",
            color=cta_color
        )
    ])

    return PosterSpec(
        canvas=canvas,
        background=BackgroundConfig(type="gradient", value=f"{bg_color} -> #02120C"),
        fonts=fonts,
        reading_order=["eyebrow", "headline", "subhead", "grid_container", "cta_bg", "cta_text"],
        focal_element="grid_container",
        elements=elements
    )


def create_stats_metric_spec(
    stat_number: str = "99.4%",
    stat_label: str = "PATIENT SATISFACTION RATE",
    headline: str = "Proven Outcomes Powered by Advanced Clinical Technology",
    subhead: str = "Over 12,000 successful smile restorations delivered with zero downtime.",
    cta: str = "Schedule Exam",
    business_name: str = "Apex Health",
    primary_color: str = "#10B981",
    bg_color: str = "#06221A",
    variant: str = "giant_number"
) -> PosterSpec:
    """Archetype 9: stats-metric. Massive numerical proof callout anchored by empirical data."""
    canvas = CanvasConfig(width=1080, height=1350, scale=1.0, margin=64)
    fonts = FontsConfig(display="Space Grotesk", text="Inter")
    v = variant.lower().replace("-", "_")

    elements = [
        PosterElement(
            id="eyebrow",
            type="text",
            z=3,
            x=64,
            y=96,
            w=952,
            h=40,
            text="✦ VERIFIED CLINICAL OUTCOMES",
            font="text",
            weight=700,
            size=28,
            color=primary_color,
            letter_spacing="0.08em"
        ),
        PosterElement(
            id="stat_number",
            type="text",
            z=3,
            x=64,
            y=160,
            w=952,
            h=200,
            text=stat_number,
            font="display",
            weight=900,
            size=136,
            align="center",
            color=primary_color
        ),
        PosterElement(
            id="stat_label",
            type="text",
            z=3,
            x=64,
            y=376,
            w=952,
            h=64,
            text=stat_label,
            font="text",
            weight=700,
            size=32,
            align="center",
            color="#A7F3D0",
            letter_spacing="0.06em"
        ),
        PosterElement(
            id="headline",
            type="text",
            z=3,
            x=64,
            y=464,
            w=952,
            h=240,
            text=headline,
            font="display",
            weight=700,
            size=64,
            line_height=1.15,
            align="center",
            color="#F8FAFC"
        ),
        PosterElement(
            id="metric_card",
            type="shape",
            z=1,
            x=64,
            y=736,
            w=952,
            h=344,
            radius=24,
            fill="#0F2D23",
            stroke=primary_color,
            stroke_width=2,
            decorative=True
        ),
        PosterElement(
            id="subhead",
            type="text",
            z=3,
            x=104,
            y=784,
            w=872,
            h=144,
            text=subhead,
            font="text",
            weight=400,
            size=32,
            line_height=1.45,
            align="center",
            color="#D1FAE5"
        ),
        PosterElement(
            id="proof_tag",
            type="text",
            z=3,
            x=104,
            y=960,
            w=872,
            h=64,
            text=f"✦ AUDITED BY INDEPENDENT RESEARCH • {business_name.upper()}",
            font="text",
            weight=600,
            size=28,
            align="center",
            color="#6EE7B7"
        ),
        PosterElement(
            id="cta_bg",
            type="shape",
            z=2,
            x=340,
            y=1144,
            w=400,
            h=88,
            radius=44,
            fill=primary_color
        ),
        PosterElement(
            id="cta_text",
            type="text",
            z=3,
            x=340,
            y=1144,
            w=400,
            h=88,
            text=f"{cta} →",
            font="text",
            weight=700,
            size=32,
            line_height=2.7,
            align="center",
            color="#06221A"
        )
    ]

    return PosterSpec(
        canvas=canvas,
        background=BackgroundConfig(type="gradient", value=f"{bg_color} -> #02120C"),
        fonts=fonts,
        reading_order=["eyebrow", "stat_number", "stat_label", "headline", "metric_card", "subhead", "proof_tag", "cta_bg", "cta_text"],
        focal_element="stat_number",
        elements=elements
    )


ARCHETYPE_SPECS = {
    "hero-text": create_hero_text_spec,
    "split-image-text": create_split_image_text_spec,
    "centered-badge": create_centered_badge_spec,
    "offer-burst": create_offer_burst_spec,
    "quote-card": create_quote_card_spec,
    "product-cutout": create_product_cutout_spec,
    "grid-multi-item": create_grid_multi_item_spec,
    "event-ticket": create_event_ticket_spec,
    "stats-metric": create_stats_metric_spec,
    "minimal-editorial": create_minimal_editorial_spec,
}


def get_archetype_template(
    archetype: str,
    headline: str,
    subhead: Optional[str] = None,
    primary_color: str = "#6366F1",
    bg_color: Optional[str] = None,
    cta: str = "Learn More",
    business_name: str = "My Business"
) -> PosterSpec:
    """Generates a validated archetype spec tailored to the client's brief across all 10 archetypes and 30 templates."""
    arch = archetype.lower().strip()

    # 1. Product Cutout
    if arch in ("product-cutout", "product", "product_cutout", "product-floating-shadow", "product-neon-glow", "product-pedestal-stage"):
        variant = "floating_shadow"
        if "neon" in arch:
            variant = "neon_glow"
        elif "pedestal" in arch:
            variant = "pedestal_stage"
        return create_product_cutout_spec(
            headline=headline,
            eyebrow=f"✦ {business_name.upper()}",
            subhead=subhead or "Engineered with precision materials and tailored performance.",
            cta=cta or "Explore Now",
            product_name=headline.split()[0] if headline else "Featured",
            primary_color=primary_color or "#EF4444",
            bg_color=bg_color or "#0F172A",
            variant=variant
        )

    # 2. Grid Multi-Item
    elif arch in ("grid-multi-item", "grid", "lookbook", "grid-3-item-showcase", "grid-4-lookbook", "grid-2x2-comparison"):
        variant = "3_item_showcase"
        if "lookbook" in arch or "4" in arch:
            variant = "4_lookbook"
        elif "comparison" in arch or "before" in arch:
            variant = "2x2_comparison"
        return create_grid_multi_item_spec(
            headline=headline,
            eyebrow=f"✦ {business_name.upper()} SELECTIONS",
            subhead=subhead or "Specialized treatments and curated offerings tailored to your needs.",
            cta=cta or "Book Appointment",
            business_name=business_name,
            primary_color=primary_color or "#059669",
            bg_color=bg_color or "#062018",
            variant=variant
        )

    # 3. Stats & Metric
    elif arch in ("stats-metric", "stats", "metric", "stats-giant-number", "stats-progress-ring", "stats-comparative-bar"):
        variant = "giant_number"
        if "progress" in arch:
            variant = "progress_ring"
        elif "bar" in arch or "tier" in arch:
            variant = "comparative_bar"
        # Extract or construct stat number
        stat_num = "99.4%"
        words = headline.split()
        for w in words:
            if any(ch.isdigit() for ch in w) or "%" in w or "★" in w:
                stat_num = w
                break
        return create_stats_metric_spec(
            stat_number=stat_num,
            stat_label="VERIFIED SUCCESS METRIC",
            headline=headline,
            subhead=subhead or f"Proven track record delivered by {business_name}.",
            cta=cta or "Learn More",
            business_name=business_name,
            primary_color=primary_color or "#10B981",
            bg_color=bg_color or "#06221A",
            variant=variant
        )

    # 4. Split Image + Text
    elif arch in ("split-image-text", "split", "food", "dining", "split-50-50-vertical", "split-60-40-horizontal", "split-asymmetric-diagonal"):
        text_context = (headline + " " + business_name).lower()
        is_shoe = any(k in text_context for k in ("shoe", "sneaker", "footwear", "kicks", "runner", "boots"))
        is_coffee = not is_shoe and any(k in text_context for k in ("cold brew", "espresso", "latte", "roast", "cafe"))
        cat = "SINGLE-ORIGIN COLD BREW" if is_coffee else (f"✦ {business_name.upper()}" if business_name and business_name != "Your Brand" else "FEATURED COLLECTION")
        default_sub = f"A guided tasting at {business_name}." if is_coffee else f"Crafted with visionary precision at {business_name}."
        default_cta = "Reserve a seat" if is_coffee else ("Shop Collection" if is_shoe else "Learn More")
        return create_split_image_text_spec(
            headline=headline,
            category=cat,
            subhead=subhead or default_sub,
            cta=cta or default_cta,
            business_name=business_name,
            primary_color=primary_color or ("#E8890C" if is_coffee else "#6366F1"),
            bg_color=bg_color or ("#120A06" if is_coffee else "#0F172A")
        )

    # 5. Centered Badge
    elif arch in ("festival", "centered-badge", "festival_greeting", "badge", "badge-heritage-seal", "badge-neon-pill", "badge-festive-arch"):
        badge_title = "SPECIAL EDITION"
        h_lower = headline.lower()
        if "diwali" in h_lower or "deepavali" in h_lower:
            badge_title = "SHUBH DEEPAVALI"
        elif "holi" in h_lower:
            badge_title = "HAPPY HOLI"
        elif "eid" in h_lower:
            badge_title = "EID MUBARAK"
        elif "christmas" in h_lower:
            badge_title = "MERRY CHRISTMAS"
        elif "new year" in h_lower:
            badge_title = "HAPPY NEW YEAR"

        return create_centered_badge_spec(
            headline=headline,
            badge_title=badge_title,
            subhead=subhead or "Festive greetings from our team.",
            cta=cta or "Celebrate With Us",
            business_name=business_name,
            primary_color=primary_color,
            bg_color=bg_color or "#0B0712"
        )

    # 6. Offer Burst
    elif arch in ("offer", "offer-burst", "discount", "sale", "offer-explosive-tag", "offer-sticker-peel", "offer-geometric-flash"):
        return create_offer_burst_spec(
            headline=headline,
            subhead=subhead or "Limited-time opportunity for verified clients.",
            cta=cta or "Claim Deal",
            primary_color=primary_color,
            bg_color=bg_color or "#0A0A0A"
        )

    # 7. Quote Card
    elif arch in ("quote", "quote-card", "testimonial", "review", "quote-editorial-serif", "quote-chat-bubble", "quote-glass-card"):
        return create_quote_card_spec(
            quote=headline,
            attribution=subhead or business_name,
            primary_color=primary_color,
            bg_color=bg_color or "#06281E"
        )

    # 8. Event Ticket
    elif arch in ("event", "event-ticket", "ticket", "conference", "summit", "event-stub-punch", "event-vip-metallic", "event-boarding-pass"):
        return create_event_ticket_spec(
            headline=headline,
            venue=subhead or f"Hosted by {business_name}",
            cta=cta or "Register Now",
            primary_color=primary_color,
            bg_color=bg_color or "#050B18"
        )

    # 9. Minimal Editorial
    elif arch in ("minimal", "minimal-editorial", "editorial", "luxury", "editorial-high-fashion", "editorial-swiss-grid", "editorial-gallery-frame"):
        return create_minimal_editorial_spec(
            headline=headline,
            subhead=subhead or "Curated spaces and bespoke services.",
            cta=cta or "Explore",
            brand_signature=business_name.upper(),
            primary_color=primary_color,
            bg_color=bg_color or "#F5F5F4"
        )

    # 10. Hero Text (Default)
    else:
        return create_hero_text_spec(
            headline=headline,
            eyebrow=f"✦ {business_name.upper()}" if business_name else "FEATURED ANNOUNCEMENT",
            subhead=subhead or "Empowering modern business with intelligent content automation.",
            cta=cta or "Get Started",
            contact=f"{business_name.lower().replace(' ', '')}.com",
            primary_color=primary_color,
            bg_color=bg_color or "#0B0F19"
        )


