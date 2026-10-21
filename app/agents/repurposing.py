from pydantic import Field, ConfigDict
from app.agents.base import BaseAgent, AgentInput, AgentOutput

PLATFORM_LIMITS = {
    "LinkedIn": 3000,
    "Twitter": 280,
    "X": 280,
    "Instagram": 2200,
    "Facebook": 5000,
    "YouTube": 1000
}

class PlatformPost(AgentInput):
    model_config = ConfigDict(populate_by_name=True)

    platform: str
    format: str = "post"
    post_copy: str = Field(default="", alias="copy")
    character_count: int
    char_limit: int
    within_limits: bool
    hashtags: list[str] = Field(default_factory=list)
    media_prompt: str = ""
    status: str = "draft"

    @property
    def copy(self) -> str:
        return self.post_copy

class RepurposingInput(AgentInput):
    flagship_copy: str
    headline: str
    brand: str
    call_to_action: str
    platforms: list[str] = Field(default_factory=lambda: ["LinkedIn"])

class RepurposingOutput(AgentOutput):
    posts: list[PlatformPost] = Field(default_factory=list)
    total_platforms: int = 0

class RepurposingAgent(BaseAgent[RepurposingInput, RepurposingOutput]):
    agent_id = "repurposer"
    name = "Repurposing Agent"
    department = "Content"
    description = "Adapts the core message into format-optimized copy adhering to channel length limits."

    async def execute(self, input_data: RepurposingInput) -> RepurposingOutput:
        posts = []
        for plat in input_data.platforms:
            limit = PLATFORM_LIMITS.get(plat, 2000)
            if plat.lower() in ("twitter", "x"):
                copy = f"{input_data.brand}: {input_data.headline[:150]}\n\n{input_data.call_to_action[:80]}"
                hashtags = ["#Tech", f"#{input_data.brand.replace(' ', '')}"]
            elif plat.lower() == "instagram":
                copy = f"{input_data.headline}\n\n{input_data.flagship_copy}\n\n👉 {input_data.call_to_action}\n\nDrop your thoughts below 👇"
                hashtags = ["#BehindTheScenes", "#Growth", f"#{input_data.brand.replace(' ', '')}"]
            else: # LinkedIn, Facebook, default
                copy = f"{input_data.headline}\n\n{input_data.flagship_copy}\n\n{input_data.call_to_action}"
                hashtags = ["#Marketing", "#Innovation", "#Leadership"]

            char_count = len(copy)
            within_limits = char_count <= limit

            posts.append(PlatformPost(
                platform=plat,
                format="social_post",
                copy=copy,
                character_count=char_count,
                char_limit=limit,
                within_limits=within_limits,
                hashtags=hashtags,
                media_prompt=f"High quality editorial banner for {input_data.brand} featuring {plat} layout style.",
                status="draft"
            ))

        return RepurposingOutput(
            success=True,
            posts=posts,
            total_platforms=len(posts)
        )
