from typing import Optional
from pydantic import Field
from app.agents.base import BaseAgent, AgentInput, AgentOutput
from app.agents.brand_memory import BrandVoiceProfile

class ContentEngineInput(AgentInput):
    brand: str
    goal: str
    tone: str
    audience: str
    offer: Optional[str] = ""
    research_summary: str = ""
    voice_profile: Optional[BrandVoiceProfile] = None

class ContentEngineOutput(AgentOutput):
    flagship_headline: str
    flagship_copy: str
    call_to_action: str
    key_takeaways: list[str] = Field(default_factory=list)
    suggested_hashtags: list[str] = Field(default_factory=list)

class ContentEngineAgent(BaseAgent[ContentEngineInput, ContentEngineOutput]):
    agent_id = "content-engine"
    name = "Content Engine"
    department = "Content"
    description = "Drafts authoritative flagship messaging and campaign narratives."

    async def execute(self, input_data: ContentEngineInput) -> ContentEngineOutput:
        brand = input_data.brand
        goal = input_data.goal
        offer_str = f" {input_data.offer}." if input_data.offer else ""
        headline = f"How {brand} is solving: {goal}"
        
        copy = (
            f"{headline}\n\n"
            f"For {input_data.audience}: achieving {goal.lower()} shouldn't require compromising on quality or clarity.\n\n"
            f"Here is our fresh approach:{offer_str}\n"
            f"1. Cut out unnecessary overhead.\n"
            f"2. Focus strictly on measurable impact.\n"
            f"3. Maintain full transparency from day one.\n\n"
            f"What has been your biggest hurdle when tackling this?"
        )
        
        cta = input_data.offer if input_data.offer else f"Discover how {brand} can accelerate your workflow today."
        hashtags = ["#Innovation", "#Productivity", f"#{brand.replace(' ', '')}"]

        return ContentEngineOutput(
            success=True,
            flagship_headline=headline,
            flagship_copy=copy,
            call_to_action=cta,
            key_takeaways=["Measurable impact", "Complete transparency", "Direct audience engagement"],
            suggested_hashtags=hashtags,
            metadata={"tone": input_data.tone}
        )
