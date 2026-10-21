import pytest
from app.agents.orchestrator import OrchestratorAgent, OrchestratorInput
from app.agents.brand_memory import BrandMemoryAgent, BrandMemoryInput
from app.agents.market_radar import MarketRadarAgent, MarketRadarInput
from app.agents.content_engine import ContentEngineAgent, ContentEngineInput
from app.agents.repurposing import RepurposingAgent, RepurposingInput, PlatformPost
from app.agents.quality_gate import QualityGateAgent, QualityGateInput
from app.agents.approval_gate import ApprovalGateAgent, ApprovalGateInput
from app.agents.publishing import PublishingAgent, PublishingInput
from app.agents.analytics import AnalyticsAgent, AnalyticsInput
from app.agents.reporting import ReportingAgent, ReportingInput
from app.agents.graph import AgentGraph

@pytest.mark.asyncio
async def test_orchestrator_agent():
    agent = OrchestratorAgent()
    assert agent.agent_id == "orchestrator"
    
    # Valid input
    inp = OrchestratorInput(
        brand="Acme Co",
        goal="Launch product X",
        platforms=["LinkedIn", "Twitter"],
        approval_required=True
    )
    out = await agent.execute(inp)
    assert out.success is True
    assert out.workflow_id.startswith("wf-")
    assert len(out.plan) == 9
    assert out.selected_platforms == ["LinkedIn", "Twitter"]

@pytest.mark.asyncio
async def test_brand_memory_agent():
    agent = BrandMemoryAgent()
    out = await agent.execute(BrandMemoryInput(brand="Acme", custom_guidelines="Strictly avoid slang"))
    assert out.success is True
    assert "Acme" in out.retrieved_context_summary
    assert len(out.voice_profile.banned_words) > 0

@pytest.mark.asyncio
async def test_market_radar_agent():
    agent = MarketRadarAgent()
    out = await agent.execute(MarketRadarInput(
        brand="Acme",
        goal="Cold brew launch",
        audience="professionals",
        enable_live_search=False
    ))
    assert out.success is True
    assert out.is_live_search is False
    assert out.audience_pain_points == []
    assert len(out.recommended_angles) > 0

@pytest.mark.asyncio
async def test_content_engine_agent():
    agent = ContentEngineAgent()
    out = await agent.execute(ContentEngineInput(
        brand="Acme",
        goal="Launch Cold Brew",
        tone="professional",
        audience="remote workers",
        offer="Save 15%"
    ))
    assert out.success is True
    assert len(out.flagship_headline) > 3
    assert "15%" in out.call_to_action or len(out.call_to_action) > 5
    assert out.generation_mode in {"llm", "template_fallback"}

@pytest.mark.asyncio
async def test_repurposing_agent():
    agent = RepurposingAgent()
    out = await agent.execute(RepurposingInput(
        flagship_copy="This is core copy.",
        headline="Core Headline",
        brand="Acme",
        call_to_action="Click here",
        platforms=["LinkedIn", "Twitter", "Instagram"]
    ))
    assert out.success is True
    assert len(out.posts) == 3
    # Twitter limit check
    tw_post = next(p for p in out.posts if p.platform == "Twitter")
    assert tw_post.within_limits is True
    assert tw_post.char_limit == 280

@pytest.mark.asyncio
async def test_quality_gate_clean_and_violations():
    agent = QualityGateAgent()
    brand_agent = BrandMemoryAgent()
    brand_out = await brand_agent.execute(BrandMemoryInput(brand="Acme"))

    # Clean posts
    posts = [
        PlatformPost(
            platform="LinkedIn", copy="Great reliable product.", character_count=23,
            char_limit=3000, within_limits=True
        )
    ]
    clean_out = await agent.execute(QualityGateInput(posts=posts, voice_profile=brand_out.voice_profile))
    assert clean_out.passed is True
    assert clean_out.compliance_score == 100

    # Posts with banned word
    bad_posts = [
        PlatformPost(
            platform="LinkedIn", copy="This is a get rich quick scheme with guaranteed 100% win.",
            character_count=60, char_limit=3000, within_limits=True
        )
    ]
    bad_out = await agent.execute(QualityGateInput(posts=bad_posts, voice_profile=brand_out.voice_profile))
    assert bad_out.passed is False
    assert len(bad_out.blockers) > 0
    assert bad_out.compliance_score < 100

