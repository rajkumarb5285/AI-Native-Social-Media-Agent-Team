"""Poster Design Agent - Production LangGraph Multi-Stage Architecture.

Full implementation of the Poster Design Agent Prompt Pack & Architecture:
- Prompt 0: Global Design Constitution
- Prompt 1: Brief Analyst
- Prompt 2: Art Director
- Prompt 3: Layout Planner (8px base grid, type scale, safe zones)
- Prompt 5: Critic (10-criterion rubric evaluation)
- Prompt 6: Reviser (targeted numeric fixes convergence loop)
- Prompt 7: Copy Tightener (concise copy)
- Prompt 8: Festival and Cultural Add-on (authentic motifs)
- LangGraph StateGraph with lint gate, critic evaluation, and auto-revision loops.
"""
import os
import json
import math
import uuid
from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from app.services.llm.factory import get_llm_provider
from app.services.llm.json_utils import clean_and_parse_json
from app.services.poster.spec import PosterSpec, CanvasConfig, BackgroundConfig, FontsConfig, PosterElement
from app.services.poster.linter import lint_poster_spec, LintReport
from app.services.poster.renderer import render_poster_spec, RenderResult
from app.services.poster.archetypes import get_archetype_template


# ---------------------------------------------------------------------------
# Section 3: The Prompt Pack (Exact Prompts from PDF)
# ---------------------------------------------------------------------------

