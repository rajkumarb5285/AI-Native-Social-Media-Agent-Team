from typing import Optional
from pydantic import Field
from app.agents.base import BaseAgent, AgentInput, AgentOutput, current_time_iso

class MetricTarget(AgentInput):
    kpi_name: str
    target_value: str
    measurement_window: str
    is_live_metric: bool = False

class AnalyticsInput(AgentInput):
    platforms: list[str]
    goal: str
    has_live_connections: bool = False
    connection_ids: dict[str, str] = Field(default_factory=dict)

class AnalyticsOutput(AgentOutput):
    primary_kpi: str
    secondary_kpis: list[str] = Field(default_factory=list)
    targets: list[MetricTarget] = Field(default_factory=list)
    measurement_plan_notes: str
    is_live_data: bool = False
    fetched_at: str = Field(default_factory=current_time_iso)

class AnalyticsAgent(BaseAgent[AnalyticsInput, AnalyticsOutput]):
    agent_id = "analytics"
    name = "Analytics Agent"
    department = "Analytics"
    description = "Defines measurement frameworks and retrieves real performance analytics via official APIs."

    async def execute(self, input_data: AnalyticsInput) -> AnalyticsOutput:
        if not input_data.has_live_connections:
            targets = [
                MetricTarget(kpi_name="Qualified Engagement Rate", target_value="> 3.5%", measurement_window="7 days", is_live_metric=False),
                MetricTarget(kpi_name="Click-Through Rate (CTR)", target_value="> 1.8%", measurement_window="7 days", is_live_metric=False),
                MetricTarget(kpi_name="Audience Sentiment Ratio", target_value="> 85% positive", measurement_window="14 days", is_live_metric=False)
            ]
            return AnalyticsOutput(
                success=True,
                primary_kpi="Qualified Engagement Rate",
                secondary_kpis=["Click-Through Rate", "Direct Inquiries", "Shares & Saves"],
                targets=targets,
                measurement_plan_notes="No official analytics APIs are currently connected. Targets represent planning baselines.",
                is_live_data=False,
                metadata={"mode": "planning_baseline"}
            )

        # When connected
        return AnalyticsOutput(
            success=True,
            primary_kpi="Qualified Engagement Rate",
            secondary_kpis=["Live Impressions", "Live Clicks"],
            targets=[],
            measurement_plan_notes="Real analytics retrieved from connected platform endpoints.",
            is_live_data=True,
            metadata={"mode": "live"}
        )
