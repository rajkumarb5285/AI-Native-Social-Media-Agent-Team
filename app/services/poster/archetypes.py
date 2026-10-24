"""The 7 Layout Archetypes for Poster Design Agent.

Direct implementation of Section 4.5 (Layout archetypes) of the Poster Design pack:
1. hero-text (announcements, bold greetings)
2. split-image-text (food, products, services)
3. centered-badge (festivals, grand openings)
4. offer-burst (flash sales, discounts)
5. quote-card (testimonials, thought leadership)
6. event-ticket (workshops, dates, details)
7. minimal-editorial (premium boutique, 60%+ whitespace)
"""
from typing import Dict, Any, Optional
from .spec import PosterSpec, CanvasConfig, BackgroundConfig, FontsConfig, PosterElement, OverlayScrim, SelfCheck


def create_hero_text_spec(
    headline: str = "Empower Your Brand with Autonomous AI Agents",
    eyebrow: str = "NEXT-GENERATION MARKETING",
    subhead: str = "Continuous market research, creative campaigns, and automated publishing.",
    cta: str = "Start Free Trial",
    contact: str = "nexus.studio | @nexusstudio",
    primary_color: str = "#6366F1",
    bg_color: str = "#0B0F19"
) -> PosterSpec:
    """Archetype 1: hero-text. Zone map: eyebrow 6-10%, headline 14-44%, shape 46-72%, subhead 74-82%, CTA 86-93%."""
    return PosterSpec(
        canvas=CanvasConfig(width=1080, height=1350, scale=1.0, margin=64),
        background=BackgroundConfig(type="solid", value=bg_color),
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
                fill="#1E293B",
                stroke="#334155",
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
                h=140,
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
                y=1160,
                w=400,
                h=88,
                text=cta,
                font="text",
                weight=700,
                size=32,
                line_height=2.7,
                align="center",
                color="#FFFFFF"
            ),
            PosterElement(
                id="contact",
                type="text",
                z=3,
                x=504,
                y=1184,
                w=512,
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


def create_centered_badge_spec(
    headline: str = "Shubh Deepavali & Auspicious Blessings",
    eyebrow: str = "FESTIVAL OF LIGHTS",
    subhead: str = "May this Diwali bring prosperity, good fortune, and radiant light to your home.",
    cta: str = "Celebrate Together",
    business_name: str = "Royal Jewellers & Co.",
    primary_color: str = "#F59E0B",
    bg_color: str = "#180D05"
) -> PosterSpec:
    """Archetype 3: centered-badge. Best for festivals and grand openings."""
    return PosterSpec(
        canvas=CanvasConfig(width=1080, height=1350, scale=1.0, margin=64),
        background=BackgroundConfig(type="solid", value=bg_color),
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
                y=200,
                w=600,
                h=440,
                radius=40,
                fill="#2A170A",
                stroke=primary_color,
                stroke_width=3
            ),
            PosterElement(
                id="badge_inner_title",
                type="text",
                z=3,
                x=280,
                y=360,
                w=520,
                h=120,
                text="DIWALI MUBARAK",
                font="display",
                weight=800,
                size=57,
                align="center",
                color="#FEF3C7"
            ),
            PosterElement(
                id="headline",
                type="text",
                z=3,
                x=64,
                y=700,
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
                y=910,
                w=888,
                h=140,
                text=subhead,
                font="text",
                weight=400,
                size=32,
                line_height=1.4,
                align="center",
                color="#FDE68A"
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
    primary_color: str = "#E11D48",
    bg_color: str = "#0F172A"
) -> PosterSpec:
    """Archetype 4: offer-burst. Giant offer value in display-xl."""
    return PosterSpec(
        canvas=CanvasConfig(width=1080, height=1350, scale=1.0, margin=64),
        background=BackgroundConfig(type="solid", value=bg_color),
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
                text="FLASH SALE",
                font="text",
                weight=700,
                size=28,
                color="#FDA4AF",
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
                h=340,
                radius=32,
                fill=primary_color
            ),
            PosterElement(
                id="burst_text",
                type="text",
                z=3,
                x=64,
                y=230,
                w=952,
                h=200,
                text=offer_value,
                font="display",
                weight=900,
                size=135,
                align="center",
                color="#FFFFFF"
            ),
            PosterElement(
                id="headline",
                type="text",
                z=3,
                x=64,
                y=560,
                w=952,
                h=220,
                text=headline,
                font="display",
                weight=800,
                size=76,
                line_height=1.1,
                color="#F8FAFC"
            ),
            PosterElement(
                id="subhead",
                type="text",
                z=3,
                x=64,
                y=820,
                w=952,
                h=140,
                text=subhead,
                font="text",
                weight=400,
                size=36,
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
                text=cta,
                font="text",
                weight=700,
                size=32,
                line_height=2.7,
                align="center",
                color="#FFFFFF"
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
    bg_color: str = "#064E3B"
) -> PosterSpec:
    """Archetype 5: quote-card. Oversized quotes with verified attribution."""
    return PosterSpec(
        canvas=CanvasConfig(width=1080, height=1350, scale=1.0, margin=64),
        background=BackgroundConfig(type="solid", value=bg_color),
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
                text=eyebrow,
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
                h=144,
                text="“",
                font="display",
                weight=900,
                size=135,
                line_height=1.0,
                color=primary_color
            ),
            PosterElement(
                id="quote_text",
                type="text",
                z=3,
                x=64,
                y=320,
                w=952,
                h=540,
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
                h=4,
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
                h=90,
                text=attribution,
                font="text",
                weight=500,
                size=32,
                line_height=1.35,
                color="#D1FAE5"
            ),
        ]
    )


ARCHETYPE_SPECS = {
    "hero-text": create_hero_text_spec,
    "centered-badge": create_centered_badge_spec,
    "offer-burst": create_offer_burst_spec,
    "quote-card": create_quote_card_spec,
}


def get_archetype_template(
    archetype: str,
    headline: str,
    subhead: Optional[str] = None,
    primary_color: str = "#6366F1",
    cta: str = "Learn More",
    business_name: str = "My Business"
) -> PosterSpec:
    """Generates a validated archetype spec tailored to the client's brief."""
    arch = archetype.lower().strip()
    if arch in ("festival", "centered-badge", "festival_greeting"):
        return create_centered_badge_spec(
            headline=headline,
            subhead=subhead or "Festive greetings from our team.",
            cta=cta or "Celebrate With Us",
            business_name=business_name,
            primary_color=primary_color
        )
    elif arch in ("offer", "offer-burst", "discount", "sale"):
        return create_offer_burst_spec(
            headline=headline,
            subhead=subhead or "Limited-time opportunity for verified clients.",
            cta=cta or "Claim Deal",
            primary_color=primary_color
        )
    elif arch in ("quote", "quote-card", "testimonial"):
        return create_quote_card_spec(
            quote=headline,
            attribution=subhead or business_name,
            primary_color=primary_color
        )
    else:
        # Default to hero-text
        return create_hero_text_spec(
            headline=headline,
            subhead=subhead or "Empowering modern business with intelligent content automation.",
            cta=cta or "Get Started",
            primary_color=primary_color
        )
