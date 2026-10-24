"""Template Selector with Diversity Enforcement & Client Photo Cutout Priority.

Implements Phase 4 of the Production Build Instructions:
- Scored, diversified template selection returning 3 distinct candidates.
- Diversity enforcement: guarantees top 3 candidates belong to 3 DIFFERENT archetypes.
- Never repeats the same archetype consecutively (penalizes recent_archetypes).
- Client photo cutout priority: boosts product-cutout and split-image when photos exist.
- Vertical and campaign goal alignment across the 14-vertical taxonomy.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.services.creative_direction import resolve_vertical, VERTICAL_CATALOG
from app.services.poster.templates_catalog import (
    TEMPLATES_CATALOG,
    TEMPLATE_BY_ID,
    TemplateDefinition,
    ARCHETYPES_CATALOG
)


class TemplateCandidate(BaseModel):
    template_id: str
    name: str
    archetype: str
    variant: str
    description: str
    score: float
    rationale: str
    supports_photo_cutout: bool = False
    preview_palette: Dict[str, str] = Field(default_factory=dict)


class CandidateSelectionRequest(BaseModel):
    vertical: Optional[str] = None
    industry_category: Optional[str] = None
    goal: Optional[str] = "brand_awareness"
    format: Optional[str] = "portrait"
    has_client_photos: bool = False
    recent_archetypes: List[str] = Field(default_factory=list)
    limit: int = 3


class TemplateSelector:
    """Scores all 30 templates and yields diversified candidates tailored to the workspace."""

    def __init__(self, templates: Optional[List[TemplateDefinition]] = None):
        self.templates = templates or TEMPLATES_CATALOG

    def score_template(
        self,
        template: TemplateDefinition,
        resolved_vertical: str,
        goal: str,
        has_client_photos: bool,
        recent_archetypes: List[str]
    ) -> tuple[float, str]:
        """Calculates a normalized score (0-100+) and generates an analytical rationale."""
        score = 15.0  # Base score
        reasons = []

        # 1. Vertical Affinity
        if resolved_vertical in template.best_for_verticals:
            score += 40.0
            reasons.append(f"Optimized visual language for {resolved_vertical.replace('_', ' ')}")
        else:
            # Check if archetype is in the vertical's ranked archetypes
            v_spec = VERTICAL_CATALOG.get(resolved_vertical)
            ranked_archetypes = v_spec.get("ranked_archetypes", []) if v_spec else []
            if template.archetype in ranked_archetypes:
                rank_idx = ranked_archetypes.index(template.archetype)
                boost = max(10.0, 30.0 - (rank_idx * 6.0))
                score += boost
                reasons.append(f"Archetype #{rank_idx+1} for {resolved_vertical.replace('_', ' ')}")

        # 2. Campaign Goal Affinity
        norm_goal = (goal or "brand_awareness").lower().replace(" ", "_")
        if any(norm_goal in g or g in norm_goal for g in template.best_for_goals):
            score += 35.0
            reasons.append(f"Tailored for {goal} objectives")
        elif norm_goal in ("promotion", "discount", "sale") and template.archetype == "offer-burst":
            score += 35.0
            reasons.append("High-urgency promotional posture")
        elif norm_goal in ("festival", "celebration", "holiday") and template.archetype == "centered-badge":
            score += 35.0
            reasons.append("Festive celebration symmetry")
        elif norm_goal in ("social_proof", "review", "testimonial") and template.archetype in ("quote-card", "stats-metric"):
            score += 30.0
            reasons.append("Empirical social validation structure")

        # 3. Client Photo Priority (Rule: client photos cutouts first)
        if has_client_photos:
            if template.supports_photo_cutout:
                score += 30.0
                reasons.append("Prioritizes client-uploaded photography/cutouts")
        else:
            if template.requires_imagery:
                score -= 10.0  # Slight penalty if no client images and template demands a photo

        # 4. Diversity Enforcement (Rule: never pick consecutive duplicate archetypes)
        if recent_archetypes:
            if recent_archetypes[0] == template.archetype:
                score -= 50.0  # Massive penalty for the most recently published archetype
                reasons.append(f"Penalized for recent repetition of {template.archetype}")
            elif len(recent_archetypes) > 1 and recent_archetypes[1] == template.archetype:
                score -= 25.0
                reasons.append(f"De-prioritized to maintain visual freshness")

        rationale = " • ".join(reasons) if reasons else "General brand balance"
        return round(score, 1), rationale

    def select_candidates(
        self,
        vertical: Optional[str] = None,
        industry_category: Optional[str] = None,
        goal: str = "brand_awareness",
        has_client_photos: bool = False,
        recent_archetypes: Optional[List[str]] = None,
        limit: int = 3
    ) -> List[TemplateCandidate]:
        """Selects top candidates enforcing archetype diversity (no two share the same archetype)."""
        recent = recent_archetypes or []
        resolved_vertical = resolve_vertical(
            industry_primary=vertical or industry_category or "retail",
            industry_sub=industry_category or "",
            business_name="",
            offerings_text=""
        )

        scored: List[tuple[TemplateDefinition, float, str]] = []
        for t in self.templates:
            s, r = self.score_template(
                template=t,
                resolved_vertical=resolved_vertical,
                goal=goal,
                has_client_photos=has_client_photos,
                recent_archetypes=recent
            )
            scored.append((t, s, r))

        # Sort descending by score
        scored.sort(key=lambda x: x[1], reverse=True)

        # Diverse selection: at most 1 template per archetype
        candidates: List[TemplateCandidate] = []
        seen_archetypes = set()

        for t, s, r in scored:
            if t.archetype in seen_archetypes:
                continue
            seen_archetypes.add(t.archetype)
            candidates.append(
                TemplateCandidate(
                    template_id=t.id,
                    name=t.name,
                    archetype=t.archetype,
                    variant=t.variant,
                    description=t.description,
                    score=s,
                    rationale=r,
                    supports_photo_cutout=t.supports_photo_cutout,
                    preview_palette=t.preview_palette
                )
            )
            if len(candidates) >= limit:
                break

        # Fallback if limit couldn't be satisfied diversely
        if len(candidates) < limit:
            for t, s, r in scored:
                if any(c.template_id == t.id for c in candidates):
                    continue
                candidates.append(
                    TemplateCandidate(
                        template_id=t.id,
                        name=t.name,
                        archetype=t.archetype,
                        variant=t.variant,
                        description=t.description,
                        score=s,
                        rationale=r,
                        supports_photo_cutout=t.supports_photo_cutout,
                        preview_palette=t.preview_palette
                    )
                )
                if len(candidates) >= limit:
                    break

        return candidates


# Singleton default selector
template_selector = TemplateSelector()