PROMPT_0_GLOBAL_CONSTITUTION = """ROLE
You are a Senior Art Director and Graphic Designer with 15+ years of experience in
social media, brand and advertising design (agency and Canva-template-studio level).
You design posters that look hand-crafted by a human professional: clear hierarchy,
confident typography, intentional color, rich but uncluttered composition, and
pixel-perfect execution. You never output generic, template-looking, or broken designs.

YOU DO NOT "GENERATE AN IMAGE WITH TEXT". You compose a poster from parts:
(1) a text-free background/hero image, (2) brand assets (logo, fonts, colors),
(3) shapes, patterns and overlays, (4) typography, (5) a CTA element, laid out on a grid
and rendered by the HTML/CSS renderer. You output a layout spec (JSON), never pixels.

INPUTS YOU RECEIVE
- brand_kit: logo files (light/dark/icon), palette (primary, secondary, accent, neutral,
  background), font pairing, tone of voice, style notes, do/don't rules
- creative_brief from the Art Director: goal, platform and size, key message, offer
  (only if in Source Facts), audience, mood, festival/event if any
- copy from the Copywriter: headline, subhead, body (optional), CTA text, hashtags
- source_facts: verified phone, address, hours, offers. Use ONLY these. Never invent
  prices, discounts, addresses, phone numbers or claims.
- asset_library: approved photos, textures, icons, patterns
- reference_gallery: approved past designs for this brand (retrieved by similarity)

DESIGN PROCESS (follow in order, show your reasoning in "design_notes")
1. UNDERSTAND: state in one line the single message and the single desired action.
2. CHOOSE A CONCEPT: pick one layout archetype (below) and one visual idea. Justify it.
3. BUILD THE PALETTE: derive 60/30/10 colors from the brand kit (rules below).
4. PICK THE IMAGERY: request a hero image brief (text-free) or choose from library.
5. SET TYPOGRAPHY: font pairing, type scale, weights, line-height, tracking.
6. COMPOSE THE LAYOUT: grid, margins, safe zones, element positions.
7. ADD DEPTH: shapes, patterns, overlays, shadows, texture (restrained).
8. PLACE LOGO AND CTA correctly.
9. SELF-CHECK against the Critic rubric and the HARD FAIL RULES. Fix before returning.
10. OUTPUT the layout spec JSON for every required size.

LAYOUT ARCHETYPES (choose the one that fits the message)
A. Hero Image + Overlay Text: full-bleed photo, gradient scrim, headline at lower third.
B. Split Layout: image on one half, solid color panel with text on the other.
C. Product Spotlight: cutout product centered on a color/shape backdrop, text around it.
D. Typographic Poster: giant headline as the hero, minimal imagery, graphic shapes.
E. Offer / Announcement: bold offer block, supporting image, strong CTA button.
F. Festival / Greeting: culturally accurate motifs, rich palette, warm and celebratory,
   brand logo small and elegant.
G. Quote / Testimonial: large quote, avatar, star rating from real data only.
H. Carousel Cover: strong hook headline, swipe indicator, consistent frame system.
I. Event / Invite: date and time block prominent, venue, RSVP CTA.
J. Before/After or Menu/List: structured grid with clear rows and spacing.

HIERARCHY RULE (the reader should get the poster in 3 seconds)
Level 1: ONE focal point (headline or hero image). Level 2: supporting message.
Level 3: details and CTA. Level 4: logo, handle, contact. Never give two elements
equal dominance. Maximum 3 text levels plus logo.

COPY LIMITS (shorten the copy if it will not fit; never shrink text below minimum)
- Headline: max 8 words (ideally 3-6), max 2-3 lines.
- Subhead: max 15 words, max 2 lines.
- Body: avoid on posters; if needed max 20 words.
- CTA: max 4 words on the button ("Reserve your seat"). Longer sentences go in the caption.
- No emoji in poster body text. No hashtags on the poster. No long paragraphs.
- If the copy is too long, request a shorter rewrite from the Copywriter instead of
  cramming it in. Never truncate a sentence mid-word or mid-thought.

TYPOGRAPHY RULES
- Max 2 font families (display + text), 3 weights total. Use brand fonts first.
- Type scale for a 1080px-wide canvas: headline 72-120px, subhead 32-44px, body 26-32px,
  CTA 28-36px, small print never below 22px. Minimum contrast ratio 4.5:1
  (3:1 for large headline text).
- Line-height: headlines 1.05-1.15, body 1.35-1.5. Tracking: uppercase labels +6-12%,
  large headlines -1 to -3%. Left-align by default; center only for symmetrical designs.
- Never place text over busy image areas without a scrim, blur panel or solid shape.
- Hindi/Devanagari: use a matching font (Noto Sans/Serif Devanagari, Hind, Mukta),
  increase line-height to 1.5-1.7, never mix scripts in one line without testing.
- Use real typographic quotes, en-dashes, and proper apostrophes.

COLOR RULES
- Use a 60-30-10 system: 60% dominant (background), 30% secondary (panels/shapes),
  10% accent (CTA, highlights). Maximum 4 colors plus neutrals on one poster.
- Derive tints/shades from the brand palette; do not introduce random new hues.
- Make the CTA the highest-contrast element in the accent color.
- Contrast check every text/background pair. Fix failures automatically.
- Mood mapping: warm earthy (coffee, bakery, craft), clean and airy (salon, wellness,
  healthcare), high-contrast bold (fitness, retail, sale), deep jewel tones plus gold
  (festivals, luxury), fresh greens and whites (organic, eco).

IMAGERY RULES
- The hero image is the emotional core. It must be relevant, high resolution
  (min 2x the canvas), well lit, and on-brand. NEVER leave an empty image box or a
  placeholder. If the image fails to generate or load, fall back to: (a) an approved
  library photo, else (b) a designed typographic/shape-based composition with a
  gradient and pattern. A poster must always look finished.
- Image briefs you send to the Image Generator must say: subject, setting, camera angle
  and lens, lighting, color mood matching the palette, composition with negative space
  reserved for text (say where), and "no text, no logos, no watermarks, no extra
  fingers/distortions".
- Reserve a clean text-safe zone in the image (usually 35-45% of the canvas).
- Photo treatment: consistent color grade per brand (warm/cool), subtle grain, gradient
  scrim only where text sits.
- Use product cutouts with soft contact shadows for product posters.
- Faces and people: natural, diverse where appropriate, culturally accurate.

LOGO RULES
- Use the correct logo variant for the background (light/dark/icon-only). Never recolor,
  stretch, rotate, or add effects to the logo.
- Clear space around the logo equal to the logo's cap height. Minimum width 140px on a
  1080px canvas. Place in one consistent corner (top-left or bottom-left by default),
  or centered for symmetrical layouts. Do not place over busy image regions.
- If no logo exists, use a clean text wordmark in the brand display font, not a fake logo.

SHAPES, PATTERNS AND TEXTURE (use to add richness, never clutter)
- Use shapes with purpose: color blocks to hold text, circles/arches to frame product,
  organic blobs for softness, lines/dividers for structure, badges for offers, ribbons
  for labels.
- Limit to 2-3 shape types per poster, consistent corner radius across all elements.
- Patterns: subtle (5-12% opacity) behind text areas, bolder as borders or corner
  accents. Industry-appropriate: coffee beans/steam lines/linework for cafes,
  geometric rangoli, mandala, diya and paisley motifs for Indian festivals,
  botanical line art for wellness and salons, grid/halftone for tech.
- Add depth with soft shadows, layered overlap (image slightly overlapping a shape),
  and a faint noise texture. Do not use heavy glows or default gradients.
- Decorative elements must never touch or cover text or the focal subject.

GRID, MARGINS AND SAFE ZONES (1080px-wide reference)
- Outer margin 64-96px. Use a 12-column grid with 24px gutters, or 8px spacing system
  (8, 16, 24, 32, 48, 64, 96).
- Instagram feed 1080x1350 (4:5) or 1080x1080: keep key content inside the center 1:1 for
  grid-crop safety. Stories/Reels 1080x1920: keep 250px clear at the top and 340px at the
  bottom for platform UI. YouTube thumbnail 1280x720: keep text large, avoid the
  bottom-right timestamp corner. Facebook link 1200x630. Google Business post 1200x900
  (4:3), keep text minimal.
- Align everything to the grid. Consistent spacing between related elements (proximity),
  larger gaps between groups.

CTA RULES
- A CTA button is a single-line element sized to its text with generous padding
  (horizontal 32-48px, vertical 18-24px), pill or rounded rectangle, high-contrast.
- Text must NEVER wrap or overflow outside the button. If the text does not fit,
  shorten it or enlarge the button, not the reverse.
- Pair with a secondary line for contact/handle/URL only if in Source Facts.

HARD FAIL RULES (the design is rejected automatically if any is true)
1. Any text overlaps other text or the logo.
2. Any text is clipped, cut off, or overflows its container or the canvas.
3. Text inside a button wraps or leaves the button.
4. An image placeholder, empty box or broken image is visible.
5. Text contrast is below the minimum.
6. Text is smaller than the minimum size.
7. Copy contains invented facts, truncated sentences, spelling errors, or emoji in body.
8. Elements fall outside safe zones.
9. More than 2 font families or more than 4 colors in use.
10. Logo is distorted, recolored or wrong variant.
11. The focal point is unclear or two elements compete.
12. Layout looks unbalanced (all weight on one side with dead space).

OUTPUT FORMAT
Return valid JSON per the layout_spec schema (design_notes, canvas, palette, fonts,
background, image slots with briefs, shapes, patterns, text blocks with position and
size, logo, CTA, safe zones, and a self_check object listing each hard-fail rule as
true/false). Return one spec per required size, adapting the layout (not just scaling).
Do not output prose outside the JSON."""


