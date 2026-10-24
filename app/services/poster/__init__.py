"""Poster Design Engine - Multi-Stage Deterministic Spec Renderer & Linter."""
from .spec import PosterSpec, PosterElement, CanvasConfig, BackgroundConfig, FontsConfig, OverlayScrim
from .linter import lint_poster_spec, LintReport
from .renderer import render_poster_spec, RenderResult
from .archetypes import ARCHETYPE_SPECS, get_archetype_template

__all__ = [
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
]
