from typing import Any, Optional
from pydantic import BaseModel, Field

from app.agents.base import current_time_iso
import os
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
    status: str = "completed"
    details: Optional[dict[str, Any]] = None


class WorkflowExecutionResult(BaseModel):
    workflow_id: str
    status: str
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
    """
    Prototype graph runner. Stages are sequential today; explicit failure checks
    stop downstream actions instead of marking a failed stage as success.
    External publishing remains a separate API action that requires approval.
    """

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
            logs.append(WorkflowLogEntry(agent=agent_name, message=message, status=status, details=details))

        def require_success(stage: str, result: Any) -> None:
            if not result.success:
                details = "; ".join(result.errors) if result.errors else "No further details returned."
                log(stage, f"Stage failed: {details}", "failed")
                raise RuntimeError(f"{stage} failed: {details}")

        log("Orchestrator", "Validating campaign brief and creating a plan.", "started")
        orch_res = await self.orchestrator.execute(OrchestratorInput(
            brand=brand, goal=goal, platforms=platforms, audience=audience, tone=tone,
            offer=offer, context=context, approval_required=approval_required, tenant_id=tenant_id
        ))
        require_success("Orchestrator", orch_res)
        log("Orchestrator", f"Validated campaign for {len(orch_res.selected_platforms)} platform(s).", "completed")

        log("BrandMemory", "Loading brand rules and provided context.", "started")
        brand_res = await self.brand_memory.execute(BrandMemoryInput(
            tenant_id=tenant_id, brand=brand, custom_guidelines=context
        ))
        require_success("BrandMemory", brand_res)
        log("BrandMemory", brand_res.retrieved_context_summary, "completed")

        log("MarketRadar", "Retrieving real research sources or explicitly-labelled hypotheses.", "started")
        radar_res = await self.market_radar.execute(MarketRadarInput(
            brand=brand, goal=goal, audience=audience, context=context,
            enable_live_search=live_search_enabled
        ))
        require_success("MarketRadar", radar_res)
        log("MarketRadar", radar_res.hypothesis_summary, "completed",
            {"is_live_search": radar_res.is_live_search, "citation_count": len(radar_res.citations)})

        log("Content Engine", "Generating campaign copy from the research and voice profile.", "started")
        content_res = await self.content_engine.execute(ContentEngineInput(
            brand=brand, goal=goal, tone=tone, audience=audience, offer=offer,
            research_summary=radar_res.hypothesis_summary, voice_profile=brand_res.voice_profile
        ))
        require_success("Content Engine", content_res)
        log("Content Engine", f"Generated headline: {content_res.flagship_headline}",
            "completed", {"generation_mode": content_res.generation_mode})

        log("Repurposing Agent", "Formatting copy for selected platforms.", "started")
        repurp_res = await self.repurposer.execute(RepurposingInput(
            flagship_copy=content_res.flagship_copy,
            headline=content_res.flagship_headline,
            brand=brand,
            call_to_action=content_res.call_to_action,
            platforms=platforms
        ))
        require_success("Repurposing Agent", repurp_res)
        log("Repurposing Agent", f"Created {repurp_res.total_platforms} platform-specific draft(s).", "completed")

        log("Quality Gate", "Checking platform limits and brand safety rules.", "started")
        quality_res = await self.quality_gate.execute(QualityGateInput(
            posts=repurp_res.posts, voice_profile=brand_res.voice_profile
        ))
        require_success("Quality Gate", quality_res)
        log("Quality Gate",
            f"Score {quality_res.compliance_score}/100; passed={quality_res.passed}.",
            "completed" if quality_res.passed else "failed",
            {"blockers": quality_res.blockers, "warnings": quality_res.warnings})

        if not quality_res.passed:
            raise RuntimeError(
                "Quality Gate blocked the workflow; revise the content and re-run before approval. "
                + "; ".join(quality_res.blockers)
            )

        log("Approval Gate", "Waiting for a human decision before external publication.", "waiting")
        approval_res = await self.approval_gate.execute(ApprovalGateInput(
            workflow_id=orch_res.workflow_id, run_id=orch_res.workflow_id,
            required=approval_required, action="request"
        ))
        log("Approval Gate", approval_res.audit_notes,
            "waiting" if approval_res.status == "awaiting_approval" else "completed")

        # This stage only prepares a truthful draft-only summary. The production
        # publisher is app/main.py's authenticated /publish endpoint; no fake IDs.
        pub_res = await self.publishing.execute(PublishingInput(
            posts=repurp_res.posts,
            is_approved=False,
            tenant_id=tenant_id,
            connected_adapters=connected_adapters or {},
            live_publish_requested=False
        ))
        log("Publishing Agent", pub_res.audit_summary, "completed")

        analytics_res = await self.analytics.execute(AnalyticsInput(
            platforms=platforms, goal=goal, has_live_connections=False
        ))
        require_success("Analytics Agent", analytics_res)
        log("Analytics Agent", analytics_res.measurement_plan_notes, "completed")

        report_res = await self.reporting.execute(ReportingInput(
            brand=brand, goal=goal, workflow_id=orch_res.workflow_id,
            posts=repurp_res.posts, quality_summary=quality_res, analytics_plan=analytics_res
        ))
        require_success("Reporting Agent", report_res)
        log("Reporting Agent", f"Report compiled: {report_res.readiness_status}", "completed")

        final_status = "awaiting_approval" if approval_required else "draft_ready"
        return WorkflowExecutionResult(
            workflow_id=orch_res.workflow_id, status=final_status, orchestrator=orch_res,
            brand_memory=brand_res, market_radar=radar_res, content_engine=content_res,
            repurposer=repurp_res, quality_gate=quality_res, approval_gate=approval_res,
            publishing=pub_res, analytics=analytics_res, reporting=report_res, logs=logs
        )
