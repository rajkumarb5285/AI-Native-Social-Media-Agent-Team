"""Draft-only publishing gate.

Actual platform writes are delegated to the authenticated application service.
This agent must never claim that an external post exists unless an adapter has
returned a real external post identifier.
"""
from typing import Optional
from pydantic import Field
from app.agents.base import BaseAgent, AgentInput, AgentOutput, current_time_iso
from app.agents.repurposing import PlatformPost


class PublishItemResult(AgentInput):
    platform: str
    status: str
    external_post_id: Optional[str] = None
    idempotency_key: str
    timestamp: str = Field(default_factory=current_time_iso)
    details: str


class PublishingInput(AgentInput):
    posts: list[PlatformPost]
    is_approved: bool
    tenant_id: str = "default"
    connected_adapters: dict[str, bool] = Field(default_factory=dict)
    live_publish_requested: bool = False


class PublishingOutput(AgentOutput):
    results: list[PublishItemResult] = Field(default_factory=list)
    all_published: bool = False
    draft_only_mode: bool = True
    audit_summary: str


class PublishingAgent(BaseAgent[PublishingInput, PublishingOutput]):
    agent_id = "publishing"
    name = "Publishing Agent"
    department = "Operations"
    description = "Prepares draft status; real writes happen only through the verified application publisher."

    async def execute(self, input_data: PublishingInput) -> PublishingOutput:
        import hashlib
        results = []
        if not input_data.is_approved:
            for post in input_data.posts:
                key = hashlib.sha256(
                    f"{input_data.tenant_id}:{post.platform}:{post.copy}".encode("utf-8")
                ).hexdigest()
                results.append(PublishItemResult(
                    platform=post.platform,
                    status="blocked",
                    idempotency_key=key,
                    details="Publishing blocked: human approval has not been granted."
                ))
            return PublishingOutput(
                success=False, errors=["Approval required before publishing."],
                results=results, all_published=False, draft_only_mode=True,
                audit_summary="Blocked by approval gate."
            )

        for post in input_data.posts:
            key = hashlib.sha256(
                f"{input_data.tenant_id}:{post.platform}:{post.copy}".encode("utf-8")
            ).hexdigest()
            results.append(PublishItemResult(
                platform=post.platform,
                status="draft_retained",
                idempotency_key=key,
                details=(
                    "Draft is approved internally. No external publishing is performed by this graph stage; "
                    "use the authenticated publish service to dispatch and verify the platform response."
                )
            ))
        return PublishingOutput(
            success=True, results=results, all_published=False, draft_only_mode=True,
            audit_summary="Draft status recorded. External publication has not been attempted."
        )
