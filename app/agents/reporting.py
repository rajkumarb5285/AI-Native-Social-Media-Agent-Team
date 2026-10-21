from pydantic import Field
from app.agents.base import BaseAgent, AgentInput, AgentOutput, current_time_iso
from app.agents.repurposing import PlatformPost
from app.agents.quality_gate import QualityGateOutput
from app.agents.analytics import AnalyticsOutput

class ReportingInput(AgentInput):
    brand: str
    goal: str
    workflow_id: str
    posts: list[PlatformPost]
    quality_summary: QualityGateOutput
    analytics_plan: AnalyticsOutput

class ReportingOutput(AgentOutput):
    campaign_summary: str
    compliance_verdict: str
    readiness_status: str
    recommended_next_actions: list[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=current_time_iso)

class ReportingAgent(BaseAgent[ReportingInput, ReportingOutput]):
    agent_id = "reporting"
    name = "Reporting Agent"
    department = "Operations"
    description = "Compiles campaign status briefs, governance audits, and continuous optimization recommendations."

    async def execute(self, input_data: ReportingInput) -> ReportingOutput:
        q_pass = input_data.quality_summary.passed
        q_score = input_data.quality_summary.compliance_score
        total_posts = len(input_data.posts)

        verdict = f"Passed with score {q_score}/100" if q_pass else f"Flagged issues (Score: {q_score}/100)"
        readiness = "Ready for human editorial approval" if q_pass else "Requires revisions before approval"

        next_actions = [
            "Human editor must review all platform copy and verify claims",
            "Obtain sign-off via dashboard Approval Gate",
            "Connect platform OAuth credentials if live publishing is desired",
            f"Monitor '{input_data.analytics_plan.primary_kpi}' post-launch"
        ]

        summary = (
            f"Campaign '{input_data.goal}' for {input_data.brand} processed across {total_posts} platforms. "
            f"Quality compliance rating is {q_score}%. All drafts remain safely in internal storage."
        )

        return ReportingOutput(
            success=True,
            campaign_summary=summary,
            compliance_verdict=verdict,
            readiness_status=readiness,
            recommended_next_actions=next_actions,
            metadata={"workflow_id": input_data.workflow_id}
        )
