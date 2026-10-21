"""Market research stage connected to the configured search adapter."""
from typing import Optional
from pydantic import Field
from app.agents.base import BaseAgent, AgentInput, AgentOutput
from app.services.research.search_service import search_service


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
    description = "Retrieves sourced market evidence and labels hypotheses explicitly."

    async def execute(self, input_data: MarketRadarInput) -> MarketRadarOutput:
        if not input_data.enable_live_search:
            return MarketRadarOutput(
                success=True,
                hypothesis_summary=(
                    f"Context-derived hypothesis for '{input_data.brand}' targeting "
                    f"{input_data.audience}: {input_data.goal}. No live sources were queried."
                ),
                audience_pain_points=[],
                recommended_angles=[
                    "Validate the audience problem with customer interviews",
                    "Use a product demonstration when supported by provided facts",
                    "Test an educational post against a question-led post"
                ],
                citations=[],
                is_live_search=False,
                metadata={"mode": "context_derived", "source_count": 0}
            )

        result = await search_service.search(
            f"market and audience research for {input_data.brand}; "
            f"campaign goal: {input_data.goal}; target audience: {input_data.audience}",
            max_results=5
        )
        citations = [
            ResearchCitation(
                source_title=item.title,
                url=item.url,
                snippet=item.snippet,
                retrieved_at=item.retrieved_at
            )
            for item in result.citations
        ]
        if not result.is_live or not citations:
            return MarketRadarOutput(
                success=False,
                errors=["Live research requested but the provider is unconfigured or returned no usable sources."],
                hypothesis_summary=(
                    "Research blocked: no verified live search results are available. "
                    "Configure TAVILY_API_KEY or select context-only research."
                ),
                audience_pain_points=[],
                recommended_angles=[],
                citations=citations,
                is_live_search=False,
                metadata={"mode": result.source, "source_count": len(citations)}
            )

        source_lines = [
            f"- {item.source_title}: {item.snippet} (source: {item.url})"
            for item in citations
        ]
        return MarketRadarOutput(
            success=True,
            hypothesis_summary=(
                f"Retrieved research for {input_data.brand}. These sources are evidence to evaluate, "
                f"not automatically verified claims:\n" + "\n".join(source_lines)
            ),
            audience_pain_points=[],
            recommended_angles=[
                "Build an educational post using the strongest source-backed finding",
                "Validate market-wide claims against customer interviews before publication"
            ],
            citations=citations,
            is_live_search=True,
            metadata={"mode": result.source, "source_count": len(citations)}
        )
