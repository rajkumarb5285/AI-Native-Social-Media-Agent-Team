import time
from typing import Any, Awaitable, Callable, Optional
from pydantic import BaseModel, Field

from app.agents.base import current_time_iso
from app.services.llm.factory import get_llm_provider
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


class RunCancelled(Exception):
    """Raised by an event callback to stop the pipeline between stages."""


class WorkflowLogEntry(BaseModel):
    time: str = Field(default_factory=current_time_iso)
    agent: str
    message: str
    status: str = "completed"
    details: Optional[dict[str, Any]] = None


EventCallback = Callable[[WorkflowLogEntry], Awaitable[None]]


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
    revisions_used: int = 0
    cost_summary: dict[str, Any] = Field(default_factory=dict)


class AgentGraph:
    """Sequential specialist pipeline that reports progress as it happens.

    * `on_event` is awaited for EVERY log entry the moment it is produced, so a caller can persist it and
      push it to the browser live. (Before, logs were collected in a local list and only returned once the
      whole run had finished - nothing could stream.)
    * The callback may raise RunCancelled to stop between stages.
    * If the Quality Gate rejects the draft and an LLM is configured, the team revises the copy with the
      reviewer's feedback (up to `revision_limit` times) instead of failing the whole run.
    * External publishing remains a separate, approval-gated API action.
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

    @staticmethod
    def _usage_of(*outputs) -> dict[str, Any]:
        calls, cost, tokens, models = 0, 0.0, 0, set()
        for out in outputs:
            md = getattr(out, "metadata", {}) or {}
            u = md.get("llm_usage")
            if u:
                calls += 1; cost += float(u.get("cost", 0) or 0); tokens += int(u.get("tokens", 0) or 0)
                if u.get("model"): models.add(u["model"])
            elif md.get("provider_model"):
                calls += 1; cost += float(md.get("estimated_cost_usd", 0) or 0)
                models.add(md["provider_model"])
        return {"llm_calls": calls, "estimated_cost_usd": round(cost, 6), "tokens": tokens, "models": sorted(models)}

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
        connected_adapters: Optional[dict[str, bool]] = None,
        business_profile: Optional[dict[str, Any]] = None,
        primary_color: Optional[str] = None,
        on_event: Optional[EventCallback] = None,
        revision_limit: int = 2,
    ) -> WorkflowExecutionResult:
        logs: list[WorkflowLogEntry] = []
        clocks: dict[str, float] = {}

        async def log(agent_name: str, message: str, status: str = "completed", details: Optional[dict[str, Any]] = None):
            if status == "started":
                clocks[agent_name] = time.perf_counter()
            elif agent_name in clocks and status in ("completed", "failed", "waiting"):
                details = {**(details or {}), "duration_ms": int((time.perf_counter() - clocks.pop(agent_name)) * 1000)}
            entry = WorkflowLogEntry(agent=agent_name, message=message, status=status, details=details)
            logs.append(entry)
            if on_event is not None:
                await on_event(entry)

        async def require_success(stage: str, result: Any) -> None:
            if not result.success:
                details = "; ".join(result.errors) if result.errors else "No further details returned."
                await log(stage, f"Stage failed: {details}", "failed")
                raise RuntimeError(f"{stage} failed: {details}")

        await log("Orchestrator", "Validating campaign brief and creating a plan.", "started")
        orch_res = await self.orchestrator.execute(OrchestratorInput(
            brand=brand, goal=goal, platforms=platforms, audience=audience, tone=tone,
            offer=offer, context=context, approval_required=approval_required, tenant_id=tenant_id
        ))
        await require_success("Orchestrator", orch_res)
        await log("Orchestrator", f"Validated campaign for {len(orch_res.selected_platforms)} platform(s).", "completed",
                  {"platforms": orch_res.selected_platforms})

        await log("BrandMemory", "Loading brand rules and your saved business profile.", "started")
        brand_res = await self.brand_memory.execute(BrandMemoryInput(
            tenant_id=tenant_id, brand=brand, custom_guidelines=context, business_profile=business_profile or {}
        ))
        await require_success("BrandMemory", brand_res)
        await log("BrandMemory", brand_res.retrieved_context_summary, "completed")

        await log("MarketRadar", "Researching the audience and angles.", "started")
        radar_res = await self.market_radar.execute(MarketRadarInput(
            brand=brand, goal=goal, audience=audience, context=context,
            enable_live_search=(live_search_enabled or os.getenv("ENABLE_LIVE_SEARCH", "false").lower() == "true")
        ))
        await require_success("MarketRadar", radar_res)
        await log("MarketRadar", radar_res.hypothesis_summary[:300], "completed",
                  {"is_live_search": radar_res.is_live_search, "citation_count": len(radar_res.citations),
                   "mode": radar_res.metadata.get("mode")})

        facts = {k: v for k, v in (business_profile or {}).items() if k in ("business_name", "category", "tagline", "website") and v}
        feedback: list[str] = []
        revisions_used = 0
        llm_available = get_llm_provider() is not None
        content_res = repurp_res = quality_res = None

        for attempt in range(revision_limit + 1):
            label = "Content Engine" if attempt == 0 else f"Content Engine (revision {attempt})"
            await log("Content Engine", "Writing the flagship message from research and brand voice." if attempt == 0
                      else f"Revising the draft using reviewer feedback (attempt {attempt}/{revision_limit}).", "started")
            content_res = await self.content_engine.execute(ContentEngineInput(
                brand=brand, goal=goal, tone=tone, audience=audience, offer=offer,
                research_summary=radar_res.hypothesis_summary, voice_profile=brand_res.voice_profile,
                business_facts=facts, revision_feedback=feedback,
            ))
            await require_success("Content Engine", content_res)
            await log("Content Engine", f"Headline: {content_res.flagship_headline}", "completed",
                      {"generation_mode": content_res.generation_mode, "revision": attempt})

            await log("Repurposing Agent", "Adapting the message natively for each platform.", "started")
            repurp_res = await self.repurposer.execute(RepurposingInput(
                flagship_copy=content_res.flagship_copy, headline=content_res.flagship_headline, brand=brand,
                call_to_action=content_res.call_to_action, platforms=platforms, tone=tone, goal=goal,
                audience=audience, banned_words=brand_res.voice_profile.banned_words,
                primary_color=primary_color,
            ))
            await require_success("Repurposing Agent", repurp_res)
            modes = sorted({p.generation_mode for p in repurp_res.posts})
            await log("Repurposing Agent", f"Created {repurp_res.total_platforms} platform-specific draft(s).", "completed",
                      {"generation_modes": modes})

            await log("Quality Gate", "Checking platform limits and brand-safety rules.", "started")
            quality_res = await self.quality_gate.execute(QualityGateInput(
                posts=repurp_res.posts, voice_profile=brand_res.voice_profile
            ))
            await require_success("Quality Gate", quality_res)
            await log("Quality Gate", f"Score {quality_res.compliance_score}/100; passed={quality_res.passed}.",
                      "completed" if quality_res.passed else "failed",
                      {"blockers": quality_res.blockers, "warnings": quality_res.warnings})
            if quality_res.passed:
                break
            if attempt >= revision_limit or not llm_available:
                raise RuntimeError(
                    "Quality Gate blocked the workflow; revise the content and re-run before approval. "
                    + "; ".join(quality_res.blockers)
                )
            feedback = list(quality_res.blockers)
            revisions_used += 1

        await log("Approval Gate", "Waiting for a human decision before external publication." if approval_required
                  else "Approval not required for this run (autonomous mode).", "waiting" if approval_required else "completed")
        approval_res = await self.approval_gate.execute(ApprovalGateInput(
            workflow_id=orch_res.workflow_id, run_id=orch_res.workflow_id,
            required=approval_required, action="request"
        ))

        pub_res = await self.publishing.execute(PublishingInput(
            posts=repurp_res.posts, is_approved=False, tenant_id=tenant_id,
            connected_adapters=connected_adapters or {}, live_publish_requested=False
        ))
        await log("Publishing Agent", pub_res.audit_summary, "completed")

        await log("Analytics Agent", "Defining the measurement plan.", "started")
        analytics_res = await self.analytics.execute(AnalyticsInput(platforms=platforms, goal=goal, has_live_connections=False))
        await require_success("Analytics Agent", analytics_res)
        await log("Analytics Agent", analytics_res.measurement_plan_notes, "completed")

        await log("Reporting Agent", "Compiling the campaign brief.", "started")
        report_res = await self.reporting.execute(ReportingInput(
            brand=brand, goal=goal, workflow_id=orch_res.workflow_id,
            posts=repurp_res.posts, quality_summary=quality_res, analytics_plan=analytics_res
        ))
        await require_success("Reporting Agent", report_res)
        await log("Reporting Agent", f"Report compiled: {report_res.readiness_status}", "completed")

        final_status = "awaiting_approval" if approval_required else "draft_ready"
        return WorkflowExecutionResult(
            workflow_id=orch_res.workflow_id, status=final_status, orchestrator=orch_res,
            brand_memory=brand_res, market_radar=radar_res, content_engine=content_res,
            repurposer=repurp_res, quality_gate=quality_res, approval_gate=approval_res,
            publishing=pub_res, analytics=analytics_res, reporting=report_res, logs=logs,
            revisions_used=revisions_used,
            cost_summary=self._usage_of(radar_res, content_res, repurp_res),
        )
