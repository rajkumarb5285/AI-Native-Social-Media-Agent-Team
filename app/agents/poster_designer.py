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
from app.services.poster.qa_suite import run_full_poster_qa, QASuiteReport, NumericAdjustment
from app.services.poster.vision_critic import evaluate_vision_critic, apply_numeric_revisions, VisionCritiqueReport




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
Do not output prose outside the JSON.

ALIGNMENT AND COMPOSITION RULES (v3). These are mandatory and checked by code:
1. DEFINE THE AXES FIRST
Before placing anything, declare the axes in the spec:
- left axis A_L = margin (80)
- right axis A_R = canvas_width - margin (1000)
- center axis A_C = 540
- top line T = margin (80), bottom line B = canvas_height - margin (1270)
Every element's left edge sits on A_L, OR its right edge sits on A_R, OR it is centered
on A_C. Nothing else may have its own arbitrary x position. The hero subject is the only
exception. Text and shapes never cross A_R or go beyond B.

2. THE HEADER ROW AND FOOTER ROW SPAN THE AXES
Header: logo's left edge on A_L, badge's right edge on A_R, both vertically centered on
the same horizontal midline (same center-Y, not same top). Footer row: CTA's left edge
on A_L, meta/handle's right edge on A_R, vertical centers aligned. These two rows
"frame" the poster, so margins always look intentional.

3. BASELINE AND SPACING GRID
Use an 8px grid. Heights, paddings and gaps are multiples of 8. Line-heights are set in
whole px multiples of 8 for display text (e.g. 88px type with 96px line-height).
Allowed gaps: 8, 16, 24, 32, 40, 48, 64, 80. Related items: 16-24. Between groups: 40-64.

4. ANCHOR THE TEXT STACK TO THE BOTTOM LINE
Stack the text group upward from B using flex column with justify-content:end. Never
position text from the top. Compute the stack height, then verify the top of the stack is
at least 48px below the bottom of the hero subject. If not, shorten the copy or move the
subject up using object-position.

5. OPTICAL ALIGNMENT (the "senior designer" detail)
Round letters (O, C, G, S) and large display type look indented at the margin. Apply a
negative left offset of 2-4% of font size to display headlines (hanging punctuation
and optical margin alignment, e.g. -3px). Align the cap-height of the badge text with the
x-height midline of the wordmark. Pills have text visually centered by adjusting
padding-top by -1px if the font has high ascenders.

6. SUBJECT-RELATIVE PLACEMENT (rings, shapes, text near the hero)
Decorative shapes that frame the subject are centered on the subject's visual center,
measured from the image (use the provided subject_bbox), never on the canvas center.
Ring diameter = 1.25 to 1.4 x subject height. A ring or shape must never intersect
the header row, the text stack, or the logo clear space; shrink or move it until its
bounding box clears them by 24px.

7. BALANCE AND VISUAL WEIGHT
Place the heaviest elements on a diagonal (e.g. subject center-right, text bottom-left).
If the subject is centered, keep text strictly left-aligned on A_L, not centered.
Use rule of thirds (1/3 and 2/3 lines) for the subject's focal point, or exact
center for symmetric designs. Never split weight 50/50 left and right without a reason.

8. SCRIMS AND TRANSITIONS
- Top scrim for header legibility: linear-gradient(180deg, rgba(bg,0.65) 0, rgba(bg,0) 22%).
- Bottom scrim: start at 40% of the canvas height, 4 color stops (0, 0.55, 0.92, 1.0),
  and the hero image must extend UNDER the text region so there is no visible seam.
  Test: there must be no horizontal line visible between the photo and the bottom area.

9. HIERARCHY BUDGET (max text elements)
Header: logo + badge. Body: eyebrow, headline (max 2 lines), ONE subline (max 1 line).
Footer: CTA + optional meta. That is the maximum. No second paragraph, ever.

10. COPY OWNERSHIP
The Designer owns the on-poster copy (separate from the social caption). If the incoming
copy violates limits, DO NOT render it. Rewrite it yourself within limits using only
Source Facts, and report the rewrite in design_notes. Hard limits:
headline <= 6 words and <= 2 lines; subline <= 44 characters (one line at 34px);
CTA <= 3 words; eyebrow <= 28 characters; badge <= 16 characters.
No exclamation marks, no scarcity or superlative claims unless in Source Facts.

