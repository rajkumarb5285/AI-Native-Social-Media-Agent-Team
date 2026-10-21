import os
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app, init_db
from app.security.auth import create_jwt, AuthenticatedUser
from app.security.rbac import Role

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_runs.db"
    monkeypatch.setattr("app.main.DB_PATH", str(test_db))
    init_db()

@pytest.fixture
def client():
    test_user = AuthenticatedUser(user_id="api-test-user", email="api-test@example.com", role=Role.ADMIN.value, tenant_id="api-test-tenant")
    test_client = TestClient(app)
    test_client.headers.update({"Authorization": f"Bearer {create_jwt(test_user)}"})
    return test_client

def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "AI Native" in response.text
    assert "Social Agent Team" in response.text

def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["mode"] in ("demo", "llm-enabled")
    assert data["integrations"]["social_publishing"] is False

def test_agents_endpoint(client):
    response = client.get("/api/agents")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert len(data["agents"]) >= 6
    agent_ids = [a["id"] for a in data["agents"]]
    assert "orchestrator" in agent_ids
    assert "market-radar" in agent_ids
    assert "content-engine" in agent_ids

def test_list_runs_initially_empty(client):
    response = client.get("/api/runs")
    assert response.status_code == 200
    assert response.json() == {"runs": []}

def test_create_run_validation(client):
    # Missing brand and goal
    response = client.post("/api/runs", json={})
    assert response.status_code == 422

    # Brand too long
    response = client.post("/api/runs", json={"brand": "x" * 150, "goal": "Launch"})
    assert response.status_code == 422

def test_create_run_and_approval_flow(client):
    payload = {
        "brand": "Test Coffee Co",
        "goal": "Launch artisan nitro cold brew",
        "platforms": ["LinkedIn", "Instagram"],
        "audience": "remote tech workers",
        "tone": "sharp and energized",
        "offer": "20% off starter cans",
        "context": "Organic Colombian beans, 18-hour steep.",
        "approval_required": True
    }
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 200
    run_data = response.json()
    run_id = run_data["id"]
    assert run_data["status"] == "awaiting_approval"
    assert run_data["mode"] in ("demo", "llm-enabled")
    assert "result" in run_data
    assert "content" in run_data["result"]
    assert len(run_data["result"]["content"]) == 2
    assert len(run_data["logs"]) >= 5

    # Retrieve by ID
    get_res = client.get(f"/api/runs/{run_id}")
    assert get_res.status_code == 200
    assert get_res.json()["approved"] is False

    # List runs includes it
    list_res = client.get("/api/runs")
    assert list_res.status_code == 200
    assert len(list_res.json()["runs"]) == 1

    # Approve run
    approve_res = client.post(f"/api/runs/{run_id}/approve")
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "approved"

    # Verify approved state
    get_res_after = client.get(f"/api/runs/{run_id}")
    assert get_res_after.json()["approved"] is True
    assert get_res_after.json()["status"] == "approved"

def test_clean_and_parse_json():
    from app.main import clean_and_parse_json
    # Plain JSON
    assert clean_and_parse_json('{"key": "val"}') == {"key": "val"}
    # Markdown code fence with json tag
    assert clean_and_parse_json('```json\n{"key": "val"}\n```') == {"key": "val"}
    # Markdown code fence without tag
    assert clean_and_parse_json('```\n{"key": "val"}\n```') == {"key": "val"}

def test_create_run_empty_platforms(client):
    response = client.post("/api/runs", json={
        "brand": "Acme",
        "goal": "Test goal",
        "platforms": []
    })
    assert response.status_code == 422

def test_get_nonexistent_run(client):
    res = client.get("/api/runs/non-existent-id")
    assert res.status_code == 404

def test_approve_nonexistent_run(client):
    res = client.post("/api/runs/non-existent-id/approve")
    assert res.status_code == 404

def test_integration_readiness_never_returns_secrets(client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://api.example.com")
    monkeypatch.setenv("LINKEDIN_CLIENT_ID", "visible-id-must-not-leak")
    monkeypatch.setenv("LINKEDIN_CLIENT_SECRET", "private-linkedin-secret")
    monkeypatch.setenv("TWITTER_CLIENT_ID", "visible-x-id-must-not-leak")
    monkeypatch.setenv("TWITTER_CLIENT_SECRET", "private-x-secret")
    monkeypatch.setenv("SECRET_ENCRYPTION_KEY", "private-encryption-secret")
    monkeypatch.setenv("JWT_SECRET", "a-long-test-secret-that-is-not-the-default")

    response = client.get("/api/integrations/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["platforms"]["linkedin"]["oauth_ready"] is True
    assert data["platforms"]["x"]["oauth_ready"] is True
    assert data["token_encryption_key_configured"] is True
    assert "private-linkedin-secret" not in response.text
    assert "private-x-secret" not in response.text
    assert "private-encryption-secret" not in response.text


def test_linkedin_oauth_requires_client_secret(client, monkeypatch):
    monkeypatch.setenv("LINKEDIN_CLIENT_ID", "configured-client-id")
    monkeypatch.delenv("LINKEDIN_CLIENT_SECRET", raising=False)
    response = client.get("/api/connections/linkedin/connect")
    assert response.status_code == 503
    assert "LINKEDIN_CLIENT_SECRET" in response.json()["detail"]

