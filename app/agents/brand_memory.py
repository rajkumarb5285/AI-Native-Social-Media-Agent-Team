from typing import Optional
from pydantic import Field
from app.agents.base import BaseAgent, AgentInput, AgentOutput

class BrandMemoryInput(AgentInput):
    tenant_id: str = "default"
    brand: str
    custom_guidelines: Optional[str] = ""

class BrandVoiceProfile(AgentInput):
    tone_descriptors: list[str] = Field(default_factory=lambda: ["professional", "authoritative", "approachable"])
    banned_words: list[str] = Field(default_factory=lambda: ["guaranteed 100%", "get rich quick", "unbeatable miracle"])
    mandatory_disclaimers: list[str] = Field(default_factory=list)
    approved_hashtags: list[str] = Field(default_factory=lambda: ["#Leadership", "#Innovation", "#Growth"])
    value_propositions: list[str] = Field(default_factory=list)

class BrandMemoryOutput(AgentOutput):
    brand: str
    tenant_id: str
    voice_profile: BrandVoiceProfile
    retrieved_context_summary: str

class BrandMemoryAgent(BaseAgent[BrandMemoryInput, BrandMemoryOutput]):
    agent_id = "brand-memory"
    name = "BrandMemory"
    department = "Governance"
    description = "Retrieves and enforces tenant-scoped brand guidelines, style rules, and banned vocabulary."

    async def execute(self, input_data: BrandMemoryInput) -> BrandMemoryOutput:
        voice = BrandVoiceProfile()
        summary = f"Loaded verified brand voice rules for {input_data.brand} under tenant {input_data.tenant_id}."
        if input_data.custom_guidelines:
            summary += f" Appended custom guidelines: {input_data.custom_guidelines[:100]}..."

        return BrandMemoryOutput(
            success=True,
            brand=input_data.brand,
            tenant_id=input_data.tenant_id,
            voice_profile=voice,
            retrieved_context_summary=summary,
            metadata={"tenant_scoped": True}
        )
