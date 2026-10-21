from typing import Any, Optional
from pydantic import BaseModel, Field

from app.agents.base import current_time_iso
from app.agents.orchestrator import OrchestratorAgent, OrchestratorInput, OrchestratorOutput
from app.agents.brand_memory import BrandMemoryAgent, BrandMemoryInput, BrandMemoryOutput
from app.agents.market_radar import MarketRadarAgent, MarketRadarInput, MarketRadarOutput
from app.agents.content_engine import ContentEngineAgent, ContentEngineInput, ContentEngineOutput
from app.agents.repurposing import RepurposingAgent, RepurposingInput, RepurposingOutput
from app.agents.quality_gate import QualityGateAgent, QualityGateInput, QualityGateOutput
from app.agents.approval_gate import ApprovalGateAgent, ApprovalGateInput, ApprovalGateOutput
from app.agents.publishing import PublishingAgent, PublishingInput, PublishingOutput
from app.agents.analytics import AnalyticsAgent, AnalyticsInput, AnalyticsOutput
from app.agents.reporting import ReportingAgent, ReportingInput, ReportingOutput

class WorkflowLogEntry(BaseModel):
    time: str = Field(default_factory=current_time_iso)
    agent: str
    message: str
    status: str = "completed" # "started", "completed", "failed", "waiting"
    details: Optional[dict[str, Any]] = None

class WorkflowExecutionResult(BaseModel):
    workflow_id: str
    status: str # "awaiting_approval", "draft_ready", "approved", "failed"
    orchestrator: OrchestratorOutput
    brand_memory: BrandMemoryOutput
    market_radar: MarketRadarOutput
    content_engine: ContentEngineOutput
    repurposer: RepurposingOutput
    quality_gate: QualityGateOutput
    approval_gate: ApprovalGateOutput
    publishing: PublishingOutput
    analytics: AnalyticsOutput
    reporting: ReportingOutput
    logs: list[WorkflowLogEntry] = Field(default_factory=list)