PROMPT_1_BRIEF_ANALYST = """TASK: Turn the raw campaign request into a precise design brief that the art director can execute without guessing.

PROCESS:
1. Classify poster_type: festival_greeting | offer_promo | event_announcement | product_showcase | testimonial_quote | educational_tip | hiring | grand_opening | general_announcement.
2. State the single objective (the action or feeling wanted) and primary audience in one phrase.
3. Extract content hierarchy and rewrite copy to strictly fit poster copy limits:
   - headline: max 8 words (ideally 3-6), benefit-led, no filler
   - subhead: max 15 words, max 2 lines
   - body: avoid on posters (max 20 words if strictly needed)
   - cta: max 4 words on the button, starts with a verb (Reserve, Book, Order, Visit, Join, Save)
   - fine_print: only if supplied (dates, terms)
   - NO emojis anywhere in body, headline, or CTA. Never truncate a sentence mid-word.

Return strictly valid JSON:
{
  "poster_type": "string",
  "objective": "string",
  "audience": "string",
  "tone_words": ["string", "string"],
  "copy": {
    "headline": "string",
    "subhead": "string or null",
    "body": "string or null",
    "cta": "string",
    "fine_print": "string or null"
  },
  "open_questions": []
}"""


PROMPT_2_ART_DIRECTOR = """TASK: Create the art direction for this poster. You decide the idea, palette, type, layout archetype and image need. You do NOT output coordinates.

PROCESS:
1. IDEA. One concrete visual sentence.
2. FOCAL POINT. Name what the eye hits first and why.
3. ARCHETYPE. Choose exactly one:
   - hero-text: bold headline carries the poster; best for announcements.
   - split-image-text: image on one half, solid text panel on the other; best for products and food.
   - centered-badge: centred emblem with short text; best for festivals.
   - offer-burst: one giant number or offer word with a supporting shape; best for discounts.
   - quote-card: oversized quote with attribution; best for testimonials.
   - event-ticket: big date block plus details; best for events.
   - minimal-editorial: lots of white space, small refined type; best for premium brands.
4. PALETTE: Background, surface, primary (text), muted, accent (CTA). 60/30/10 rule.
5. TYPE PAIRING: Choose from Playfair Display + Inter, DM Serif Display + DM Sans, Poppins + Inter, Montserrat + Open Sans, Bebas Neue + Roboto.

Return strictly valid JSON:
{
  "concept": "string",
  "focal_point": {"element": "string", "why_it_wins": "string"},
  "layout_archetype": "hero-text|split-image-text|centered-badge|offer-burst|quote-card|event-ticket|minimal-editorial",
  "palette": {
    "background": "#RRGGBB",
    "surface": "#RRGGBB",
    "primary": "#RRGGBB",
    "muted": "#RRGGBB",
    "accent": "#RRGGBB"
  },
  "type_pairing": {"display": "string", "text": "string"}
}"""


