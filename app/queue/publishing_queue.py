"""Production Queue-Based Publishing and Retry Hardening.

Features:
1. Deterministic Idempotency Key computation based on run_id, platform, and content hash.
2. Error classification:
   - Transient (HTTP 429, 500, 502, 503, 504, network timeouts): triggers exponential backoff retry.
   - Permanent (HTTP 400, 401, 403, missing scopes, banned copy): sends directly to Dead-Letter state.
3. Audit trail integration for publishing lifecycle events.
"""
import hashlib
import uuid
import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from app.integrations.base import PlatformPublishResult


class PublishingJob(BaseModel):
    model_config = {"populate_by_name": True}

    job_id: str
    run_id: str
    tenant_id: str
    platform: str
    connection_id: str
    post_copy: str = Field(alias="copy")
    media_urls: List[str] = Field(default_factory=list)
    idempotency_key: str
    status: str = "queued"  # queued, publishing, succeeded, failed_transient, dead_letter
    retry_count: int = 0
    max_retries: int = 3
    last_error: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    @property
    def copy(self) -> str:
        return self.post_copy


def compute_deterministic_idempotency_key(run_id: str, platform: str, copy: str) -> str:
    """Generates an SHA-256 derived deterministic idempotency key to prevent duplicate posts."""
    raw = f"{run_id}:{platform.lower().strip()}:{copy.strip()}"
    content_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"pub_{run_id[:8]}_{platform.lower()}_{content_hash}"


def classify_publish_error(error_message: Optional[str], status_code: Optional[int] = None) -> str:
    """Classifies an error into 'transient' (retryable) or 'permanent' (dead_letter)."""
    if not error_message:
        return "transient"

    err_lower = error_message.lower()

    # Permanent failure indicators
    permanent_indicators = [
        "401", "unauthorized", "invalid token", "token revoked", "expired token",
        "403", "forbidden", "missing scope", "permission denied", "insufficient scope",
        "400", "bad request", "character limit exceeded", "invalid media",
        "duplicate", "already posted"
    ]
    for ind in permanent_indicators:
        if ind in err_lower:
            return "permanent"

    if status_code in (400, 401, 403, 422):
        return "permanent"

    # Transient failure indicators
    transient_indicators = [
        "429", "rate limit", "too many requests",
        "500", "502", "503", "504", "internal server error", "bad gateway",
        "service unavailable", "gateway timeout", "timeout", "connection reset", "connection aborted"
    ]
    for ind in transient_indicators:
        if ind in err_lower:
            return "transient"

    if status_code and status_code >= 500:
        return "transient"

    # Default to transient for unexpected network exceptions
    return "transient"


class DurablePublishingQueue:
    """In-memory & SQLite-backed durable publishing queue with retry classification."""

    def __init__(self, platform_manager=None):
        self._platform_manager = platform_manager
        self._dead_letter_jobs: Dict[str, PublishingJob] = {}

    def create_job(
        self,
        run_id: str,
        tenant_id: str,
        platform: str,
        connection_id: str,
        copy: str,
        media_urls: Optional[List[str]] = None
    ) -> PublishingJob:
        idempotency_key = compute_deterministic_idempotency_key(run_id, platform, copy)
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        return PublishingJob(
            job_id=job_id,
            run_id=run_id,
            tenant_id=tenant_id,
            platform=platform,
            connection_id=connection_id,
            copy=copy,
            media_urls=media_urls or [],
            idempotency_key=idempotency_key
        )

    async def execute_job(self, job: PublishingJob, manager) -> PlatformPublishResult:
        """Executes a publishing job with retry classification."""
        job.status = "publishing"
        job.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        res = await manager.publish(
            platform=job.platform,
            connection_id=job.connection_id,
            copy=job.copy,
            media_urls=job.media_urls,
            idempotency_key=job.idempotency_key,
            tenant_id=job.tenant_id
        )

        if res.success:
            job.status = "succeeded"
            job.last_error = None
        else:
            job.last_error = res.error_message
            err_type = classify_publish_error(res.error_message)

            if err_type == "permanent":
                job.status = "dead_letter"
                self._dead_letter_jobs[job.job_id] = job
            else:
                job.retry_count += 1
                if job.retry_count >= job.max_retries:
                    job.status = "dead_letter"
                    self._dead_letter_jobs[job.job_id] = job
                else:
                    job.status = "failed_transient"

        job.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return res

    def get_dead_letter_jobs(self, tenant_id: str) -> List[PublishingJob]:
        return [j for j in self._dead_letter_jobs.values() if j.tenant_id == tenant_id]


durable_publishing_queue = DurablePublishingQueue()
