"""Channel-specific social copy formatting and validation."""
import json
import re
from typing import Optional
from pydantic import Field, ConfigDict
from app.agents.base import BaseAgent, AgentInput, AgentOutput

from app.services.poster_generator import generate_social_poster
from app.services.llm.factory import get_llm_provider
from app.services.llm.base import ChatMessage

PLATFORM_LIMITS = {
    "linkedin": 3000,
    "twitter": 280,
    "x": 280,
    "instagram": 2200,
    "facebook": 5000,
    "youtube": 1000,
    "gmb": 1500,
    "google_business": 1500,
    "google": 1500,
    "google business": 1500,
    "threads": 500,
    "pinterest": 500,
    "tiktok": 2200
}


def canonical_platform(name: str) -> str:
    key = name.strip().lower()
    if key in ("twitter", "x"):
        return "x"
    if key in ("gmb", "google_business", "google", "google business"):
        return "gmb"
    return key


STYLE_GUIDE = {
    "linkedin": "Professional, insight-led. Short paragraphs separated by blank lines. Strong first line. Max 3 hashtags.",
    "x": "Punchy and conversational. One idea. Must be well under the limit. Max 2 hashtags.",
    "instagram": "Warm, visual, emoji-friendly. Hook in the first line. 5-8 relevant hashtags.",
    "facebook": "Friendly and community-minded. End with a question or invitation to comment. 1-3 hashtags.",
    "gmb": "Plain local-business update. Clear offer or news, one call to action. No hashtags, no hype.",
    "youtube": "Community-post style, curious and inviting. 1-3 hashtags.",
    "threads": "Casual, short, conversational. 0-2 hashtags.",
    "pinterest": "Descriptive, keyword-rich, inspiring. 3-5 hashtags.",
    "tiktok": "Energetic caption with a hook. 3-5 hashtags.",
}


def fit_to_limit(text: str, limit: int) -> str:
    """Trim on a sentence/word boundary so a draft never exceeds a platform limit."""
    text = text.strip()
    if len(text) <= limit:
        return text
    cut = text[: max(1, limit - 1)]
    m = max(cut.rfind(". "), cut.rfind("\n"), cut.rfind("! "), cut.rfind("? "))
    if m > limit * 0.5:
        return cut[: m + 1].rstrip()
    sp = cut.rfind(" ")
    if sp > limit * 0.5:
        cut = cut[:sp]
    return cut.rstrip(" ,;:-") + "\u2026"


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
    poster_url: str = ""
    poster_path: str = ""
    published_id: Optional[str] = None
    published_url: Optional[str] = None
    status: str = "draft"
    generation_mode: str = "template"

    @property
    def copy(self) -> str:
        return self.post_copy


class RepurposingInput(AgentInput):
    flagship_copy: str
    headline: str
    brand: str
    call_to_action: str
    tone: str = "visionary"
    platforms: list[str] = Field(default_factory=lambda: ["LinkedIn"])
    goal: str = ""
    audience: str = ""
    banned_words: list[str] = Field(default_factory=list)
    primary_color: Optional[str] = None


class RepurposingOutput(AgentOutput):
    posts: list[PlatformPost] = Field(default_factory=list)
    total_platforms: int = 0