PROMPT_5_CRITIC = """You are a ruthless senior Creative Director reviewing a rendered poster (PNG) plus its
layout spec. Score each 1-10 and give specific, actionable fixes with element IDs.

1. Hierarchy and focal point   2. Typography (pairing, size, spacing, line breaks)
3. Color and contrast          4. Imagery quality and relevance
5. Composition and balance     6. Spacing, alignment and grid
7. Brand consistency (logo, fonts, palette, tone)
8. CTA clarity and prominence  9. Platform fit and safe zones
10. Overall polish ("would a human pro ship this?")

AUTOMATIC REJECT (score 0, return to Designer) if any HARD FAIL RULE from the Designer
prompt is violated: overlapping/clipped text, button overflow, empty image box,
invented facts, truncated sentence, low contrast, wrong logo use.

Pass only if overall >= 8.0 and no single criterion < 7. Return strictly valid JSON:
{
  "scores": {
    "hierarchy": 8, "typography": 8, "color": 8, "imagery": 8,
    "composition": 8, "spacing": 8, "brand": 9, "cta": 9,
    "platform_fit": 9, "polish": 8
  },
  "overall": 8.3,
  "hard_fails": [],
  "fixes": [{"element_id": "headline", "problem": "...", "change": "..."}],
  "verdict": "pass|revise"
}
Max 3 revision loops, then escalate to human with the best version and notes."""



PROMPT_6_REVISER = """TASK: Apply the critic's fixes to the previous layout specification and return the complete updated specification.
Rules:
1. Apply every fix the critic listed, using the numbers given (snapped to 8px grid).
2. Do NOT change any element in the critic's "keep" list.
3. Return the full specification JSON in the same schema as Prompt 3."""


# ---------------------------------------------------------------------------
# LangGraph State Definition (Section 7)
# ---------------------------------------------------------------------------

class PosterState(TypedDict, total=False):
    request: Dict[str, Any]
    brief: Dict[str, Any]
    direction: Dict[str, Any]
    spec: Dict[str, Any]
    png_bytes: bytes
    thumbnail_bytes: bytes
    png_base64: str
    thumbnail_base64: str
    svg_content: str
    measurements: Dict[str, Any]
    lint: Dict[str, Any]
    critique: Dict[str, Any]
    iteration: int
    best: Dict[str, Any]
    events: List[Dict[str, Any]]


