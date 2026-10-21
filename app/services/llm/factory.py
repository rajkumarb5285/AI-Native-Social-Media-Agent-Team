import os
from typing import Optional
from app.services.llm.base import BaseLLMProvider
from app.services.llm.openai_provider import OpenAICompatibleProvider

def get_llm_provider() -> Optional[BaseLLMProvider]:
    # Re-read configuration so runtime-loaded secrets or test overrides are honored.
    api_key = os.getenv("LLM_API_KEY", "").strip()
    if not api_key:
        return None
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("LLM_MODEL", "gpt-4.1-mini")
    timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "45"))
    return OpenAICompatibleProvider(
        api_key=api_key,
        base_url=base_url,
        model=model,
        timeout=timeout
    )