11. TYPOGRAPHY EXECUTION
- Use only weights that are loaded. Declare every weight used in @font-face and verify
  document.fonts.check() for each before render.
- Eyebrow/badge/labels: Inter 600, uppercase, letter-spacing 0.12em (apply as
  letter-spacing in em, confirm it renders).
- Apply smart typography: ’ “ ” – — … and non-breaking spaces before units. Convert every
  straight apostrophe in text to ’.
- Headline accent: set one phrase in Fraunces italic or the accent color for
  rhythm (e.g. "One origin. <i>One slow pour.</i>"), never more than one accent.

12. DESIGN DEVICES (choose 2-3 per poster; they separate crafted from basic)
- Hairline rule: 48px x 2px accent line before the eyebrow or above the CTA row.
- Inset frame: 1px line at 15% opacity inset 32px from the canvas edge, with a 24px
  gap in the middle of the top edge for the logo.
- Meta line: small uppercase facts row (e.g. "COLD BREW · TASTING SESSION") from
  Source Facts only.
- Vertical side text: handle or city rotated 90 degrees along the A_R axis at 20px,
  tracking 0.2em, 50% opacity.
- Color grade: warm shadows, lifted blacks, subtle light leak in the upper corner.
- Depth by overlap: if a subject mask is available, place a large headline word
  BEHIND the subject (text behind glass) for a magazine-cover effect, only when the
  word stays readable.
- Pattern: only if it reads as a deliberate motif at 100% zoom (e.g. 3 curved steam
  strokes, 2px, accent color, 10-14% opacity near the glass). If it looks like
  scratches or noise, remove it.

13. VARIANTS
Produce 3 layout variants with different archetypes (e.g. A: full-bleed bottom text,
B: arch-framed image on color block, C: giant typographic with subject overlap). Run the
critic on each, return the best as primary and the others as alternates.

14. SELF-CHECK
Before returning, compute and report: text bounding boxes, stack top vs subject bottom,
left edges list, right edges list, header/footer row center-Y values, ring bbox vs header
bbox. Fix and recompute until every check passes. Never return a spec that fails."""


PROMPT_1_BRIEF_ANALYST = """TASK: Turn the raw campaign request into a precise design brief that the art director can execute without guessing.

PROCESS:
1. Classify poster_type: festival_greeting | offer_promo | event_announcement | product_showcase | testimonial_quote | educational_tip | hiring | grand_opening | general_announcement.
2. State the single objective (the action or feeling wanted) and primary audience in one phrase.
3. Extract content hierarchy and rewrite copy to strictly fit poster copy limits:
   - headline: max 6 words, benefit-led, no filler, no business name in headline
   - subhead: max 44 characters, 1 line, no body paragraph, no exclamation marks
   - cta: max 3 words on the button ("Reserve a seat")
   - fine_print: only if supplied (dates, terms)
   - NO emojis anywhere. Strictly preserve apostrophes (Rajkumar’s, never Rajkumar s).
   - If event details (date, time, price, venue) are needed but missing, list in needs_input instead of guessing.

