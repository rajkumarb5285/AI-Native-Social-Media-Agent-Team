"""Business Understanding & Creative Direction Agent.

Analyzes the multi-factor business profile (primary/sub industry, business model,
positioning, offerings, personality, guardrails) and synthesizes a strict,
tailored CreativeDirection specification for downstream agents (art director,
copywriter, poster designer, pamphlet designer).
"""
import json
from typing import Dict, Any, List, Optional
from app.agents.base import BaseAgent
from app.services.creative_direction import (
    CreativeDirection,
    resolve_vertical,
    build_creative_direction,
    VERTICAL_CATALOG
)


from app.agents.base import BaseAgent, AgentInput, AgentOutput


class BusinessUnderstandingInput(AgentInput):
    profile: Dict[str, Any]
    offerings: Optional[List[Dict[str, Any]]] = None


class BusinessUnderstandingOutput(AgentOutput):
    creative_direction: Optional[CreativeDirection] = None


class BusinessUnderstandingAgent(BaseAgent[BusinessUnderstandingInput, BusinessUnderstandingOutput]):
    """Synthesizes high-level business profile intake into precise creative direction."""
    agent_id: str = "business-understanding"
    name: str = "Business Understanding Agent"
    department: str = "Strategy"
    description: str = "Synthesizes business profile intake into tailored creative direction."

    def __init__(self):
        super().__init__()

    async def execute(self, input_data: BusinessUnderstandingInput) -> BusinessUnderstandingOutput:
        cd = self.generate_creative_direction(input_data.profile, input_data.offerings)
        return BusinessUnderstandingOutput(success=True, creative_direction=cd)

    def generate_creative_direction(
        self,
        profile: Dict[str, Any],
        offerings: Optional[List[Dict[str, Any]]] = None
    ) -> CreativeDirection:
        """Synthesizes CreativeDirection from business profile and offerings."""
        business_name = profile.get("business_name", "") or profile.get("name", "")
        industry_primary = profile.get("industry_primary", "") or profile.get("category", "")
        industry_sub = profile.get("industry_sub", "")
        offerings_desc = profile.get("offerings_description", "")
        
        # Combine offering product names if available
        offerings_text = offerings_desc
        if offerings:
            offering_names = [o.get("name", "") for o in offerings if isinstance(o, dict)]
            if offering_names:
                offerings_text += " " + " ".join(offering_names)

        # 1. Resolve vertical strictly
        vertical = resolve_vertical(
            industry_primary=industry_primary,
            industry_sub=industry_sub,
            business_name=business_name,
            offerings_text=offerings_text
        )

        # 2. Extract brand colors if customized by client
        custom_primary = profile.get("primary_color")
        custom_secondary = profile.get("secondary_color")
        custom_accent = profile.get("accent_color")
        custom_bg = profile.get("background_color")

        # 3. Extract typography if customized by client
        custom_display = profile.get("display_font")
        custom_body = profile.get("body_font")

        # 4. Extract custom tone from personality
        personality = profile.get("personality_json", {})
        if isinstance(personality, str):
            try:
                personality = json.loads(personality)
            except Exception:
                personality = {}
        
        custom_tone = None
        if isinstance(personality, dict) and personality.get("tone"):
            custom_tone = personality.get("tone")
        elif isinstance(personality, list) and personality:
            custom_tone = ", ".join(personality)

        # 5. Build direction
        direction = build_creative_direction(
            vertical_key=vertical,
            business_name=business_name,
            custom_primary_color=custom_primary,
            custom_secondary_color=custom_secondary,
            custom_accent_color=custom_accent,
            custom_bg_color=custom_bg,
            custom_display_font=custom_display,
            custom_body_font=custom_body,
            custom_tone=custom_tone
        )

        # 6. Inject client-specific source facts / guardrails into custom_rules
        guardrails = profile.get("guardrails_json", {})
        if isinstance(guardrails, str):
            try:
                guardrails = json.loads(guardrails)
            except Exception:
                guardrails = {}

        if isinstance(guardrails, dict):
            disallowed = guardrails.get("disallowed_words", []) or guardrails.get("forbidden_terms", [])
            if disallowed and isinstance(disallowed, list):
                direction.disallowed_terms.extend([str(d).lower() for d in disallowed])

        return direction

    def run(self, input_data: BusinessUnderstandingInput) -> CreativeDirection:
        """Standard Agent interface."""
        return self.generate_creative_direction(input_data.profile, input_data.offerings)


def analyze_business_profile(profile: Dict[str, Any], offerings: Optional[List[Dict[str, Any]]] = None) -> CreativeDirection:
    """Convenience helper for generating creative direction."""
    agent = BusinessUnderstandingAgent()
    return agent.generate_creative_direction(profile, offerings)
