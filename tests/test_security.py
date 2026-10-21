import pytest
from fastapi.testclient import TestClient
from app.main import app, init_db
from app.security.auth import create_jwt, AuthenticatedUser
from app.security.rbac import Role
from app.security.auth import verify_jwt

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_sec_runs.db"
    monkeypatch.setattr("app.main.DB_PATH", str(test_db))
    init_db()

@pytest.fixture
def client():
    return TestClient(app)

def test_jwt_rejects_tampered_signature():
    user = AuthenticatedUser(user_id="secure_user", email="secure@example.com", role=Role.ADMIN.value, tenant_id="secure_tenant")
    token = create_jwt(user)
    parts = token.split(".")
    parts[1] = parts[1][:-1] + ("A" if parts[1][-1] != "A" else "B")
    tampered = ".".join(parts)
    assert verify_jwt(tampered) is None

def test_missing_authentication_is_rejected(client):
    res = client.get("/api/runs")
    assert res.status_code == 401

def test_tenant_isolation(client):
    # Tenant A creates a run
    user_a = AuthenticatedUser(user_id="user_a", email="a@tenanta.com", role=Role.ADMIN.value, tenant_id="tenant_a")
    token_a = create_jwt(user_a)

    headers_a = {"Authorization": f"Bearer {token_a}"}
    create_res = client.post("/api/runs", json={"brand": "Brand A", "goal": "Launch A"}, headers=headers_a)
    assert create_res.status_code == 200
    run_id = create_res.json()["id"]

    # Tenant B tries to view Tenant A's run
    user_b = AuthenticatedUser(user_id="user_b", email="b@tenantb.com", role=Role.ADMIN.value, tenant_id="tenant_b")
    token_b = create_jwt(user_b)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    get_res = client.get(f"/api/runs/{run_id}", headers=headers_b)
    assert get_res.status_code == 404 # Isolated: cannot see other tenant's run

    # Tenant B listing runs should be empty
    list_res_b = client.get("/api/runs", headers=headers_b)
    assert list_res_b.status_code == 200
    assert len(list_res_b.json()["runs"]) == 0

    # Tenant A listing runs sees 1 run
    list_res_a = client.get("/api/runs", headers=headers_a)
    assert len(list_res_a.json()["runs"]) == 1

def test_rbac_permissions(client):
    # Admin creates run
    admin_user = AuthenticatedUser(user_id="admin_1", email="admin@corp.com", role=Role.ADMIN.value, tenant_id="t1")
    admin_token = create_jwt(admin_user)
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    res = client.post("/api/runs", json={"brand": "Brand X", "goal": "Goal X"}, headers=headers_admin)
    run_id = res.json()["id"]

    # Viewer role tries to approve run -> 403 Forbidden
    viewer_user = AuthenticatedUser(user_id="viewer_1", email="viewer@corp.com", role=Role.VIEWER.value, tenant_id="t1")
    viewer_token = create_jwt(viewer_user)
    headers_viewer = {"Authorization": f"Bearer {viewer_token}"}

    approve_fail = client.post(f"/api/runs/{run_id}/approve", headers=headers_viewer)
    assert approve_fail.status_code == 403

    # Editor role approves run -> 200 OK
    editor_user = AuthenticatedUser(user_id="editor_1", email="editor@corp.com", role=Role.EDITOR.value, tenant_id="t1")
    editor_token = create_jwt(editor_user)
    headers_editor = {"Authorization": f"Bearer {editor_token}"}

    approve_ok = client.post(f"/api/runs/{run_id}/approve", headers=headers_editor)
    assert approve_ok.status_code == 200
    assert approve_ok.json()["status"] == "approved"

def test_publish_approval_and_connection_guard(client):
    admin_user = AuthenticatedUser(user_id="admin_1", email="admin@corp.com", role=Role.ADMIN.value, tenant_id="t1")
    admin_token = create_jwt(admin_user)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create run
    res = client.post("/api/runs", json={"brand": "Brand Guard", "goal": "Test Guard"}, headers=headers)
    run_id = res.json()["id"]

    # Attempt publish before approval -> 403 Forbidden
    pub_unapproved = client.post(f"/api/runs/{run_id}/publish", headers=headers)
    assert pub_unapproved.status_code == 403
    assert "Explicit human approval is required" in pub_unapproved.json()["detail"]

    # Approve run
    client.post(f"/api/runs/{run_id}/approve", headers=headers)

    # Attempt publish without connected platform accounts -> 412 Precondition Failed
    pub_no_conn = client.post(f"/api/runs/{run_id}/publish", headers=headers)
    assert pub_no_conn.status_code == 412
    assert "No verified official platform connections" in pub_no_conn.json()["detail"]

def test_audit_trail(client):
    admin_user = AuthenticatedUser(user_id="aud_admin", email="audit@corp.com", role=Role.ADMIN.value, tenant_id="t_audit")
    admin_token = create_jwt(admin_user)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create and approve run
    res = client.post("/api/runs", json={"brand": "Audit Brand", "goal": "Audit Goal"}, headers=headers)
    run_id = res.json()["id"]
    client.post(f"/api/runs/{run_id}/approve", headers=headers)

    # Check audit logs
    audit_res = client.get("/api/audit", headers=headers)
    assert audit_res.status_code == 200
    events = audit_res.json()["events"]
    assert len(events) >= 2
    actions = [e["action"] for e in events]
    assert "WORKFLOW_CREATED" in actions
    assert "DRAFT_APPROVED" in actions
