import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app, init_db, task_queue

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_realtime_runs.db"
    monkeypatch.setattr("app.main.DB_PATH", str(test_db))
    init_db()

@pytest.fixture
def client():
    return TestClient(app)

def test_async_queue_and_status(client):
    payload = {
        "brand": "Quantum AI",
        "goal": "Announce series A funding",
        "platforms": ["LinkedIn"],
        "audience": "investors and developers",
        "tone": "visionary and confident",
        "approval_required": True
    }
    # Enqueue asynchronously
    res = client.post("/api/runs?sync=false", json=payload)
    assert res.status_code == 200
    data = res.json()
    run_id = data["id"]
    assert data["status"] == "queued"
    assert "stream_url" in data

    # Verify run persists as queued
    get_res = client.get(f"/api/runs/{run_id}")
    assert get_res.status_code == 200
    assert get_res.json()["status"] in ("queued", "running", "awaiting_approval")

def test_cancellation_flow(client):
    payload = {
        "brand": "CancelCo",
        "goal": "Goal to be cancelled",
        "platforms": ["LinkedIn"],
        "approval_required": True
    }
    res = client.post("/api/runs?sync=false", json=payload)
    run_id = res.json()["id"]

    # Cancel run
    cancel_res = client.post(f"/api/runs/{run_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    # Verify status in database
    get_res = client.get(f"/api/runs/{run_id}")
    assert get_res.json()["status"] == "cancelled"

    # Second cancel should fail with 409
    cancel_again = client.post(f"/api/runs/{run_id}/cancel")
    assert cancel_again.status_code == 409

def test_retry_flow(client):
    payload = {
        "brand": "RetryCo",
        "goal": "Goal to test retry",
        "platforms": ["LinkedIn"],
        "approval_required": True
    }
    res = client.post("/api/runs?sync=false", json=payload)
    run_id = res.json()["id"]

    # Cancel it first so it is eligible for retry
    client.post(f"/api/runs/{run_id}/cancel")

    # Now retry
    retry_res = client.post(f"/api/runs/{run_id}/retry")
    assert retry_res.status_code == 200
    assert retry_res.json()["status"] == "queued"

    get_res = client.get(f"/api/runs/{run_id}")
    assert get_res.json()["retry_count"] == 1

def test_sse_stream_snapshot(client):
    payload = {
        "brand": "StreamCo",
        "goal": "Verify stream snapshot",
        "platforms": ["LinkedIn"],
        "approval_required": True
    }
    res = client.post("/api/runs?sync=true", json=payload)
    run_id = res.json()["id"]

    # Stream snapshot check
    with client.stream("GET", f"/api/runs/{run_id}/stream") as response:
        assert response.status_code == 200
        # Read the first event
        for line in response.iter_lines():
            if line.startswith("data:"):
                event_data = json.loads(line.replace("data: ", ""))
                assert event_data["event"] == "snapshot"
                assert event_data["status"] == "awaiting_approval"
                break
