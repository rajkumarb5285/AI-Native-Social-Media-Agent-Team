"""Channel-specific social copy formatting and validation."""
from pydantic import Field, ConfigDict
from app.agents.base import BaseAgent, AgentInput, AgentOutput

PLATFORM_LIMITS = {
    "linkedin": 3000,
    "twitter": 280,
    "x": 280,
    "instagram": 2200,
    "facebook": 5000,
    "youtube": 1000
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
    description = "Formats campaign copy for supported channel limits and marks unsupported channels."

    async def execute(self, input_data: RepurposingInput) -> RepurposingOutput:
        posts = []
        errors = []
        for requested in input_data.platforms:
            platform = requested.strip()
            key = platform.lower()
            if key not in PLATFORM_LIMITS:
                errors.append(f"Unsupported publishing platform '{platform}'.")
                continue
            limit = PLATFORM_LIMITS[key]
            if key in ("twitter", "x"):
                copy = f"{input_data.headline}\n\n{input_data.call_to_action}"
                hashtags = []
            elif key == "instagram":
                copy = f"{input_data.headline}\n\n{input_data.flagship_copy}\n\n{input_data.call_to_action}"
                hashtags = ["#BehindTheScenes", "#Growth"]
            else:
                copy = f"{input_data.headline}\n\n{input_data.flagship_copy}\n\n{input_data.call_to_action}"
                hashtags = ["#Marketing", "#Innovation"]
            count = len(copy)
            media_prompt = (
                f"Create an on-brand campaign visual for {input_data.brand}. "
                f"Channel: {platform}. Message: {input_data.headline}. "
                "Do not render fake logos, statistics, or unapproved text."
            )
            posts.append(PlatformPost(
                platform=platform,
                format="social_post",
                copy=copy,
                character_count=count,
                char_limit=limit,
                within_limits=count <= limit,
                hashtags=hashtags,
                media_prompt=media_prompt,
                status="draft"
            ))
        return RepurposingOutput(
            success=len(errors) == 0,
            errors=errors,
            posts=posts,
            total_platforms=len(posts),
            metadata={"supported_platforms": sorted(PLATFORM_LIMITS.keys())}
        )
