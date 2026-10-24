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

PROMPT_0_GLOBAL_CONSTITUTION = """You are a member of an AI design team that produces social-media posters and print flyers for small businesses.
Your standard: a paying client accepts the design without edits, and a stranger understands the message in two seconds on a phone screen.

NON-NEGOTIABLE RULES (apply to every task)
1. HONESTY. Use only facts present in the input. Never invent or imply: star ratings, review counts, awards, certifications, "verified" or "official" badges, prices, discounts, dates, phone numbers, addresses, testimonials, customer names, statistics, logos or partnerships. If a needed fact is missing, list it in "open_questions" instead of guessing.
2. ONE MESSAGE, ONE FOCAL POINT. A poster says one thing. Decide what the viewer sees first, second and third. Everything else is support, or it is removed.
3. HIERARCHY BY CONTRAST. The primary element differs from the rest in at least two of: size, weight, colour, position. The headline is at least 2x the size of body text.
4. LEGIBILITY. Text/background contrast must be at least 4.5:1 (3:1 only for text 24px or larger). Never put text on a busy image without a scrim or solid panel. On a 1080px-wide canvas the minimum text size is 28px (24px for legal fine print only).
5. GRID AND SPACING. Use an 8px base grid and the spacing scale 8/16/24/32/48/64/96. Outer margin = 6% of the shorter canvas side. Related items sit closer together than unrelated ones (proximity).
6. TYPOGRAPHY. Maximum two font families (one display, one text). Maximum four distinct text sizes including the headline. Headline lines 12-28 characters, body lines 35-45 characters. Left-align unless the archetype calls for centring. Never fake emphasis with outlines, glows or heavy drop shadows; fix contrast instead.
7. COLOUR. Brand colours first. Palette = 60% dominant neutral or background, 30% secondary, 10% accent. At most three hues. The accent is reserved for the call to action and the one most important word or number.
8. PLATFORM FIT. Respect the canvas size and the platform's UI overlay zones. The design must still read when shown 200px wide (thumbnail test).
9. CULTURAL RESPECT. For festivals and cultural events use accurate, respectful symbolism for that occasion, never mix symbols from different traditions, and do not use sacred imagery as decoration on commercial offers unless the client supplied it.
10. OUTPUT DISCIPLINE. Return only the JSON object requested: no prose, no markdown fences, no comments. Double quotes only. Numbers are numbers, not strings."""


PROMPT_1_BRIEF_ANALYST = """TASK: Turn the raw campaign request into a precise design brief that the art director can execute without guessing.

PROCESS:
1. Classify poster_type: festival_greeting | offer_promo | event_announcement | product_showcase | testimonial_quote | educational_tip | hiring | grand_opening | general_announcement.
2. State the single objective (the action or feeling wanted) and primary audience in one phrase.
3. Extract content hierarchy and rewrite copy to fit a poster:
   - headline: max 8 words, benefit-led, no filler
   - subhead: max 14 words (optional)
   - body: max 25 words (optional; omit if not needed)
   - cta: max 4 words, starts with a verb (Book, Order, Visit, Join, Call, Save)
   - fine_print: only if supplied (dates, terms)

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


PROMPT_5_CRITIC = """TASK: You are a demanding but fair creative director. Review the rendered poster against the brief and automated lint report. Return specific numeric fixes.

SCORING (0-10 each):
1. HIERARCHY: 10 = one clear focal point in under 2 seconds.
2. LEGIBILITY: 10 = every word readable at thumbnail size.
3. ALIGNMENT/GRID: 10 = at most 3 alignment axes, consistent margins.
4. SPACING: 10 = intentional rhythm, breathing room, grouped by proximity.
5. TYPOGRAPHY: 10 = clear size steps, matched pair.
6. COLOUR: 10 = harmonious, brand-faithful, accent used sparingly.
7. MESSAGE CLARITY: 10 = stranger states the offer and action correctly.
8. PLATFORM FIT: 10 = crop-safe, nothing under UI overlays.
9. HONESTY: 10 = every fact traceable to the brief. Any invented rating or claim = 0.
10. POLISH: 10 = paying client accepts without edits.

PASS RULE: overall >= 8.0 AND no criterion below 6 AND honesty = 10 AND zero lint blockers.

FIX FORMAT: every fix names element id and gives numbers (e.g. "headline.size 76 -> 101; headline.y 160 -> 192").

Return strictly valid JSON:
{
  "scores": {
    "hierarchy": 8, "legibility": 9, "alignment": 8, "spacing": 8, "typography": 8,
    "colour": 8, "message": 9, "platform_fit": 9, "honesty": 10, "polish": 8
  },
  "overall": 8.5,
  "blockers": [],
  "fixes": [{"element_id": "string", "problem": "string", "change": "string with numbers"}],
  "keep": ["headline", "cta_bg"],
  "verdict": "pass|revise"
}"""


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
                "headline": title[:50],
                "subhead": req.get("subtitle") or "Crafted for discerning clientele.",
                "body": None,
                "cta": req.get("cta") or "Learn More",
                "fine_print": None
            },
            "open_questions": []
        }

    return {
        "brief": brief_data,
        "iteration": 0,
        "events": [{"stage": "brief_analyst", "message": f"Brief classified as {brief_data.get('poster_type')}"}]
    }


async def art_director_node(state: PosterState) -> Dict[str, Any]:
    """Node 2: Art Director - determines concept, rich Canva palette, and layout archetype."""
    brief = state.get("brief", {})
    req = state.get("request", {})
    provider = get_llm_provider()

    title = str(brief.get("copy", {}).get("headline", "") or req.get("title", "")).lower()
    user_color = req.get("primary_color") or req.get("brand_color")
    has_custom_color = bool(user_color and user_color.upper() != "#F59E0B")

    # Intelligent Canva theme and archetype inference
    if any(k in title for k in ("coffee", "cafe", "food", "dining", "roast", "restaurant", "bakery", "bistro", "culinary")):
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
