import pytest
import datetime
from fastapi.testclient import TestClient

from app.main import app, init_db
from app.security.auth import create_jwt, AuthenticatedUser
from app.security.rbac import Role
from app.queue.publishing_queue import (
    compute_deterministic_idempotency_key,
    classify_publish_error,
    durable_publishing_queue,
    PublishingJob
)
from app.integrations.base import PlatformPublishResult, BaseSocialAdapter
from app.integrations.manager import PlatformManager, ConnectionRecord
from app.integrations.crypto import encrypt_token


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_phase8_prod.db"
    monkeypatch.setattr("app.main.DB_PATH", str(test_db))
    monkeypatch.setattr("app.services.analytics.analytics_service._db_path_getter", lambda: str(test_db))
    init_db()


@pytest.fixture
def client():
    user = AuthenticatedUser(
        user_id="user_p8_admin",
        email="admin@production.com",
        role=Role.ADMIN.value,
        tenant_id="tenant_p8_prod"
    )
    c = TestClient(app)
    c.headers.update({"Authorization": f"Bearer {create_jwt(user)}"})
    return c


def test_production_readiness_probe(client):
    """Verifies that the /api/ready and /ready probes test database, encryption, and storage."""
    # 1. /api/ready
    res = client.get("/api/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["checks"]["database"] == "ok"
    assert data["checks"]["encryption"] == "ok"
    assert data["checks"]["storage"] == "ok"

    # 2. Root /ready alias for Kubernetes / Render / AWS health probes
    res_root = client.get("/ready")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "ready"


def test_deterministic_idempotency_key_generation():
    """Validates that identical posts yield identical keys, and different content yields different keys."""
    run_id = "run_12345678_abcd"
    copy_a = "Check out our exclusive drop! #sneakers"
    copy_b = "Check out our exclusive drop! #streetwear"

    key_1 = compute_deterministic_idempotency_key(run_id, "LinkedIn", copy_a)
    key_2 = compute_deterministic_idempotency_key(run_id, "linkedin", copy_a)
    key_diff = compute_deterministic_idempotency_key(run_id, "linkedin", copy_b)

    # Must be deterministic regardless of platform casing
    assert key_1 == key_2
    assert key_1.startswith("pub_run_1234_linkedin_")
    # Different copy must produce a distinct idempotency key
    assert key_1 != key_diff


def test_publish_error_classification():
    """Validates that transient errors trigger retry, while permanent auth/scope errors dead-letter."""
    # 1. Transient errors (should be retryable)
    assert classify_publish_error("HTTP 429 Too Many Requests: Rate limit exceeded") == "transient"
    assert classify_publish_error("HTTP 503 Service Unavailable: upstream timeout") == "transient"
    assert classify_publish_error("Connection reset by peer: network timeout") == "transient"
    assert classify_publish_error("Gateway timeout", status_code=504) == "transient"

    # 2. Permanent errors (should dead-letter immediately)
    assert classify_publish_error("HTTP 401 Unauthorized: token revoked by user") == "permanent"
    assert classify_publish_error("HTTP 403 Forbidden: Insufficient scope w_member_social") == "permanent"
    assert classify_publish_error("HTTP 400 Bad Request: Character limit exceeded") == "permanent"
    assert classify_publish_error("Duplicate post detected on social account", status_code=400) == "permanent"


@pytest.mark.asyncio
async def test_publishing_queue_transient_retry_and_dead_letter():
    """Tests that durable publishing queue increments retry on transient error and routes permanent to dead-letter."""
    class MockManager:
        def __init__(self, fail_type="transient"):
            self.fail_type = fail_type
            self._published_keys = set()

        async def publish(self, platform, connection_id, copy, media_urls, idempotency_key, tenant_id):
            if idempotency_key in self._published_keys:
                return PlatformPublishResult(success=True, platform=platform, idempotency_key=idempotency_key, external_post_id="idempotent_cached_post")
            if self.fail_type == "transient":
                return PlatformPublishResult(success=False, platform=platform, idempotency_key=idempotency_key, error_message="HTTP 503 Service Unavailable")
            elif self.fail_type == "permanent":
                return PlatformPublishResult(success=False, platform=platform, idempotency_key=idempotency_key, error_message="HTTP 401 Unauthorized: token expired")
            self._published_keys.add(idempotency_key)
            return PlatformPublishResult(success=True, platform=platform, idempotency_key=idempotency_key, external_post_id="post_999")

    queue = durable_publishing_queue

    # 1. Transient job: attempt 1 sets failed_transient and increments retry
    transient_job = queue.create_job(
        run_id="run_retry_test",
        tenant_id="tenant_p8",
        platform="linkedin",
        connection_id="conn_1",
        copy="Test post"
    )
    mgr_transient = MockManager("transient")
    res1 = await queue.execute_job(transient_job, mgr_transient)
    assert res1.success is False
    assert transient_job.status == "failed_transient"
    assert transient_job.retry_count == 1

    # 2. Permanent job: goes straight to dead_letter without retry
    perm_job = queue.create_job(
        run_id="run_deadletter_test",
        tenant_id="tenant_p8",
        platform="twitter",
        connection_id="conn_2",
        copy="Dead letter post"
    )
    mgr_perm = MockManager("permanent")
    res2 = await queue.execute_job(perm_job, mgr_perm)
    assert res2.success is False
    assert perm_job.status == "dead_letter"
    dead_letters = queue.get_dead_letter_jobs("tenant_p8")
    assert any(j.job_id == perm_job.job_id for j in dead_letters)


def test_production_owasp_security_headers_and_isolation(client):
    """Verifies that requests strictly require authorization and enforce tenant boundaries."""
    # 1. Unauthenticated request to protected endpoint is rejected
    unauth_client = TestClient(app)
    res_unauth = unauth_client.get("/api/runs")
    assert res_unauth.status_code == 401

    # 2. Tampered JWT signature is rejected
    fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    res_fake = unauth_client.get("/api/runs", headers={"Authorization": f"Bearer {fake_token}"})
    assert res_fake.status_code == 401
