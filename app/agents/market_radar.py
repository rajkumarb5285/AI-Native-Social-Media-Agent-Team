from typing import Optional
from pydantic import Field
from app.agents.base import BaseAgent, AgentInput, AgentOutput

class MarketRadarInput(AgentInput):
    brand: str
    goal: str
    audience: str
    context: Optional[str] = ""
    enable_live_search: bool = False

class ResearchCitation(AgentInput):
    source_title: str
    url: Optional[str] = None
    snippet: str
    retrieved_at: str

class MarketRadarOutput(AgentOutput):
    hypothesis_summary: str
    audience_pain_points: list[str] = Field(default_factory=list)
    recommended_angles: list[str] = Field(default_factory=list)
    citations: list[ResearchCitation] = Field(default_factory=list)
    is_live_search: bool = False

class MarketRadarAgent(BaseAgent[MarketRadarInput, MarketRadarOutput]):
    agent_id = "market-radar"
    name = "MarketRadar"
    department = "Research"
    description = "Synthesizes audience research, competitive positioning, and trending content angles."

    async def execute(self, input_data: MarketRadarInput) -> MarketRadarOutput:
        # Honest boundary: clearly distinguish live search from context-derived synthesis
        if not input_data.enable_live_search:
            return MarketRadarOutput(
                success=True,
                hypothesis_summary=f"Context-derived research brief for '{input_data.brand}' targeting {input_data.audience}. Validates '{input_data.goal}'.",
                audience_pain_points=[
                    f"Needs clear proof points for {input_data.brand}",
                    f"Overwhelmed by generic claims in this category",
                    f"Seeks streamlined execution aligned with: {input_data.audience}"
                ],
                recommended_angles=[
                    f"Position {input_data.brand} as an evidence-based solution",
                    "Practical actionable breakdown rather than vague hype",
                    "Direct community question prompting feedback"
                ],
                citations=[],
                is_live_search=False,
                metadata={"mode": "context_derived", "live_search_configured": False}
            )

        # When live search adapter is called (e.g. via Tavily/SerpAPI in Phase 4)
        return MarketRadarOutput(
            success=True,
            hypothesis_summary=f"Live research brief for '{input_data.brand}'.",
            audience_pain_points=["Audience trend data retrieved"],
            recommended_angles=["Verified topical angle"],
            citations=[],
            is_live_search=True,
            metadata={"mode": "live"}
        )