class AgentGraph:
    """Orchestrates the 10 specialist agents in a typed, traceable pipeline."""

    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.brand_memory = BrandMemoryAgent()
        self.market_radar = MarketRadarAgent()
        self.content_engine = ContentEngineAgent()
        self.repurposer = RepurposingAgent()
        self.quality_gate = QualityGateAgent()
        self.approval_gate = ApprovalGateAgent()
        self.publishing = PublishingAgent()
        self.analytics = AnalyticsAgent()
        self.reporting = ReportingAgent()

    async def run(
        self,
        brand: str,
        goal: str,
        platforms: list[str],
        audience: str = "general audience",
        tone: str = "clear and helpful",
        offer: str = "",
        context: str = "",
        approval_required: bool = True,
        tenant_id: str = "default",
        live_search_enabled: bool = False,
        connected_adapters: Optional[dict[str, bool]] = None
    ) -> WorkflowExecutionResult:
        logs: list[WorkflowLogEntry] = []

        def log(agent_name: str, message: str, status: str = "completed", details: Optional[dict[str, Any]] = None):
            logs.append(WorkflowLogEntry(
                agent=agent_name,
                message=message,
                status=status,
                details=details
            ))

        # 1. Orchestrator
        log("Orchestrator", "Initializing workflow execution graph.", "started")
        orch_res = await self.orchestrator.execute(OrchestratorInput(
            brand=brand,
            goal=goal,
            platforms=platforms,
            audience=audience,
            tone=tone,
            offer=offer,
            context=context,
            approval_required=approval_required,
            tenant_id=tenant_id
        ))
        if not orch_res.success:
            log("Orchestrator", f"Validation failed: {', '.join(orch_res.errors)}", "failed")
            raise ValueError(f"Orchestrator validation failed: {orch_res.errors}")
        log("Orchestrator", f"Plan generated for {len(orch_res.selected_platforms)} platforms. Workflow ID: {orch_res.workflow_id}", "completed")

        # 2. BrandMemory
        log("BrandMemory", "Retrieving brand voice and compliance guidelines.", "started")
        brand_res = await self.brand_memory.execute(BrandMemoryInput(
            tenant_id=tenant_id,
            brand=brand,
            custom_guidelines=context
        ))
        log("BrandMemory", brand_res.retrieved_context_summary, "completed")

        # 3. MarketRadar
        log("MarketRadar", "Synthesizing market research hypotheses and audience angles.", "started")
        radar_res = await self.market_radar.execute(MarketRadarInput(
            brand=brand,
            goal=goal,
            audience=audience,
            context=context,
            enable_live_search=live_search_enabled
        ))
        log("MarketRadar", radar_res.hypothesis_summary, "completed")

        # 4. ContentEngine
        log("Content Engine", "Generating flagship campaign narrative.", "started")
        content_res = await self.content_engine.execute(ContentEngineInput(
            brand=brand,
            goal=goal,
            tone=tone,
            audience=audience,
            offer=offer,
            research_summary=radar_res.hypothesis_summary,
            voice_profile=brand_res.voice_profile
        ))
        log("Content Engine", f"Drafted core message: '{content_res.flagship_headline}'", "completed")

        # 5. RepurposingAgent
        log("Repurposing Agent", "Adapting copy to target platform constraints.", "started")
        repurp_res = await self.repurposer.execute(RepurposingInput(
            flagship_copy=content_res.flagship_copy,
            headline=content_res.flagship_headline,
            brand=brand,
            call_to_action=content_res.call_to_action,
            platforms=platforms
        ))
        log("Repurposing Agent", f"Formatted {repurp_res.total_platforms} platform-specific draft posts.", "completed")

        # 6. QualityGate
        log("Quality Gate", "Validating compliance, character limits, and prohibited words.", "started")
        quality_res = await self.quality_gate.execute(QualityGateInput(
            posts=repurp_res.posts,
            voice_profile=brand_res.voice_profile
        ))
        q_status = "completed" if quality_res.passed else "failed"
        log("Quality Gate", f"Compliance score: {quality_res.compliance_score}/100. Checks passed: {quality_res.passed}", q_status)

        # 7. ApprovalGate
        log("Approval Gate", "Evaluating approval requirement.", "started")
        approval_res = await self.approval_gate.execute(ApprovalGateInput(
            workflow_id=orch_res.workflow_id,
            run_id=orch_res.workflow_id,
            required=approval_required,
            action="request"
        ))
        log("Approval Gate", approval_res.audit_notes, "waiting" if approval_res.status == "awaiting_approval" else "completed")

        # 8. PublishingAgent
        log("Publishing Agent", "Checking publishing authorization and adapters.", "started")
        is_approved = (approval_res.status == "approved" or approval_res.status == "bypassed")
        pub_res = await self.publishing.execute(PublishingInput(
            posts=repurp_res.posts,
            is_approved=is_approved,
            tenant_id=tenant_id,
            connected_adapters=connected_adapters or {},
            live_publish_requested=False
        ))
        log("Publishing Agent", pub_res.audit_summary, "completed")

        # 9. AnalyticsAgent
        log("Analytics Agent", "Formulating measurement framework and KPI targets.", "started")
        analytics_res = await self.analytics.execute(AnalyticsInput(
            platforms=platforms,
            goal=goal,
            has_live_connections=False
        ))
        log("Analytics Agent", f"Primary KPI: {analytics_res.primary_kpi} ({analytics_res.measurement_plan_notes})", "completed")

        # 10. ReportingAgent
        log("Reporting Agent", "Compiling final campaign audit and recommendation report.", "started")
        report_res = await self.reporting.execute(ReportingInput(
            brand=brand,
            goal=goal,
            workflow_id=orch_res.workflow_id,
            posts=repurp_res.posts,
            quality_summary=quality_res,
            analytics_plan=analytics_res
        ))
        log("Reporting Agent", f"Report compiled: {report_res.readiness_status}", "completed")

        final_status = "awaiting_approval" if approval_required else "draft_ready"

        return WorkflowExecutionResult(
            workflow_id=orch_res.workflow_id,
            status=final_status,
            orchestrator=orch_res,
            brand_memory=brand_res,
            market_radar=radar_res,
            content_engine=content_res,
            repurposer=repurp_res,
            quality_gate=quality_res,
            approval_gate=approval_res,
            publishing=pub_res,
            analytics=analytics_res,
            reporting=report_res,
            logs=logs
        )
