"""LLM-backed content generation with a clearly-labelled template fallback."""
import json
from typing import Optional
from pydantic import Field
from app.agents.base import BaseAgent, AgentInput, AgentOutput
from app.agents.brand_memory import BrandVoiceProfile
from app.services.llm.factory import get_llm_provider
from app.services.llm.base import ChatMessage


class ContentEngineInput(AgentInput):
    brand: str
    goal: str
    tone: str
    audience: str
    offer: Optional[str] = ""
    research_summary: str = ""
    voice_profile: Optional[BrandVoiceProfile] = None
    platform: str = "LinkedIn"
    source_facts: list[str] = Field(default_factory=list)


class ContentEngineOutput(AgentOutput):
    flagship_headline: str
    flagship_copy: str
    call_to_action: str
    key_takeaways: list[str] = Field(default_factory=list)
    suggested_hashtags: list[str] = Field(default_factory=list)
    generation_mode: str = "template_fallback"


class ContentEngineAgent(BaseAgent[ContentEngineInput, ContentEngineOutput]):
    agent_id = "content-engine"
    name = "Content Engine"
    department = "Content"
    description = "Creates structured channel-specific copy grounded in available evidence."

    async def execute(self, input_data: ContentEngineInput) -> ContentEngineOutput:
        provider = get_llm_provider()
        brand = input_data.brand.strip()
        goal = input_data.goal.strip()
        voice = input_data.voice_profile.model_dump() if input_data.voice_profile else {}
        facts = [item.strip() for item in input_data.source_facts if item.strip()]
        offer_value = (input_data.offer or "").strip()
        if offer_value:
            facts.append(f"Offer supplied by the user: {offer_value}")

        if provider is not None:
            system = (
                "You are a senior marketing creative strategist. Create specific, original and useful copy, "
                "not generic filler. Never invent statistics, testimonials, awards, customer results, "
                "or competitor claims. Use only supported facts. If evidence is missing, use a clearly "
                "labelled hypothesis or avoid the claim. Follow the requested brand voice and platform. "
                "Return valid JSON only."
            )
            payload = {
                "brand": brand,
                "goal": goal,
                "audience": input_data.audience,
                "tone": input_data.tone,
                "offer": offer_value,
                "platform": input_data.platform,
                "research_summary": input_data.research_summary,
                "brand_voice": voice,
                "source_facts": facts,
                "output_schema": {
                    "headline": "string",
                    "copy": "string",
                    "call_to_action": "string",
                    "key_takeaways": ["string"],
                    "hashtags": ["string"]
                }
            }
            try:
                response = await provider.generate(
                    [
                        ChatMessage(role="system", content=system),
                        ChatMessage(role="user", content=json.dumps(payload, ensure_ascii=False))
                    ],
                    temperature=0.7,
                    json_mode=True
                )
                obj = response.parsed_json or json.loads(response.content)
                headline = str(obj["headline"]).strip()
                copy = str(obj["copy"]).strip()
                cta = str(obj["call_to_action"]).strip()
                if not headline or not copy or not cta:
                    raise ValueError("LLM response contains an empty required field.")
                return ContentEngineOutput(
                    success=True,
                    flagship_headline=headline,
                    flagship_copy=copy,
                    call_to_action=cta,
                    key_takeaways=[str(v) for v in obj.get("key_takeaways", [])][:8],
                    suggested_hashtags=[str(v) for v in obj.get("hashtags", [])][:15],
                    generation_mode="llm",
                    metadata={
                        "provider_model": response.model,
                        "latency_seconds": response.latency_seconds,
                        "estimated_cost_usd": response.usage.estimated_cost_usd
                    }
                )
            except Exception as exc:
                # Fall back to template generation if LLM provider is unavailable or rate-limited
                pass

        headline = f"{brand}: {goal}"
        copy = (
            f"{headline}\n\n"
            f"For {input_data.audience}, start by identifying one clear customer problem, "
            f"showing a concrete example, and explaining the next useful step.\n\n"
            f"Research context (not independently verified): {input_data.research_summary[:500]}"
        )
        cta = offer_value or f"What would help you achieve this goal with {brand}?"
        return ContentEngineOutput(
            success=True,
            flagship_headline=headline,
            flagship_copy=copy,
            call_to_action=cta,
            key_takeaways=[
                "State the customer's problem",
                "Use an evidence-backed example",
                "Offer a specific next step"
            ],
            suggested_hashtags=[],
            generation_mode="template_fallback",
            metadata={"warning": "Template fallback used; configure LLM_API_KEY to enable model-generated copy."}
        )