@pytest.mark.asyncio
async def test_approval_gate_lifecycle():
    agent = ApprovalGateAgent()

    # Request stage
    req_out = await agent.execute(ApprovalGateInput(workflow_id="wf-1", run_id="run-1", action="request"))
    assert req_out.status == "awaiting_approval"

    # Approve action
    appr_out = await agent.execute(ApprovalGateInput(
        workflow_id="wf-1", run_id="run-1", action="approve", approver="editor@firm.com", comments="Looks great"
    ))
    assert appr_out.status == "approved"
    assert appr_out.approved_by == "editor@firm.com"

    # Reject action
    rej_out = await agent.execute(ApprovalGateInput(
        workflow_id="wf-1", run_id="run-1", action="reject", comments="Tone is too casual"
    ))
    assert rej_out.status == "rejected"

@pytest.mark.asyncio
async def test_publishing_agent_blocks_when_unapproved():
    agent = PublishingAgent()
    posts = [PlatformPost(platform="LinkedIn", copy="Test", character_count=4, char_limit=3000, within_limits=True)]
    
    # Blocked
    out_blocked = await agent.execute(PublishingInput(posts=posts, is_approved=False))
    assert out_blocked.success is False
    assert out_blocked.results[0].status == "blocked"

    # Approved but no connected live adapters
    out_draft = await agent.execute(PublishingInput(posts=posts, is_approved=True, connected_adapters={}))
    assert out_draft.success is True
    assert out_draft.results[0].status == "draft_retained"
    assert out_draft.draft_only_mode is True

@pytest.mark.asyncio
async def test_analytics_agent():
    agent = AnalyticsAgent()
    out = await agent.execute(AnalyticsInput(platforms=["LinkedIn"], goal="Boost signups", has_live_connections=False))
    assert out.success is True
    assert out.is_live_data is False
    assert len(out.targets) >= 3

@pytest.mark.asyncio
async def test_reporting_agent():
    agent = ReportingAgent()
    # Dummy quality and analytics inputs
    from app.agents.quality_gate import QualityGateOutput
    from app.agents.analytics import AnalyticsOutput
    q_out = QualityGateOutput(passed=True, compliance_score=95)
    a_out = AnalyticsOutput(primary_kpi="Engagement Rate", measurement_plan_notes="Baseline target")
    
    out = await agent.execute(ReportingInput(
        brand="Acme",
        goal="Launch campaign",
        workflow_id="wf-1",
        posts=[],
        quality_summary=q_out,
        analytics_plan=a_out
    ))
    assert out.success is True
    assert "Passed" in out.compliance_verdict
    assert len(out.recommended_next_actions) > 0

@pytest.mark.asyncio
async def test_full_agent_graph_pipeline():
    graph = AgentGraph()
    res = await graph.run(
        brand="Solaris Energy",
        goal="Launch residential solar subscription",
        platforms=["LinkedIn", "Instagram"],
        audience="homeowners aged 30-55",
        tone="authoritative and encouraging",
        offer="Free rooftop assessment",
        context="Tier-1 solar panels, 25-year warranty, zero money down.",
        approval_required=True
    )
    assert res.workflow_id.startswith("wf-")
    assert res.status == "awaiting_approval"
    assert res.orchestrator.success is True
    assert res.brand_memory.success is True
    assert res.market_radar.success is True
    assert res.content_engine.success is True
    assert res.content_engine.generation_mode in {"llm", "template_fallback"}
    assert len(res.repurposer.posts) == 2
    assert res.quality_gate.passed is True
    assert res.approval_gate.status == "awaiting_approval"
    assert res.publishing.draft_only_mode is True
    assert res.analytics.is_live_data is False
    assert res.reporting.success is True
    assert len(res.logs) >= 10
