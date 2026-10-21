import abc
from typing import Optional, Any
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str # "system", "user", "assistant"
    content: str

class LLMUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0

class LLMResponse(BaseModel):
    content: str
    parsed_json: Optional[dict[str, Any]] = None
    model: str
    usage: LLMUsage = Field(default_factory=LLMUsage)
    latency_seconds: float = 0.0

class BaseLLMProvider(abc.ABC):
    @abc.abstractmethod
    async def generate(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        json_mode: bool = False
    ) -> LLMResponse:
        """Executes chat completion with retry, timeout, and token usage accounting."""
        pass
