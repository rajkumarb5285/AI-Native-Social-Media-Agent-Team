import pytest
import pyotp
from fastapi.testclient import TestClient
from app.main import app, init_db
from app.agents.repurposing import RepurposingAgent, RepurposingInput

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_mfa.db"
    monkeypatch.setattr("app.main.DB_PATH", str(test_db))
    init_db()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.asyncio
async def test_repurposing_agent_supports_gmb():
    agent = RepurposingAgent()
    inp = RepurposingInput(
        flagship_copy="Experience our award-winning handcrafted espresso and fresh pastries in the heart of the city.",
        headline="Best Coffee in Town - Verified 5-Star Experience",
        brand="Artisan Roast Cafe",
        call_to_action="Visit us on 5th Avenue today!",
        tone="visionary",
        platforms=["GMB", "Instagram", "LinkedIn"]
    )
    res = await agent.execute(inp)
    assert res.success is True
    assert len(res.errors) == 0
    assert res.total_platforms == 3
    
    gmb_post = next((p for p in res.posts if p.platform.upper() == "GMB"), None)
    assert gmb_post is not None
    assert gmb_post.within_limits is True
    assert "Visit / Connect with Us Today" in gmb_post.post_copy
    assert "#GoogleBusiness" in gmb_post.hashtags

def test_strict_login_rejects_unknown_account(client):
    res = client.post("/api/auth/login", json={
        "email": "nonexistent.founder@business.com",
        "password": "ValidPassword123!"
    })
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]

def test_password_strength_enforced(client):
    # Too short (< 6 chars) rejected by schema with 422
    res_short = client.post("/api/auth/register", json={
        "email": "test.weak@business.com",
        "password": "weak"
    })
    assert res_short.status_code == 422

    # Lacking numbers or complexity rejected by password validator with 400
    res_weak = client.post("/api/auth/register", json={
        "email": "test.weak2@business.com",
        "password": "weakpassword"
    })
    assert res_weak.status_code == 400

def test_mfa_flow_totp_and_otp(client):
    # 1. Register with MFA enabled
    reg_res = client.post("/api/auth/register", json={
        "email": "mfa.user@enterprise.com",
        "password": "SecurePassword2026!",
        "business_name": "Apex Enterprise",
        "enable_mfa": True
    })
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert reg_data["user"]["mfa_enabled"] is True
    assert "mfa_setup" in reg_data
    totp_secret = reg_data["mfa_setup"]["secret"]
    assert totp_secret is not None

    # 2. Login requires MFA challenge
    login_res = client.post("/api/auth/login", json={
        "email": "mfa.user@enterprise.com",
        "password": "SecurePassword2026!"
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data.get("mfa_required") is True
    challenge_token = login_data["challenge_token"]
    assert challenge_token is not None

    # 3. Invalid code rejected
    bad_verify = client.post("/api/auth/mfa/verify", json={
        "challenge_token": challenge_token,
        "otp_code": "000000"
    })
    assert bad_verify.status_code == 401

    # 4. Valid TOTP code succeeds
    valid_code = pyotp.TOTP(totp_secret).now()
    good_verify = client.post("/api/auth/mfa/verify", json={
        "challenge_token": challenge_token,
        "otp_code": valid_code
    })
    assert good_verify.status_code == 200
    verify_data = good_verify.json()
    assert "access_token" in verify_data
    assert verify_data["user"]["email"] == "mfa.user@enterprise.com"
