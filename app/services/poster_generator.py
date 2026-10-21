"""Automated High-Resolution Social Media Poster & Graphic Generation Service."""
import os
import base64
import html
import uuid
from pathlib import Path
from typing import Optional, Tuple


def _wrap_text(text: str, max_chars_per_line: int = 32, max_lines: int = 4) -> list[str]:
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
    subtitle: Optional[str] = None
) -> Tuple[str, str]:
    """
    Generates a branded, publication-ready vector poster (1080x1080).
    Returns a tuple of (data_uri, static_relative_url).
    """
    clean_brand = html.escape(brand.strip() or "Brand")
    clean_headline = html.escape(headline.strip() or "Executive Announcement")
    clean_cta = html.escape(call_to_action.strip() or "Discover More")
    clean_sub = html.escape(subtitle.strip() or "") if subtitle else ""

    # Theme selection based on tone
    tone_lower = tone.lower()
    if "authoritative" in tone_lower or "deep" in tone_lower:
        bg_start = "#060913"
        bg_end = "#0d1b2a"
        accent_color = "#38bdf8"
        accent_gradient = "linear-gradient(135deg, #38bdf8, #818cf8)"
        badge_bg = "rgba(56, 189, 248, 0.15)"
        badge_border = "#0284c7"
    elif "warm" in tone_lower or "growth" in tone_lower:
        bg_start = "#06130e"
        bg_end = "#0b251a"
        accent_color = "#34d399"
        accent_gradient = "linear-gradient(135deg, #10b981, #34d399)"
        badge_bg = "rgba(16, 185, 129, 0.15)"
        badge_border = "#059669"
    elif "witty" in tone_lower or "punchy" in tone_lower:
        bg_start = "#160b18"
        bg_end = "#2a082b"
        accent_color = "#f43f5e"
        accent_gradient = "linear-gradient(135deg, #f43f5e, #fb7185)"
        badge_bg = "rgba(244, 63, 94, 0.15)"
        badge_border = "#e11d48"
    else: # default visionary tech indigo
        bg_start = "#080915"
        bg_end = "#131336"
        accent_color = "#818cf8"
        accent_gradient = "linear-gradient(135deg, #6366f1, #a855f7)"
        badge_bg = "rgba(99, 102, 241, 0.18)"
        badge_border = "#4f46e5"

    width = 1080
    height = 1080 if platform.lower() != "twitter" else 675

    wrapped_headline = _wrap_text(clean_headline, max_chars_per_line=28, max_lines=4)
    headline_tspans = "".join(
        f'<tspan x="90" dy="{58 if i > 0 else 0}">{line}</tspan>'
        for i, line in enumerate(wrapped_headline)
    )

    platform_label = platform.upper() + " SPOTLIGHT"
    poster_id = str(uuid.uuid4())

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{bg_start}" />
      <stop offset="100%" stop-color="{bg_end}" />
    </linearGradient>
    <radialGradient id="meshGlow" cx="80%" cy="20%" r="60%">
      <stop offset="0%" stop-color="{accent_color}" stop-opacity="0.35" />
      <stop offset="70%" stop-color="{accent_color}" stop-opacity="0.05" />
      <stop offset="100%" stop-color="{bg_start}" stop-opacity="0" />
    </radialGradient>
    <radialGradient id="meshGlow2" cx="20%" cy="85%" r="50%">
      <stop offset="0%" stop-color="{accent_color}" stop-opacity="0.2" />
      <stop offset="100%" stop-color="{bg_start}" stop-opacity="0" />
    </radialGradient>
    <filter id="glass" x="0" y="0" width="100%" height="100%">
      <feGaussianBlur stdDeviation="40" result="blur" />
    </filter>
  </defs>

  <!-- Background Layer -->
  <rect width="{width}" height="{height}" fill="url(#bgGrad)" />
  <circle cx="{width * 0.85}" cy="{height * 0.2}" r="380" fill="url(#meshGlow)" />
  <circle cx="{width * 0.15}" cy="{height * 0.8}" r="300" fill="url(#meshGlow2)" />

  <!-- Ambient Grid Patterns -->
  <g opacity="0.06">
    <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse">
      <path d="M 60 0 L 0 0 0 60" fill="none" stroke="#ffffff" stroke-width="1" />
    </pattern>
    <rect width="{width}" height="{height}" fill="url(#grid)" />
  </g>

  <!-- Outer Glass Frame -->
  <rect x="40" y="40" width="{width - 80}" height="{height - 80}" rx="32" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="2" />

  <!-- Brand Pill & Platform Badge -->
  <g transform="translate(90, 100)">
    <!-- Brand Pill -->
    <rect width="260" height="48" rx="24" fill="{badge_bg}" stroke="{badge_border}" stroke-width="1.5" />
    <circle cx="28" cy="24" r="6" fill="{accent_color}" />
    <text x="46" y="31" fill="#ffffff" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="16" font-weight="800" letter-spacing="1.5">
      {clean_brand.upper()}
    </text>
  </g>

  <g transform="translate({width - 340}, 100)">
    <!-- Platform Tag -->
    <rect width="250" height="48" rx="24" fill="rgba(255,255,255,0.05)" stroke="rgba(255,255,255,0.1)" stroke-width="1" />
    <text x="125" y="30" text-anchor="middle" fill="#94a3b8" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="13" font-weight="700" letter-spacing="1.5">
      {platform_label}
    </text>
  </g>

  <!-- Main Headline Quote -->
  <g transform="translate(0, {height * 0.38})">
    <text x="90" y="0" fill="{accent_color}" font-family="Georgia, serif" font-size="90" font-weight="700" opacity="0.4">“</text>
    <text fill="#ffffff" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="46" font-weight="800" letter-spacing="-1">
      {headline_tspans}
    </text>
  </g>

  <!-- Quote divider / takeaway box -->
  <g transform="translate(90, {height - 240})">
    <rect width="{width - 180}" height="100" rx="20" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.07)" stroke-width="1" />
    <circle cx="45" cy="50" r="16" fill="{accent_color}" fill-opacity="0.2" />
    <text x="45" y="55" text-anchor="middle" fill="{accent_color}" font-family="sans-serif" font-size="16" font-weight="bold">✦</text>
    <text x="80" y="44" fill="#cbd5e1" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="16" font-weight="600">
      Verified Official Communication
    </text>
    <text x="80" y="68" fill="#64748b" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="14">
      Orchestrated by autonomous specialist agents with quality assurance.
    </text>
  </g>

  <!-- Footer CTA Action -->
  <g transform="translate(90, {height - 100})">
    <text x="0" y="0" fill="{accent_color}" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="18" font-weight="800" letter-spacing="0.5">
      👉 {clean_cta}
    </text>
  </g>

  <g transform="translate({width - 270}, {height - 100})">
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
