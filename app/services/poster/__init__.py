"""Poster Design Engine - Multi-Stage Deterministic Spec Renderer, Linter & Knowledge Base."""
from .spec import PosterSpec, PosterElement, CanvasConfig, BackgroundConfig, FontsConfig, OverlayScrim
from .linter import lint_poster_spec, LintReport
from .renderer import render_poster_spec, RenderResult
from .archetypes import ARCHETYPE_SPECS, get_archetype_template
from .knowledge import (
    RULE_CARDS, CULTURAL_FESTIVALS, REFERENCE_BRIEFS,
    search_rule_cards, get_cultural_rules, get_reference_briefs_by_type
)
from .image_gen import formulate_background_prompt, detect_hallucinated_text_in_image, apply_scrim_overlay
from .telemetry import log_poster_generation, record_human_feedback, export_training_dataset

__all__ = [
    # Phase 1: Foundation
    "PosterSpec",
    "PosterElement",
    "CanvasConfig",
    "BackgroundConfig",
    "FontsConfig",
    "OverlayScrim",
    "lint_poster_spec",
    "LintReport",
    "render_poster_spec",
    "RenderResult",
    "ARCHETYPE_SPECS",
    "get_archetype_template",
    # Phase 4: Knowledge Base & Cultural Add-on
    "RULE_CARDS",
    "CULTURAL_FESTIVALS",
    "REFERENCE_BRIEFS",
    "search_rule_cards",
    "get_cultural_rules",
    "get_reference_briefs_by_type",
    # Phase 5: Image Generation & Scrim Compositor
    "formulate_background_prompt",
    "detect_hallucinated_text_in_image",
    "apply_scrim_overlay",
    # Phase 6: Telemetry & Learning Loop
    "log_poster_generation",
    "record_human_feedback",
    "export_training_dataset",
]
