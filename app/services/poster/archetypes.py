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
                w=420,
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
                w=420,
                h=88,
                text=f"{cta} →",
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
    headline: str = "Artisanal Single-Origin Coffee",
    category: str = "SPECIALTY ROASTERY",
    subhead: str = "Handcrafted pour-overs and small-batch cold brews roasted fresh daily.",
    cta: str = "Order For Pickup",
    business_name: str = "Artisan Cafe & Lab",
    primary_color: str = "#D97706",
    bg_color: str = "#140D07"
) -> PosterSpec:
    """Archetype 2: split-image-text. Half showcase card, half structured copy."""
    return PosterSpec(
        canvas=CanvasConfig(width=1080, height=1350, scale=1.0, margin=64),
        background=BackgroundConfig(type="gradient", value=f"{bg_color} -> #080503"),
        fonts=FontsConfig(display="Playfair Display", text="Inter"),
        reading_order=["category_tag", "showcase_card", "headline", "subhead", "cta_bg", "cta_text", "business_name"],
        focal_element="showcase_card",
        elements=[
            PosterElement(
                id="category_tag",
                type="text",
                z=3,
                x=64,
                y=80,
                w=952,
                h=40,
                text=f"✦ {category}",
                font="text",
                weight=700,
                size=28,
                color=primary_color,
                letter_spacing="0.08em"
            ),
            PosterElement(
                id="showcase_card",
                type="shape",
                z=1,
                x=64,
                y=144,
                w=952,
                h=540,
                radius=32,
                fill="#24170F",
                stroke=primary_color,
                stroke_width=2,
                decorative=True
            ),
            PosterElement(
                id="showcase_badge",
                type="badge",
                z=3,
                x=96,
                y=176,
                w=280,
                h=56,
                radius=28,
                fill=primary_color,
                text="★ VERIFIED RESERVE",
                font="text",
                size=28,
                weight=700,
                color="#FFFFFF"
            ),

            PosterElement(
                id="headline",
                type="text",
                z=3,
                x=64,
                y=728,
                w=952,
                h=200,
                text=headline,
                font="display",
                weight=800,
                size=68,
                line_height=1.15,
                color="#FFF8F0"
            ),
            PosterElement(
                id="subhead",
                type="text",
                z=3,
                x=64,
                y=944,
                w=952,
                h=140,
                text=subhead,
                font="text",
                weight=400,
                size=34,
                line_height=1.4,
                color="#D1C7BD"
            ),
            PosterElement(
                id="cta_bg",
                type="shape",
                z=2,
                x=64,
                y=1160,
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
                y=1160,
                w=440,
                h=88,
                text=f"{cta} →",
                font="text",
                weight=700,
                size=32,
                line_height=2.7,
                align="center",
                color="#FFFFFF"
            ),
            PosterElement(
                id="business_name",
                type="text",
                z=3,
                x=540,
                y=1184,
                w=476,
                h=48,
                text=business_name,
                font="text",
                weight=600,
                size=28,
                align="right",
                color="#A89F91"
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
                text=f"{cta} →",
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
                h=140,
                radius=24,
                fill=primary_color
            ),
            PosterElement(
                id="date_text",
                type="text",
                z=3,
                x=64,
                y=196,
                w=440,
                h=80,
                text=date_badge,
                font="display",
                weight=900,
                size=48,
                align="center",
                color="#FFFFFF"
            ),
            PosterElement(
                id="headline",
                type="text",
                z=3,
                x=64,
                y=360,
                w=952,
                h=340,
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
                y=740,
                w=952,
                h=120,
                text=f"📍 {venue}",
                font="text",
                weight=500,
                size=36,
                line_height=1.4,
                color="#93C5FD"
            ),
            PosterElement(
                id="ticket_divider",
                type="line",
                z=2,
                x=64,
                y=940,
                w=952,
                h=4,
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
                color="#FFFFFF"
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
                color=primary_color,
                letter_spacing="0.12em"
            ),
            PosterElement(
                id="headline",
                type="text",
                z=3,
                x=64,
                y=380,
                w=952,
                h=380,
                text=headline,
                font="display",
                weight=500,
                size=84,
                line_height=1.15,
                color="#1C1917"
            ),
            PosterElement(
                id="editorial_line",
                type="line",
                z=2,
                x=64,
                y=820,
                w=160,
                h=2,
                stroke=primary_color,
                stroke_width=2
            ),
            PosterElement(
                id="subhead",
                type="text",
                z=3,
                x=64,
                y=860,
                w=760,
                h=140,
                text=subhead,
                font="text",
                weight=400,
                size=34,
                line_height=1.5,
                color="#44403C"
            ),
            PosterElement(
                id="cta_text",
                type="text",
                z=3,
                x=64,
                y=1160,
                w=440,
                h=60,
                text=f"{cta} —",
                font="text",
                weight=600,
                size=30,
                color="#1C1917"
            ),
        ]
    )


ARCHETYPE_SPECS = {
    "hero-text": create_hero_text_spec,
    "split-image-text": create_split_image_text_spec,
    "centered-badge": create_centered_badge_spec,
    "offer-burst": create_offer_burst_spec,
    "quote-card": create_quote_card_spec,
    "event-ticket": create_event_ticket_spec,
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
    """Generates a validated archetype spec tailored to the client's brief."""
    arch = archetype.lower().strip()

    if arch in ("split-image-text", "split", "food", "dining", "product"):
        return create_split_image_text_spec(
            headline=headline,
            category=business_name.upper(),
            subhead=subhead or "Handcrafted with the finest ingredients and verified perfection.",
            cta=cta or "Order Now",
            business_name=business_name,
            primary_color=primary_color,
            bg_color=bg_color or "#140D07"
        )
    elif arch in ("festival", "centered-badge", "festival_greeting", "badge"):
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
    elif arch in ("offer", "offer-burst", "discount", "sale"):
        return create_offer_burst_spec(
            headline=headline,
            subhead=subhead or "Limited-time opportunity for verified clients.",
            cta=cta or "Claim Deal",
            primary_color=primary_color,
            bg_color=bg_color or "#0A0A0A"
        )
    elif arch in ("quote", "quote-card", "testimonial", "review"):
        return create_quote_card_spec(
            quote=headline,
            attribution=subhead or business_name,
            primary_color=primary_color,
            bg_color=bg_color or "#06281E"
        )
    elif arch in ("event", "event-ticket", "ticket", "conference", "summit"):
        return create_event_ticket_spec(
            headline=headline,
            venue=subhead or f"Hosted by {business_name}",
            cta=cta or "Register Now",
            primary_color=primary_color,
            bg_color=bg_color or "#050B18"
        )
    elif arch in ("minimal", "minimal-editorial", "editorial", "luxury"):
        return create_minimal_editorial_spec(
            headline=headline,
            subhead=subhead or "Curated spaces and bespoke services.",
            cta=cta or "Explore",
            brand_signature=business_name.upper(),
            primary_color=primary_color
        )
    else:
        # Default to hero-text
        return create_hero_text_spec(
            headline=headline,
            subhead=subhead or "Empowering modern business with intelligent content automation.",
            cta=cta or "Get Started",
            contact=f"{business_name.lower().replace(' ', '')}.com",
            primary_color=primary_color,
            bg_color=bg_color or "#0B0F19"
        )