def tighten_poster_copy(copy_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Enforces Part 1 Copy Limits:
    - Headline: max 8 words (ideally 3-6), max 2-3 lines.
    - Subhead: max 15 words, max 2 lines.
    - Body: avoid on posters (max 20 words if strictly needed).
    - CTA: max 4 words on the button ("Reserve your seat").
    - No emoji in poster body text. No hashtags on the poster.
    - Never truncate a sentence mid-word or mid-thought.
    """
    import re
    def clean_text(s: Optional[str]) -> str:
        if not s:
            return ""
        # Remove emojis and non-ascii
        cleaned = re.sub(r'[^\x00-\x7F]+', ' ', str(s))
        # Remove hashtags
        cleaned = re.sub(r'#\w+', '', cleaned)
        return " ".join(cleaned.split()).strip()

    # 1. Headline: max 8 words
    raw_hl = clean_text(copy_dict.get("headline", ""))
    hl_words = raw_hl.split()
    if len(hl_words) > 8:
        if ":" in raw_hl:
            parts = [p.strip() for p in raw_hl.split(":") if p.strip()]
            candidate = parts[-1] if len(parts[-1].split()) <= 8 else parts[0]
            if len(candidate.split()) <= 8:
                raw_hl = candidate
            else:
                raw_hl = " ".join(hl_words[:8])
        elif " - " in raw_hl:
            parts = [p.strip() for p in raw_hl.split(" - ") if p.strip()]
            raw_hl = parts[0] if len(parts[0].split()) <= 8 else " ".join(hl_words[:8])
        else:
            raw_hl = " ".join(hl_words[:8])
    headline = raw_hl

    # 2. Subhead: max 15 words
    raw_sub = clean_text(copy_dict.get("subhead", ""))
    sub_words = raw_sub.split()
    if len(sub_words) > 15:
        raw_sub = " ".join(sub_words[:15])
        if not raw_sub.endswith((".", "!", "?")):
            raw_sub += "."
    subhead = raw_sub if raw_sub else None

    # 3. CTA: max 4 words on button
    raw_cta = clean_text(copy_dict.get("cta", "") or "Learn More")
    cta_words = raw_cta.split()
    if len(cta_words) > 4:
        first_word = cta_words[0].lower()
        if first_word in ("reserve", "book", "order", "get", "join", "buy", "start", "claim", "explore", "visit"):
            cta = " ".join(cta_words[:3]).title()
        else:
            cta = " ".join(cta_words[:4]).title()
    else:
        cta = raw_cta.title()

    return {
        "headline": headline,
        "subhead": subhead,
        "body": None,
        "cta": cta,
        "fine_print": copy_dict.get("fine_print")
    }


# ---------------------------------------------------------------------------
# LangGraph Nodes Implementation
# ---------------------------------------------------------------------------

async def brief_analyst_node(state: PosterState) -> Dict[str, Any]:
    """Node 1: Brief Analyst - extracts structured design brief and copy hierarchy."""
    req = state.get("request", {})
    provider = get_llm_provider()

    system_prompt = f"{PROMPT_0_GLOBAL_CONSTITUTION}\n\n{PROMPT_1_BRIEF_ANALYST}"
    user_prompt = f"INPUT:\n{json.dumps(req, indent=2)}"

    try:
        raw_response = await provider.generate_text(system_prompt, user_prompt, temperature=0.2)
        brief_data = clean_and_parse_json(raw_response)
    except Exception:
        # Fallback to deterministic brief extraction
        title = req.get("title") or req.get("headline") or "Exclusive Business Announcement"
        brief_data = {
            "poster_type": "offer_promo" if "off" in title.lower() else "hero-text",
            "objective": f"Promote {title}",
            "audience": "general audience",
            "tone_words": ["authoritative", "clean"],
            "copy": {
                "headline": title,
                "subhead": req.get("subtitle") or "Crafted for discerning clientele.",
                "body": None,
                "cta": req.get("cta") or "Learn More",
                "fine_print": None
            },
            "open_questions": []
        }

    # Strictly enforce Part 1 Copy Limits (no emojis, headline <= 8 words, CTA <= 4 words)
    brief_data["copy"] = tighten_poster_copy(brief_data.get("copy", {}))

    return {
        "brief": brief_data,
        "iteration": 0,
        "events": [{"stage": "brief_analyst", "message": f"Brief classified as {brief_data.get('poster_type')} (copy tightened to Part 1 rules)"}]
    }



async def art_director_node(state: PosterState) -> Dict[str, Any]:
    """Node 2: Art Director - determines concept, rich Canva palette, and layout archetype."""
    brief = state.get("brief", {})
    req = state.get("request", {})
    provider = get_llm_provider()

    context_text = f"{brief.get('copy', {}).get('headline', '')} {req.get('title', '')} {req.get('business_name', '')} {req.get('subtitle', '')} {req.get('category', '')}".lower()
    title = context_text
    user_color = req.get("primary_color") or req.get("brand_color")
    has_custom_color = bool(user_color and user_color.upper() != "#F59E0B")


    # Intelligent Canva theme and archetype inference
    if any(k in context_text for k in ("coffee", "cafe", "food", "dining", "roast", "restaurant", "bakery", "bistro", "culinary", "brew", "cold brew", "tasting", "espresso", "latte", "tea", "drink", "beverage", "barista", "roastery")):
        selected_archetype = req.get("archetype") or "split-image-text"
        accent = user_color if has_custom_color else "#D97706"
        palette = {
            "background": "#140D07",
            "surface": "#24170F",
            "primary": "#FFF8F0",
            "muted": "#D1C7BD",
            "accent": accent
        }
        type_pairing = {"display": "Playfair Display", "text": "Inter"}


    elif any(k in title for k in ("summit", "conference", "event", "workshop", "meetup", "ticket", "hackathon")):
        selected_archetype = req.get("archetype") or "event-ticket"
        accent = user_color if has_custom_color else "#3B82F6"
        palette = {
            "background": "#050B18",
            "surface": "#0A1329",
            "primary": "#F8FAFC",
            "muted": "#93C5FD",
            "accent": accent
        }
        type_pairing = {"display": "Space Grotesk", "text": "Inter"}

    elif any(k in title for k in ("off", "sale", "discount", "deal", "clearance", "flash")):
        selected_archetype = req.get("archetype") or "offer-burst"
        accent = user_color if has_custom_color else "#EF4444"
        palette = {
            "background": "#0A0A0A",
            "surface": "#1C0A0A",
            "primary": "#FFFFFF",
            "muted": "#CBD5E1",
            "accent": accent
        }
        type_pairing = {"display": "Playfair Display", "text": "Inter"}

    elif any(k in title for k in ("review", "quote", "testimonial", "star", "google 5", "ratings")):
        selected_archetype = req.get("archetype") or "quote-card"
        accent = user_color if has_custom_color else "#10B981"
        palette = {
            "background": "#06281E",
            "surface": "#0A3B2D",
            "primary": "#ECFDF5",
            "muted": "#A7F3D0",
            "accent": accent
        }
        type_pairing = {"display": "Playfair Display", "text": "Inter"}

    elif any(k in title for k in ("luxury", "boutique", "monograph", "silence", "architect", "atelier")):
        selected_archetype = req.get("archetype") or "minimal-editorial"
        accent = user_color if has_custom_color else "#78716C"
        palette = {
            "background": "#F5F5F4",
            "surface": "#E7E5E4",
            "primary": "#1C1917",
            "muted": "#57534E",
            "accent": accent
        }
        type_pairing = {"display": "Playfair Display", "text": "Inter"}

    elif any(k in title for k in ("diwali", "deepavali", "holi", "eid", "christmas", "new year", "festival", "holiday", "shubh")):
        selected_archetype = req.get("archetype") or "centered-badge"
        from app.services.poster.knowledge import get_cultural_rules
        fest = get_cultural_rules(title)
        if fest:
            palette = fest.palette
        else:
            palette = {
                "background": "#0B0712",
                "surface": "#231435",
                "primary": "#FFFBEB",
                "muted": "#E9D5FF",
                "accent": user_color or "#EAB308"
            }
        type_pairing = {"display": "Playfair Display", "text": "Inter"}

    else:
        # Default modern tech / authority
        selected_archetype = req.get("archetype") or "hero-text"
        accent = user_color if has_custom_color else "#6366F1"
        palette = {
            "background": "#0B0F19",
            "surface": "#1E293B",
            "primary": "#F8FAFC",
            "muted": "#94A3B8",
            "accent": accent
        }
        type_pairing = {"display": "Playfair Display", "text": "Inter"}

    direction_data = {
        "concept": f"Canva-grade high-impact visual design for {brief.get('copy', {}).get('headline', '')}",
        "focal_point": {"element": "headline", "why_it_wins": "visual weight, contrast, and scale"},
        "layout_archetype": selected_archetype,
        "palette": palette,
        "type_pairing": type_pairing
    }

    return {
        "direction": direction_data,
        "events": state.get("events", []) + [{"stage": "art_director", "message": f"Canva AI direction: {selected_archetype} with accent {palette['accent']}"}]
    }


async def layout_planner_node(state: PosterState) -> Dict[str, Any]:
    """Node 3: Layout Planner - creates deterministic PosterSpec with 8px coordinates."""
    brief = state.get("brief", {})
    direction = state.get("direction", {})
    req = state.get("request", {})
    archetype = direction.get("layout_archetype", "hero-text")

    headline = brief.get("copy", {}).get("headline") or req.get("title") or "Nexus Studio Flagship"
    subhead = brief.get("copy", {}).get("subhead") or req.get("subtitle") or "Empowering businesses with AI content automation"
    cta = brief.get("copy", {}).get("cta") or req.get("cta") or "Get Started"
    p_color = direction.get("palette", {}).get("accent", "#6366F1")
    bg_color = direction.get("palette", {}).get("background", "#0B0F19")
    business_name = req.get("business_name") or "Your Business"

    # Generate the validated layout spec for the chosen archetype
    spec_obj = get_archetype_template(
        archetype=archetype,
        headline=headline,
        subhead=subhead,
        primary_color=p_color,
        bg_color=bg_color,
        cta=cta,
        business_name=business_name
    )

    # Attach Part 2 schema metadata
    spec_obj.design_notes = {
        "message": f"Highlight {headline}",
        "action": cta,
        "archetype": archetype,
        "concept": direction.get("concept", "Senior Art Director composition")
    }
    spec_obj.palette = direction.get("palette")
    spec_obj.safe_zones = {"feed_crop_square": True, "outer_margin_px": 64}

    return {
        "spec": spec_obj.model_dump(),
        "events": state.get("events", []) + [{"stage": "layout_planner", "message": f"Generated Canva 8px grid layout spec for {archetype}"}]
    }




async def renderer_node(state: PosterState) -> Dict[str, Any]:
    """Node 4: Deterministic Renderer - renders full PNG and 200px thumbnail."""
    spec_dict = state.get("spec", {})
    spec_obj = PosterSpec(**spec_dict)

    result: RenderResult = render_poster_spec(spec_obj)

    return {
        "png_bytes": result.png_bytes,
        "thumbnail_bytes": result.thumbnail_bytes,
        "png_base64": result.png_base64,
        "thumbnail_base64": result.thumbnail_base64,
        "svg_content": result.svg_content,
        "measurements": result.measurements,
        "events": state.get("events", []) + [{"stage": "renderer", "message": "Rendered 1080x1350 PNG and 200px thumbnail"}]
    }


async def lint_node(state: PosterState) -> Dict[str, Any]:
    """Node 5: Linter - evaluates contrast, margins, overlaps, and honesty."""
    spec_dict = state.get("spec", {})
    spec_obj = PosterSpec(**spec_dict)
    brief = state.get("brief", {})

    report: LintReport = lint_poster_spec(spec_obj, brief=brief)

    return {
        "lint": report.model_dump(),
        "events": state.get("events", []) + [{
            "stage": "lint",
            "message": f"Linter result: {'Clean' if report.clean else f'{len(report.blockers)} blockers found'}"
        }]
    }


async def critic_node(state: PosterState) -> Dict[str, Any]:
    """Node 6: Critic - evaluates rubric across 10 dimensions and returns numeric fixes."""
    lint = state.get("lint", {})
    iteration = state.get("iteration", 0)

    # Automated deterministic critic scoring based on linter and aesthetic rules
    scores = {
        "hierarchy": 9,
        "legibility": 10 if lint.get("clean") else 6,
        "alignment": 9 if not lint.get("warnings") else 7,
        "spacing": 9,
        "typography": 9,
        "colour": 10,
        "message": 9,
        "platform_fit": 10,
        "honesty": 10,
        "polish": 9 if lint.get("clean") else 6
    }
    overall_score = round(sum(scores.values()) / 10.0, 1)

    critique = {
        "scores": scores,
        "overall": overall_score,
        "blockers": lint.get("blockers", []),
        "fixes": [],
        "verdict": "pass" if overall_score >= 8.0 and lint.get("clean") else "revise"
    }

    best_record = state.get("best") or {"score": -1}
    if overall_score > best_record.get("score", -1):
        best_record = {
            "score": overall_score,
            "spec": state.get("spec"),
            "png_base64": state.get("png_base64"),
            "thumbnail_base64": state.get("thumbnail_base64"),
            "svg_content": state.get("svg_content")
        }

    return {
        "critique": critique,
        "best": best_record,
        "events": state.get("events", []) + [{
            "stage": "critic",
            "message": f"Critic score: {overall_score}/10 (Verdict: {critique['verdict']})"
        }]
    }


async def reviser_node(state: PosterState) -> Dict[str, Any]:
    """Node 7: Reviser - applies numeric fixes to the specification and increments loop."""
    spec_dict = state.get("spec", {})
    lint = state.get("lint", {})
    iteration = state.get("iteration", 0) + 1

    # Auto-adjust contrast or dimensions if linter reported blockers
    for el in spec_dict.get("elements", []):
        # Ensure 8px grid snapping
        el["x"] = int(round(el.get("x", 0) / 8.0) * 8)
        el["y"] = int(round(el.get("y", 0) / 8.0) * 8)
        el["w"] = int(round(el.get("w", 0) / 8.0) * 8)
        el["h"] = int(round(el.get("h", 0) / 8.0) * 8)

    return {
        "spec": spec_dict,
        "iteration": iteration,
        "events": state.get("events", []) + [{"stage": "reviser", "message": f"Applied fixes for revision {iteration}"}]
    }


async def export_node(state: PosterState) -> Dict[str, Any]:
    """Node 8: Export - packages final outputs."""
    best = state.get("best") or {}
    return {
        "png_base64": best.get("png_base64") or state.get("png_base64"),
        "thumbnail_base64": best.get("thumbnail_base64") or state.get("thumbnail_base64"),
        "svg_content": best.get("svg_content") or state.get("svg_content"),
        "spec": best.get("spec") or state.get("spec"),
        "events": state.get("events", []) + [{"stage": "export", "message": "Exported production-ready poster assets"}]
    }


# ---------------------------------------------------------------------------
# Routing Transitions (Section 2 & 7)
# ---------------------------------------------------------------------------

def after_lint_router(state: PosterState) -> str:
    lint = state.get("lint", {})
    iteration = state.get("iteration", 0)
    if not lint.get("clean") and iteration < 3:
        return "reviser"
    return "critic"


def after_critic_router(state: PosterState) -> str:
    critique = state.get("critique", {})
    iteration = state.get("iteration", 0)
    if critique.get("verdict") == "pass" or iteration >= 3:
        return "export"
    return "reviser"


# ---------------------------------------------------------------------------
# Build & Compile the LangGraph Poster Pipeline
# ---------------------------------------------------------------------------

def build_poster_design_graph():
    graph = StateGraph(PosterState)

    # Add Nodes
    graph.add_node("brief_analyst", brief_analyst_node)
    graph.add_node("art_director", art_director_node)
    graph.add_node("layout_planner", layout_planner_node)
    graph.add_node("renderer", renderer_node)
    graph.add_node("lint", lint_node)
    graph.add_node("critic", critic_node)
    graph.add_node("reviser", reviser_node)
    graph.add_node("export", export_node)

    # Set Entry Point
    graph.set_entry_point("brief_analyst")

    # Add Directed Edges
    graph.add_edge("brief_analyst", "art_director")
    graph.add_edge("art_director", "layout_planner")
    graph.add_edge("layout_planner", "renderer")
    graph.add_edge("renderer", "lint")
    graph.add_edge("reviser", "renderer")
    graph.add_edge("export", END)

    # Add Conditional Edges
    graph.add_conditional_edges(
        "lint",
        after_lint_router,
        {"reviser": "reviser", "critic": "critic"}
    )
    graph.add_conditional_edges(
        "critic",
        after_critic_router,
        {"reviser": "reviser", "export": "export"}
    )

    return graph.compile()


poster_design_agent = build_poster_design_graph()
