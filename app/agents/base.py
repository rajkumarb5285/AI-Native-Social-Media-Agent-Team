import abc
import datetime
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

def current_time_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

class AgentInput(BaseModel):
    pass

class AgentOutput(BaseModel):
    success: bool = True
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

TInput = TypeVar("TInput", bound=AgentInput)
TOutput = TypeVar("TOutput", bound=AgentOutput)

class BaseAgent(abc.ABC, Generic[TInput, TOutput]):
    agent_id: str
    name: str
    department: str
    description: str

    def __init__(self):
        if not hasattr(self, "agent_id") or not self.agent_id:
            raise ValueError(f"Agent class {self.__class__.__name__} must define agent_id")

    @abc.abstractmethod
    async def execute(self, input_data: TInput) -> TOutput:
        """Executes the agent logic with defined input schema and returns typed output schema."""
        pass

    def get_metadata(self) -> dict[str, str]:
        return {
            "id": self.agent_id,
            "name": self.name,
            "department": self.department,
            "description": self.description
        }
