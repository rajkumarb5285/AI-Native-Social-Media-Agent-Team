from typing import Optional
from pydantic import Field
from app.agents.base import BaseAgent, AgentInput, AgentOutput, current_time_iso

class OrchestratorInput(AgentInput):
    brand: str = Field(min_length=1, max_length=120)
    goal: str = Field(min_length=1, max_length=600)
    platforms: list[str] = Field(min_length=1, max_length=6)
    audience: str = Field(default="general audience", max_length=300)
    tone: str = Field(default="clear and helpful", max_length=120)
    offer: Optional[str] = Field(default="", max_length=400)
    context: Optional[str] = Field(default="", max_length=4000)
    approval_required: bool = True
    tenant_id: str = "default"

class ExecutionStep(AgentInput):
    agent_id: str
    step_name: str
    status: str = "pending"
    description: str

class OrchestratorOutput(AgentOutput):
    workflow_id: str
    plan: list[ExecutionStep] = Field(default_factory=list)
    selected_platforms: list[str] = Field(default_factory=list)
    approval_required: bool = True
    created_at: str = Field(default_factory=current_time_iso)

class OrchestratorAgent(BaseAgent[OrchestratorInput, OrchestratorOutput]):
    agent_id = "orchestrator"
    name = "Orchestrator"
    department = "Operations"
    description = "Validates incoming campaign briefs and coordinates multi-agent execution pipeline."

    async def execute(self, input_data: OrchestratorInput) -> OrchestratorOutput:
        errors = []
        if not input_data.brand.strip():
            errors.append("Brand cannot be empty or blank.")
        if not input_data.goal.strip():
            errors.append("Goal cannot be empty or blank.")
        if not input_data.platforms:
            errors.append("At least one target platform must be specified.")

        if errors:
            return OrchestratorOutput(
                success=False,
                errors=errors,
                workflow_id="",
                selected_platforms=input_data.platforms,
                approval_required=input_data.approval_required
            )

        import uuid
        wf_id = f"wf-{uuid.uuid4().hex[:12]}"
        plan = [
            ExecutionStep(agent_id="brand-memory", step_name="Brand Context Retrieval", description="Retrieve guidelines and past high-performing patterns."),
            ExecutionStep(agent_id="market-radar", step_name="Market Research Synthesis", description="Formulate audience insights and content hooks."),
            ExecutionStep(agent_id="content-engine", step_name="Core Content Generation", description="Generate cornerstone message draft."),
            ExecutionStep(agent_id="repurposer", step_name="Multi-Platform Repurposing", description="Format draft for target platforms."),
            ExecutionStep(agent_id="quality-gate", step_name="Compliance & Policy Check", description="Verify tone, limits, and claim validity."),
            ExecutionStep(agent_id="approval-gate", step_name="Human Review Gate", description="Block publishing until authorized human signs off."),
            ExecutionStep(agent_id="publishing", step_name="Platform Dispatch", description="Dispatch approved copy to verified adapters."),
            ExecutionStep(agent_id="analytics", step_name="Measurement Planning", description="Set up KPI tracking and baseline targets."),
            ExecutionStep(agent_id="reporting", step_name="Summary & Learning", description="Compile execution brief and continuous learnings.")
        ]

        return OrchestratorOutput(
            success=True,
            workflow_id=wf_id,
            plan=plan,
            selected_platforms=input_data.platforms,
            approval_required=input_data.approval_required,
            metadata={"tenant_id": input_data.tenant_id, "brand": input_data.brand}
        )
