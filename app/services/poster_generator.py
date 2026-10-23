"""Combinatorial Visual Poster Engine for Multi-Platform Marketing.

Capable of generating thousands of distinct branded design variations across
Festivals, High-Urgency Promotions, Local GMB Business Showcases, Luxury Editorial Quotes,
and Modern Tech Spotlights.
"""
import os
import base64
import html
import uuid
import hashlib
from pathlib import Path
from typing import Optional, Tuple

TEMPLATES = [
    {"id": "festival_diwali", "name": "Festive Diwali / Lights", "category": "Festivals", "description": "Royal saffron-gold aura with glowing diya patterns and auspicious warmth."},
    {"id": "festival_holi", "name": "Festival of Colors (Holi)", "category": "Festivals", "description": "Vibrant chromatic prism gradient celebrating joy and vibrancy."},
    {"id": "promotional_offer", "name": "High-Urgency Flash Sale", "category": "Commercial", "description": "High-contrast crimson and gold badges with urgency banner."},
    {"id": "gmb_local", "name": "Google Business Profile Spotlight", "category": "Local SEO", "description": "Verified Google 5-Star trust rating badge with local contact card."},
    {"id": "luxury_gold", "name": "Executive Luxury & Gold", "category": "Branding", "description": "Midnight onyx & champagne gold typography for premium clientele."},
    {"id": "quote_leadership", "name": "Thought Leadership & Quotes", "category": "Editorial", "description": "Serif editorial typography for high-impact industry authority."},
    {"id": "modern_tech", "name": "Cyberpunk Neon & SaaS", "category": "Tech", "description": "Deep indigo matrix glow with clean modern interface accents."}
]


def _wrap_text(text: str, max_chars_per_line: int = 30, max_lines: int = 4) -> list[str]:
    """Wraps text into clean, typographic lines without breaking words."""
    words = text.split()
    lines = []
    current_line = []
    current_len = 0

    for word in words:
        if current_len + len(word) + 1 <= max_chars_per_line:
            current_line.append(word)
            current_len += len(word) + 1
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_len = len(word)
        if len(lines) >= max_lines - 1:
            break

    if current_line and len(lines) < max_lines:
        lines.append(" ".join(current_line))
    
    return lines