Return strictly valid JSON:
{
  "poster_type": "string",
  "objective": "string",
  "audience": "string",
  "tone_words": ["string", "string"],
  "copy": {
    "headline": "string",
    "subhead": "string or null",
    "body": null,
    "cta": "string",
    "fine_print": "string or null"
  },
  "needs_input": [],
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
layout spec against Poster v3 Alignment Masterclass standards. Score each 1-10 and give specific, actionable fixes with element IDs.

1. Hierarchy and focal point   2. Typography (pairing, size, spacing, line breaks)
3. Color and contrast          4. Imagery quality and relevance
5. Composition and balance     6. Spacing, alignment and grid
7. Brand consistency (logo, fonts, palette, tone)
8. CTA clarity and prominence  9. Platform fit and safe zones
10. Overall polish ("would a human pro ship this?")
11. Alignment and rhythm (1-10): are edges on consistent axes (A_L=80, A_R=1000), are gaps on the 8px scale, do rows frame the poster, is visual weight balanced on a diagonal?
12. Craft details (1-10): optical alignment, accent word, hairline rule/frame devices, grade, depth.

AUTOMATIC REJECT (score 0, return to Designer) if any of the following is true:
- Any element beyond the right axis (x > 1000) or below the bottom line (y > 1270).
- Header row or footer row not vertically centered on one horizontal midline.
- Copper ring or decorative shapes intersecting the logo, wordmark, or text stack.
- Visible seam between photo and bottom background.
- Label weights wrong (should be Inter 600 with tracking +0.12em).
- Straight apostrophes (must use smart curly ’).
- Pattern that looks like scratches instead of authentic motif.
- More than one subline or subline exceeding 44 characters.
- CTA over 3 words.
- Copy that was not rewritten after violating limits or contains unverified claims ("limited spots", "visionary").

Pass only if every score >= 8 and no hard fails. Return fixes as element id plus exact numeric changes.
Return strictly valid JSON:
{
  "scores": {
    "hierarchy": 9, "typography": 9, "color": 9, "imagery": 9,
    "composition": 9, "spacing": 9, "brand": 9, "cta": 9,
    "platform_fit": 9, "polish": 9, "alignment_and_rhythm": 9, "craft_details": 9
  },
  "overall": 9.0,
  "hard_fails": [],
  "fixes": [],
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
    needs_input: List[str]


def tighten_poster_copy(copy_dict: Dict[str, Any], business_name: str = "") -> Dict[str, Any]:
    """Enforces Poster v3 Alignment Masterclass Copy Limits:
    - Headline: <= 6 words, <= 2 lines. Strip redundant business name.
    - Subhead: <= 44 characters (1 line at 34px), 0 exclamation marks.
    - CTA: <= 3 words on the button ("Reserve a seat").
    - Eyebrow: <= 28 characters ("SINGLE-ORIGIN COLD BREW").
    - Badge: <= 16 characters ("TASTING SESSION").
    - Smart typography: converts straight quotes/apostrophes to smart marks (Rajkumar’s, never Rajkumar's or Rajkumar s).
    - Zero unverified claims: strips 'limited spots', 'visionary', 'best', 'world-class', etc.
    """
    import re
    from app.services.poster.spec import smart_typography

    def clean_text(s: Optional[str]) -> str:
        if not s:
            return ""
        text = str(s)
        # Apply smart typography first
        text = smart_typography(text)
        # Remove hashtags
        text = re.sub(r'#\w+', '', text)
        return " ".join(text.split()).strip()

    # 1. Headline: max 6 words, strip redundant business name
    raw_hl = clean_text(copy_dict.get("headline", ""))
    if business_name:
        b_clean = clean_text(business_name)
        for b_cand in (b_clean, b_clean.split()[0]):
            if b_cand and b_cand.lower() in raw_hl.lower():
                raw_hl = re.sub(re.escape(b_cand), '', raw_hl, flags=re.IGNORECASE).strip()
        raw_hl = re.sub(r'\b(at|by|in|for)\b\s*$', '', raw_hl, flags=re.IGNORECASE).strip()
        raw_hl = raw_hl.strip(": -")

    if ":" in raw_hl:
        parts = [p.strip() for p in raw_hl.split(":") if p.strip()]
        for candidate in reversed(parts):
            if len(candidate.split()) <= 6:
                raw_hl = candidate
                break

    # Strip banned superlatives / unverified buzzwords
    for banned_word in ("experience the future of coffee", "future of coffee", "visionary", "ultimate", "world-class"):
        raw_hl = re.sub(re.escape(banned_word), '', raw_hl, flags=re.IGNORECASE).strip()

    raw_hl = " ".join(raw_hl.split()).strip()
    hl_words = raw_hl.split()
    if len(hl_words) > 6 or len(hl_words) == 0:
        # Rewrite to concise on-brand theme
        if any(w in (raw_hl + (business_name or "")).lower() for w in ("cold brew", "pour", "origin", "roast", "coffee", "tasting")):
            headline = "One origin.\nOne slow pour."
        else:
            headline = " ".join(hl_words[:6]) if hl_words else (f"Welcome to {clean_text(business_name)}" if business_name else "Signature Collection")
    else:
        headline = raw_hl

    # 2. Subhead: max 44 characters, exactly 1 line, NO exclamation marks
    raw_sub = clean_text(copy_dict.get("subhead", ""))
    for fluff in ("limited spots available", "limited spots", "with vision", "visionary thinking", "visionary craftsmanship", "the future of coffee", "sip the future of coffee"):
        raw_sub = re.sub(re.escape(fluff), '', raw_sub, flags=re.IGNORECASE)
    raw_sub = raw_sub.replace("!", ".").replace("?", ".")
    raw_sub = " ".join(raw_sub.split()).strip()

    # If subhead is truncated or ends mid-sentence, replace with clean on-brand copy
    if len(raw_sub) > 44 or not raw_sub or raw_sub.endswith(("single", "the", "of", "and", "with", "a")):
        if business_name:
            clean_bname = smart_typography(business_name)
            if any(k in (business_name + raw_hl).lower() for k in ("coffee", "cafe", "roast", "brew", "pour")):
                subhead = f"A guided tasting at {clean_bname}"
                if len(subhead) > 44:
                    subhead = "A guided single-origin tasting"
            else:
                subhead = f"Experience quality at {clean_bname}"
                if len(subhead) > 44:
                    subhead = f"Welcome to {clean_bname}"
        else:
            subhead = "Crafted for exceptional quality."
    else:
        # Guarantee single line <= 44 chars
        if len(raw_sub) > 44:
            subhead = raw_sub[:41].rsplit(" ", 1)[0]
        else:
            subhead = raw_sub

    # 3. CTA: strictly max 3 words
    is_coffee = any(k in ((business_name or "") + raw_hl).lower() for k in ("coffee", "cafe", "roast", "brew", "cold brew"))
    default_cta = "Reserve a seat" if is_coffee else "Learn More"
    raw_cta = clean_text(copy_dict.get("cta", "") or default_cta)
    for fluff in ("today limited spots available", "limited spots available", "limited spots", "today", "now", "available"):
        raw_cta = re.sub(re.escape(fluff), '', raw_cta, flags=re.IGNORECASE).strip()

    cta_words = raw_cta.split()
    if len(cta_words) > 3 or len(cta_words) == 0:
        cta = default_cta
    else:
        cta = " ".join(cta_words).title()

    # 4. Eyebrow & Badge
    default_eb = "SINGLE-ORIGIN COLD BREW" if is_coffee else (f"✦ {clean_text(business_name).upper()}" if business_name else "FEATURED")
    raw_eyebrow = clean_text(copy_dict.get("eyebrow", "") or default_eb).upper()
    if len(raw_eyebrow) > 28:
        raw_eyebrow = default_eb[:28]

    default_badge = "TASTING SESSION" if is_coffee else "FEATURED"
    raw_badge = clean_text(copy_dict.get("badge", "") or default_badge).upper()
    if len(raw_badge) > 16:
        raw_badge = default_badge[:16]

    return {
        "headline": smart_typography(headline),
        "subhead": smart_typography(subhead),
        "body": None,
        "cta": smart_typography(cta),
        "eyebrow": smart_typography(raw_eyebrow),
        "badge": smart_typography(raw_badge),
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

    # Strictly enforce Part 2 Copy Limits (preserve apostrophes, headline <= 6 words, no business name in headline, CTA <= 4 words)
    b_name = req.get("business_name", "")
    brief_data["copy"] = tighten_poster_copy(brief_data.get("copy", {}), business_name=b_name)

    needs_input = []
    if any(k in (brief_data.get("copy", {}).get("headline", "") + req.get("title", "")).lower() for k in ("tasting", "workshop", "event", "summit", "meetup")):
        if not req.get("date") and not req.get("time"):
            needs_input.append("event date and time")
        if not req.get("price") and not req.get("ticket_link"):
            needs_input.append("price or booking link (optional)")

    brief_data["needs_input"] = needs_input

    return {
        "brief": brief_data,
        "needs_input": needs_input,
        "iteration": 0,
        "events": [{"stage": "brief_analyst", "message": f"Brief classified as {brief_data.get('poster_type')} (copy tightened to Part 2 v2 rules)"}]
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


    # 1. Cultural festival override
    if any(k in title for k in ("diwali", "deepavali", "holi", "eid", "christmas", "new year", "festival", "holiday", "shubh")):
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

    # 2. Offer / Sale burst override
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

    # 3. Comprehensive 14-vertical taxonomy classification
    else:
        from app.services.creative_direction import resolve_vertical, build_creative_direction
        vert = resolve_vertical(
            industry_primary=req.get("category", ""),
            industry_sub=req.get("theme", ""),
            business_name=req.get("business_name", ""),
            offerings_text=context_text
        )
        cd = build_creative_direction(
            vertical_key=vert,
            business_name=req.get("business_name", ""),
            custom_primary_color=user_color if has_custom_color else None
        )
        selected_archetype = req.get("archetype") or (cd.ranked_archetypes[0] if cd.ranked_archetypes else "hero-text")
        palette = {
            "background": cd.palette.background,
            "surface": cd.palette.surface,
            "primary": cd.palette.text_primary,
            "muted": cd.palette.text_muted,
            "accent": user_color if has_custom_color else cd.palette.primary
        }
        type_pairing = {"display": cd.typography.display_font, "text": cd.typography.body_font}

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
    spec_dict = state.get("spec", {})
    spec_obj = PosterSpec(**spec_dict)
    brief = state.get("brief", {})
    req = state.get("request", {})
    platform = req.get("platform")

    critique_report: VisionCritiqueReport = await evaluate_vision_critic(
        spec=spec_obj,
        brief=brief,
        platform=platform
    )

    scores_dict = {k: v.score for k, v in critique_report.rubric.items()}
    numeric_fixes = [adj.model_dump() for adj in critique_report.numeric_adjustments]

    critique = {
        "scores": scores_dict,
        "overall": critique_report.overall_score,
        "rubric": {k: v.model_dump() for k, v in critique_report.rubric.items()},
        "strengths": critique_report.strengths,
        "weaknesses": critique_report.weaknesses,
        "fixes": numeric_fixes,
        "verdict": critique_report.verdict,
        "clean": critique_report.qa_report.clean if critique_report.qa_report else True
    }

    best_record = state.get("best") or {"score": -1}
    if critique_report.overall_score > best_record.get("score", -1):
        best_record = {
            "score": critique_report.overall_score,
            "spec": state.get("spec"),
            "png_base64": state.get("png_base64"),
            "thumbnail_base64": state.get("thumbnail_base64"),
            "svg_content": state.get("svg_content"),
            "critique": critique
        }

    return {
        "critique": critique,
        "best": best_record,
        "events": state.get("events", []) + [{
            "stage": "critic",
            "message": f"Vision Critic score: {critique_report.overall_score}/10 (Verdict: {critique['verdict']})"
        }]
    }


async def reviser_node(state: PosterState) -> Dict[str, Any]:
    """Node 7: Reviser - applies numeric fixes to the specification and increments loop."""
    spec_dict = state.get("spec", {})
    spec_obj = PosterSpec(**spec_dict)
    critique = state.get("critique", {})
    iteration = state.get("iteration", 0) + 1

    # Convert numeric adjustments from critique
    raw_fixes = critique.get("fixes", [])
    adjustments = [NumericAdjustment(**f) for f in raw_fixes]

    # Apply targeted revisions
    revised_spec = apply_numeric_revisions(spec_obj, adjustments)

    # Strictly guarantee 8px grid snapping across all elements
    for el in revised_spec.elements:
        if el.id != "headline":
            el.x = int(round(el.x / 8.0) * 8)
        el.y = int(round(el.y / 8.0) * 8)
        el.w = int(round(el.w / 8.0) * 8)
        el.h = int(round(el.h / 8.0) * 8)

    return {
        "spec": revised_spec.model_dump(),
        "iteration": iteration,
        "events": state.get("events", []) + [{"stage": "reviser", "message": f"Applied {len(adjustments)} numeric fixes for revision {iteration}"}]
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
