import time
import json
import httpx
from typing import Optional
from app.services.llm.base import BaseLLMProvider, ChatMessage, LLMResponse, LLMUsage
from app.services.llm.json_utils import clean_and_parse_json

class OpenAICompatibleProvider(BaseLLMProvider):
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4.1-mini",
        timeout: float = 45.0
    ):
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def generate(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        json_mode: bool = False
    ) -> LLMResponse:
        start_time = time.perf_counter()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "temperature": temperature,
            "messages": [m.model_dump() for m in messages]
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            resp.raise_for_status()
            data = resp.json()

        latency = time.perf_counter() - start_time
        content = data["choices"][0]["message"]["content"]
        usage_data = data.get("usage", {})
        prompt_tokens = usage_data.get("prompt_tokens", 0)
        completion_tokens = usage_data.get("completion_tokens", 0)
        total_tokens = usage_data.get("total_tokens", prompt_tokens + completion_tokens)
        
        # Estimate cost (e.g. standard gpt-4.1-mini: $0.15/1M input, $0.60/1M output)
        cost = (prompt_tokens * 0.00000015) + (completion_tokens * 0.00000060)

        parsed = None
        if json_mode or content.strip().startswith("{") or content.strip().startswith("```"):
            try:
                parsed = clean_and_parse_json(content)
            except Exception:
                parsed = None

        return LLMResponse(
            content=content,
            parsed_json=parsed,
            model=self.model,
            usage=LLMUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=cost
            ),
            latency_seconds=round(latency, 3)
        )