class RepurposingAgent(BaseAgent[RepurposingInput, RepurposingOutput]):
    agent_id = "repurposer"
    name = "Repurposing Agent"
    department = "Content"
    description = "Adapts the approved core message into platform-native posts and enforces channel limits."

    @staticmethod
    def _template(key: str, i: "RepurposingInput") -> tuple[str, list[str]]:
        if key == "x":
            return f"{i.headline}\n\n{i.call_to_action}", []
        if key == "instagram":
            return f"{i.headline}\n\n{i.flagship_copy}\n\n{i.call_to_action}", ["#BehindTheScenes", "#Growth"]
        if key == "gmb":
            return f"{i.headline}\n\n{i.flagship_copy}\n\n\U0001F4CD Visit / Connect with Us Today: {i.call_to_action}", ["#GoogleBusiness", "#LocalFavorite"]
        if key in ("facebook", "youtube"):
            return f"{i.headline}\n\n{i.flagship_copy}\n\n{i.call_to_action}", ["#Spotlight", "#Community"]
        return f"{i.headline}\n\n{i.flagship_copy}\n\n{i.call_to_action}", ["#Marketing", "#Innovation"]

    async def _llm_adapt(self, i: "RepurposingInput", keys: list[str]) -> tuple[dict, dict]:
        """One structured call that writes every platform natively. Returns ({key: (copy, tags)}, usage)."""
        provider = get_llm_provider()
        if provider is None:
            return {}, {}
        spec = [{"platform": k, "char_limit": PLATFORM_LIMITS[k], "style": STYLE_GUIDE.get(k, "Clear and on-brand.")} for k in keys]
        system = (
            "You are a senior social media manager adapting ONE approved campaign message into native posts for each platform. "
            "Rewrite for each platform's culture and format - do not just paste the same text. Stay faithful to the facts in the "
            "approved message; never invent statistics, testimonials, awards, prices or claims. Put hashtags ONLY in the hashtags "
            "array, never inside copy. copy MUST be within char_limit (hashtags are added after). Never use the banned phrases. "
            'Return JSON only: {"posts":[{"platform": string, "copy": string, "hashtags": [string]}]}'
        )
        user = json.dumps({
            "brand": i.brand, "goal": i.goal, "audience": i.audience, "tone": i.tone,
            "approved_headline": i.headline, "approved_message": i.flagship_copy, "call_to_action": i.call_to_action,
            "banned_phrases": i.banned_words, "platforms": spec,
        }, ensure_ascii=False)
        try:
            resp = await provider.generate([ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)], temperature=0.7, json_mode=True)
            obj = resp.parsed_json or json.loads(resp.content)
            out = {}
            for item in obj.get("posts", []):
                k = canonical_platform(str(item.get("platform", "")))
                copy = str(item.get("copy", "")).strip()
                if k in keys and copy:
                    tags = [("#" + t.lstrip("#").replace(" ", "")) for t in item.get("hashtags", []) if str(t).strip()][:10]
                    out[k] = (copy, tags)
            return out, {"model": resp.model, "latency": resp.latency_seconds, "cost": resp.usage.estimated_cost_usd, "tokens": resp.usage.total_tokens}
        except Exception as exc:
            return {}, {"error": f"{type(exc).__name__}: {exc}"}

    async def execute(self, input_data: RepurposingInput) -> RepurposingOutput:
        errors, requested = [], []
        for requested_name in input_data.platforms:
            platform = requested_name.strip()
            key = canonical_platform(platform)
            if key not in PLATFORM_LIMITS:
                errors.append(f"Unsupported publishing platform '{platform}'.")
                continue
            requested.append((platform, key))

        adapted, usage = await self._llm_adapt(input_data, [k for _, k in requested]) if requested else ({}, {})

        posts = []
        for platform, key in requested:
            limit = PLATFORM_LIMITS[key]
            mode = "llm" if key in adapted else "template"
            copy, hashtags = adapted[key] if key in adapted else self._template(key, input_data)
            copy = fit_to_limit(copy, limit)
            count = len(copy)
            media_prompt = (
                f"Create an on-brand campaign visual for {input_data.brand}. "
                f"Channel: {platform}. Message: {input_data.headline}. "
                "Do not render fake logos, statistics, or unapproved text."
            )
            poster_url = poster_path = ""
            try:
                poster_style = "gmb_local" if key == "gmb" else getattr(input_data, "tone", "visionary")
                poster_url, poster_path = generate_social_poster(
                    brand=input_data.brand, headline=input_data.headline, platform=platform,
                    tone=getattr(input_data, "tone", "visionary"), style=poster_style,
                    call_to_action=input_data.call_to_action,
                    brand_color=getattr(input_data, "primary_color", None),
                )
            except Exception:
                pass
            posts.append(PlatformPost(
                platform=platform, format="social_post", copy=copy, character_count=count, char_limit=limit,
                within_limits=count <= limit, hashtags=hashtags, media_prompt=media_prompt,
                poster_url=poster_url, poster_path=poster_path, status="draft", generation_mode=mode,
            ))
        meta = {"supported_platforms": sorted(PLATFORM_LIMITS.keys()), "llm_platforms": sorted(adapted.keys())}
        if usage:
            meta["llm_usage"] = usage
        return RepurposingOutput(success=len(errors) == 0, errors=errors, posts=posts, total_platforms=len(posts), metadata=meta)