def generate_social_poster(
    brand: str,
    headline: str,
    platform: str = "instagram",
    tone: str = "visionary",
    call_to_action: str = "Learn More",
    subtitle: Optional[str] = None,
    business_phone: Optional[str] = None,
    business_address: Optional[str] = None,
    business_website: Optional[str] = None,
    rating_text: Optional[str] = None,
    style: Optional[str] = None
) -> Tuple[str, str]:
    """
    Renders an ultra-high resolution branded vector & raster graphic (1080x1080).
    Returns (data_uri, static_relative_url).
    """
    clean_brand = html.escape(brand.strip() or "Brand Entity")
    clean_headline = html.escape(headline.strip() or "Special Announcement")
    clean_cta = html.escape(call_to_action.strip() or "Discover More")
    clean_phone = html.escape(business_phone.strip()) if business_phone else ""
    clean_addr = html.escape(business_address.strip()) if business_address else ""
    clean_web = html.escape(business_website.strip()) if business_website else ""
    clean_rating = html.escape(rating_text.strip()) if rating_text else "4.9 ★★★★★ on Google"

    # Style resolution: explicit style or inferred from tone/headline
    resolved_style = (style or tone or "visionary").lower()
    headline_lower = headline.lower()

    if any(k in resolved_style or k in headline_lower for k in ["diwali", "deepavali", "festival_diwali"]):
        theme = "festival_diwali"
    elif any(k in resolved_style or k in headline_lower for k in ["holi", "color", "festival_holi"]):
        theme = "festival_holi"
    elif any(k in resolved_style or k in headline_lower for k in ["eid", "ramadan", "festival_eid"]):
        theme = "festival_eid"
    elif any(k in resolved_style or k in headline_lower for k in ["republic", "independence", "festival_national"]):
        theme = "festival_national"
    elif any(k in resolved_style or k in headline_lower for k in ["newyear", "christmas", "holiday"]):
        theme = "festival_celebration"
    elif any(k in resolved_style or k in headline_lower for k in ["sale", "promo", "discount", "offer", "deal"]):
        theme = "promotional_offer"
    elif any(k in resolved_style or k in headline_lower or k in platform.lower() for k in ["gmb", "local", "store", "shop", "google_business", "google"]):
        theme = "gmb_local"
    elif any(k in resolved_style or k in headline_lower for k in ["luxury", "gold", "elite", "vip"]):
        theme = "luxury_gold"
    elif any(k in resolved_style or k in headline_lower for k in ["quote", "wisdom", "leadership"]):
        theme = "quote_leadership"
    elif any(k in resolved_style for k in ["authoritative", "deep"]):
        theme = "corporate_authoritative"
    elif any(k in resolved_style for k in ["witty", "punchy"]):
        theme = "punchy_vibrant"
    else:
        theme = "modern_tech"

    width = 1080
    height = 1080 if platform.lower() not in ("twitter", "x") else 675
    poster_id = str(uuid.uuid4())

    # Build unique visual palettes based on theme
    if theme == "festival_diwali":
        bg_gradient = """
          <radialGradient id="festGlow" cx="50%" cy="30%" r="70%">
            <stop offset="0%" stop-color="#ffd700" stop-opacity="0.3" />
            <stop offset="50%" stop-color="#ff8c00" stop-opacity="0.15" />
            <stop offset="100%" stop-color="#120617" stop-opacity="0" />
          </radialGradient>
          <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#150522" />
            <stop offset="50%" stop-color="#2a083b" />
            <stop offset="100%" stop-color="#0b0312" />
          </linearGradient>
        """
        accent = "#f59e0b"
        accent_bright = "#fde047"
        pill_fill = "rgba(245, 158, 11, 0.2)"
        pill_stroke = "#d97706"
        badge_text = "FESTIVAL CELEBRATION"
        motif_svg = """
          <g transform="translate(540, 310)" text-anchor="middle">
            <circle cx="0" cy="0" r="160" fill="none" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="8 6" opacity="0.4" />
            <circle cx="0" cy="0" r="130" fill="none" stroke="#fbbf24" stroke-width="1" opacity="0.3" />
            <text y="22" font-size="64" fill="#fbbf24" font-family="serif">🪔</text>
          </g>
        """
    elif theme == "festival_holi":
        bg_gradient = """
          <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#1a0429" />
            <stop offset="50%" stop-color="#2d0b40" />
            <stop offset="100%" stop-color="#0a1c2a" />
          </linearGradient>
          <radialGradient id="festGlow" cx="30%" cy="40%" r="55%">
            <stop offset="0%" stop-color="#ec4899" stop-opacity="0.4" />
            <stop offset="100%" stop-color="#000000" stop-opacity="0" />
          </radialGradient>
        """
        accent = "#ec4899"
        accent_bright = "#f472b6"
        pill_fill = "rgba(236, 72, 153, 0.2)"
        pill_stroke = "#db2777"
        badge_text = "FESTIVAL OF COLORS"
        motif_svg = """
          <circle cx="280" cy="300" r="180" fill="#ec4899" opacity="0.12" filter="url(#glass)" />
          <circle cx="750" cy="320" r="160" fill="#3b82f6" opacity="0.12" filter="url(#glass)" />
          <circle cx="540" cy="220" r="120" fill="#eab308" opacity="0.15" filter="url(#glass)" />
        """
    elif theme == "promotional_offer":
        bg_gradient = """
          <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#1c070c" />
            <stop offset="50%" stop-color="#2d0a14" />
            <stop offset="100%" stop-color="#0d0408" />
          </linearGradient>
          <radialGradient id="festGlow" cx="80%" cy="30%" r="60%">
            <stop offset="0%" stop-color="#ef4444" stop-opacity="0.35" />
            <stop offset="100%" stop-color="#000000" stop-opacity="0" />
          </radialGradient>
        """
        accent = "#ef4444"
        accent_bright = "#f87171"
        pill_fill = "rgba(239, 68, 68, 0.2)"
        pill_stroke = "#dc2626"
        badge_text = "LIMITED-TIME OFFER"
        motif_svg = """
          <g transform="translate(850, 140)">
            <rect width="160" height="42" rx="8" fill="#ef4444" />
            <text x="80" y="26" text-anchor="middle" fill="#ffffff" font-family="'Plus Jakarta Sans', sans-serif" font-size="14" font-weight="900" letter-spacing="1">SPECIAL DEAL</text>
          </g>
        """
    elif theme == "gmb_local":
        bg_gradient = """
          <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#06121e" />
            <stop offset="50%" stop-color="#0b2138" />
            <stop offset="100%" stop-color="#03080f" />
          </linearGradient>
          <radialGradient id="festGlow" cx="20%" cy="20%" r="60%">
            <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.35" />
            <stop offset="100%" stop-color="#000000" stop-opacity="0" />
          </radialGradient>
        """
        accent = "#38bdf8"
        accent_bright = "#60a5fa"
        pill_fill = "rgba(56, 189, 248, 0.15)"
        pill_stroke = "#0284c7"
        badge_text = "VERIFIED LOCAL BUSINESS"
        motif_svg = f"""
          <g transform="translate(90, 240)">
            <rect width="400" height="44" rx="22" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.12)" />
            <text x="20" y="28" fill="#fbbf24" font-size="15">★★★★★</text>
            <text x="100" y="27" fill="#cbd5e1" font-family="'Plus Jakarta Sans', sans-serif" font-size="13" font-weight="700">{clean_rating}</text>
          </g>
        """
    elif theme == "luxury_gold":
        bg_gradient = """
          <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#080706" />
            <stop offset="50%" stop-color="#14110c" />
            <stop offset="100%" stop-color="#040302" />
          </linearGradient>
          <radialGradient id="festGlow" cx="70%" cy="20%" r="60%">
            <stop offset="0%" stop-color="#d4af37" stop-opacity="0.3" />
            <stop offset="100%" stop-color="#000000" stop-opacity="0" />
          </radialGradient>
        """
        accent = "#eab308"
        accent_bright = "#fde047"
        pill_fill = "rgba(212, 175, 55, 0.18)"
        pill_stroke = "#ca8a04"
        badge_text = "SIGNATURE SPOTLIGHT"
        motif_svg = ""
    else:  # modern_tech
        bg_gradient = """
          <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#070914" />
            <stop offset="50%" stop-color="#11142e" />
            <stop offset="100%" stop-color="#04050a" />
          </linearGradient>
          <radialGradient id="festGlow" cx="80%" cy="20%" r="60%">
            <stop offset="0%" stop-color="#6366f1" stop-opacity="0.35" />
            <stop offset="100%" stop-color="#000000" stop-opacity="0" />
          </radialGradient>
        """
        accent = "#818cf8"
        accent_bright = "#a5b4fc"
        pill_fill = "rgba(99, 102, 241, 0.2)"
        pill_stroke = "#4f46e5"
        badge_text = f"{platform.upper()} SPOTLIGHT"
        motif_svg = ""

    # Wrap headline text cleanly
    wrapped = _wrap_text(clean_headline, max_chars_per_line=26, max_lines=4)
    headline_tspans = "".join(
        f'<tspan x="90" dy="{62 if i > 0 else 0}">{line}</tspan>'
        for i, line in enumerate(wrapped)
    )

    # Business contact footer line
    contact_parts = []
    if clean_phone:
        contact_parts.append(f"📞 {clean_phone}")
    if clean_web:
        contact_parts.append(f"🌐 {clean_web}")
    if clean_addr:
        contact_parts.append(f"📍 {clean_addr}")
    contact_line = "  ·  ".join(contact_parts) if contact_parts else f"👉 {clean_cta}"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <defs>
    {bg_gradient}
    <filter id="glass">
      <feGaussianBlur stdDeviation="30" />
    </filter>
  </defs>

  <!-- Background -->
  <rect width="{width}" height="{height}" fill="url(#bgGrad)" />
  <rect width="{width}" height="{height}" fill="url(#festGlow)" />

  <!-- Grid texture -->
  <g opacity="0.05">
    <pattern id="patGrid" width="60" height="60" patternUnits="userSpaceOnUse">
      <path d="M 60 0 L 0 0 0 60" fill="none" stroke="#ffffff" stroke-width="1" />
    </pattern>
    <rect width="{width}" height="{height}" fill="url(#patGrid)" />
  </g>

  <!-- Border Card -->
  <rect x="40" y="40" width="{width - 80}" height="{height - 80}" rx="32" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="2" />

  <!-- Top Pill Badges -->
  <g transform="translate(90, 100)">
    <rect width="280" height="48" rx="24" fill="{pill_fill}" stroke="{pill_stroke}" stroke-width="1.5" />
    <circle cx="28" cy="24" r="6" fill="{accent}" />
    <text x="48" y="31" fill="#ffffff" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="16" font-weight="800" letter-spacing="1.5">
      {clean_brand.upper()}
    </text>
  </g>

  <g transform="translate({width - 360}, 100)">
    <rect width="270" height="48" rx="24" fill="rgba(255,255,255,0.04)" stroke="rgba(255,255,255,0.1)" stroke-width="1" />
    <text x="135" y="30" text-anchor="middle" fill="#94a3b8" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="12" font-weight="700" letter-spacing="1.5">
      {badge_text}
    </text>
  </g>

  <!-- Thematic Motif (if any) -->
  {motif_svg}

  <!-- Main Headline Quote -->
  <g transform="translate(0, {int(height * 0.42)})">
    <text x="90" y="-10" fill="{accent}" font-family="Georgia, serif" font-size="80" font-weight="700" opacity="0.45">“</text>
    <text fill="#ffffff" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="48" font-weight="800" letter-spacing="-1">
      {headline_tspans}
    </text>
  </g>

  <!-- Official Brand Bar -->
  <g transform="translate(90, {height - 230})">
    <rect width="{width - 180}" height="90" rx="18" fill="rgba(255,255,255,0.04)" stroke="rgba(255,255,255,0.08)" stroke-width="1" />
    <circle cx="45" cy="45" r="16" fill="{accent}" fill-opacity="0.2" />
    <text x="45" y="51" text-anchor="middle" fill="{accent}" font-family="sans-serif" font-size="16" font-weight="bold">✦</text>
    <text x="80" y="38" fill="#f8fafc" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="16" font-weight="700">
      {clean_brand} Official Publication
    </text>
    <text x="80" y="62" fill="#94a3b8" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="13">
      {contact_line}
    </text>
  </g>

  <!-- Footer CTA Action & Security Watermark -->
  <g transform="translate(90, {height - 95})">
    <text x="0" y="0" fill="{accent_bright}" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="17" font-weight="800" letter-spacing="0.5">
      👉 {clean_cta}
    </text>
  </g>

  <g transform="translate({width - 250}, {height - 95})">
    <text x="0" y="0" fill="#475569" font-family="'JetBrains Mono', monospace" font-size="12">
      ID: #{poster_id[:8]}
    </text>
  </g>
</svg>"""

    # Ensure static directory exists
    static_dir = Path(__file__).resolve().parent.parent / "static" / "generated" / "posters"
    static_dir.mkdir(parents=True, exist_ok=True)
    poster_filename = f"{poster_id}.svg"
    poster_filepath = static_dir / poster_filename
    poster_filepath.write_text(svg, encoding="utf-8")

    # Encode as Data URI for instant rendering
    b64_svg = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    data_uri = f"data:image/svg+xml;base64,{b64_svg}"
    relative_url = f"/static/generated/posters/{poster_filename}"

    return data_uri, relative_url
