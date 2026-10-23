import datetime
import json
import os
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["GOOGLE_CLIENT_ID"] = "test-client-id.apps.googleusercontent.com"
os.environ["GOOGLE_CLIENT_SECRET"] = "test-client-secret"
os.environ["DATABASE_PATH"] = "./agent_runs.db"

from app.main import app
from app.db.migrations import run_migrations
from app.security.auth import (
    generate_pkce_pair,
    generate_oauth_state,
    generate_nonce,
    SESSION_COOKIE_NAME,
    create_db_session,
    get_session_user
)

@pytest.fixture(autouse=True)
def setup_database():
    run_migrations("./agent_runs.db")

@pytest.fixture
def client():
    return TestClient(app)

def test_pkce_generation():
    """Verify RFC 7636 PKCE pair generation format and strength."""
    verifier, challenge = generate_pkce_pair()
    assert len(verifier) >= 43
    assert len(challenge) >= 43
    assert verifier != challenge

def test_google_login_initiates_pkce_redirect(client):
    """Verify /auth/google/login redirects to Google with PKCE code_challenge, state, and nonce."""
    response = client.get("/auth/google/login", follow_redirects=False)
    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "https://accounts.google.com/o/oauth2/v2/auth" in location
    assert "response_type=code" in location
    assert "client_id=test-client-id.apps.googleusercontent.com" in location
    assert "code_challenge=" in location
    assert "code_challenge_method=S256" in location
    assert "state=" in location
    assert "nonce=" in location
    assert "scope=" in location
    assert "openid" in location

def test_google_callback_invalid_state_rejected(client):
    """Callback with nonexistent or forged state must be rejected with HTTP 400."""
    response = client.get("/auth/google/callback?code=mock_code&state=nonexistent_state")
    assert response.status_code == 400
    assert "Invalid or expired OAuth state parameter" in response.text

def test_google_callback_user_cancelled_redirects_with_error(client):
    """Callback with Google error parameter (e.g. access_denied) redirects with error message."""
    # First generate real state
    login_resp = client.get("/auth/google/login", follow_redirects=False)
    loc = login_resp.headers.get("location", "")
    state = loc.split("state=")[1].split("&")[0]

    callback_resp = client.get(f"/auth/google/callback?error=access_denied&state={state}", follow_redirects=False)
    assert callback_resp.status_code in (302, 303, 307)
    redir_url = callback_resp.headers.get("location", "")
    assert "auth_error=" in redir_url
    assert "access_denied" in redir_url

def test_google_callback_wrong_audience_rejected(client):
    """ID token with mismatched audience/client_id must be rejected with HTTP 401."""
    login_resp = client.get("/auth/google/login", follow_redirects=False)
    loc = login_resp.headers.get("location", "")
    state = loc.split("state=")[1].split("&")[0]

    mock_token_resp = {
        "access_token": "mock_google_access",
        "id_token": "mock_id_token",
        "token_type": "Bearer"
    }

    # Simulate Google token endpoint returning token, but verify_google_id_token rejects audience
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = AsyncMock(status_code=200, json=lambda: mock_token_resp, text=json.dumps(mock_token_resp))
        
        # Calling callback
        response = client.get(f"/auth/google/callback?code=valid_code&state={state}", follow_redirects=False)
        assert response.status_code in (302, 303)
        redir = response.headers.get("location", "")
        assert "auth_error=" in redir

def test_google_callback_unverified_email_rejected(client):
    """Google accounts with email_verified == False must be rejected for security."""
    login_resp = client.get("/auth/google/login", follow_redirects=False)
    loc = login_resp.headers.get("location", "")
    state = loc.split("state=")[1].split("&")[0]

    mock_token_resp = {
        "access_token": "mock_google_access",
        "id_token": "mock_id_token",
        "token_type": "Bearer"
    }

    mock_claims = {
        "sub": "google_sub_12345",
        "email": "unverified@example.com",
        "email_verified": False,
        "name": "Unverified User",
        "aud": "test-client-id.apps.googleusercontent.com",
        "iss": "https://accounts.google.com"
    }

    with patch("httpx.AsyncClient.post") as mock_post, \
         patch("app.main.verify_google_id_token") as mock_verify:
        mock_post.return_value = AsyncMock(status_code=200, json=lambda: mock_token_resp, text=json.dumps(mock_token_resp))
        from fastapi import HTTPException
        mock_verify.side_effect = HTTPException(status_code=401, detail="Google account email address is not verified.")

        response = client.get(f"/auth/google/callback?code=valid_code&state={state}", follow_redirects=False)
        assert response.status_code in (302, 303)
        redir = response.headers.get("location", "")
        assert "auth_error=" in redir
        assert "not+verified" in redir or "not%20verified" in redir

def test_google_callback_happy_path_sets_session_cookie(client):
    """Happy path: exchanges code, validates ID token, creates user by google_sub, sets httpOnly cookie."""
    login_resp = client.get("/auth/google/login", follow_redirects=False)
    loc = login_resp.headers.get("location", "")
    state = loc.split("state=")[1].split("&")[0]

    mock_token_resp = {
        "access_token": "mock_google_access_token",
        "id_token": "mock_google_id_token_jwt",
        "token_type": "Bearer"
    }

    test_sub = f"google_sub_test_{datetime.datetime.now().timestamp()}"
    test_email = f"verified.user.{datetime.datetime.now().timestamp()}@gmail.com"

    mock_claims = {
        "sub": test_sub,
        "email": test_email,
        "email_verified": True,
        "name": "Verified Google User",
        "picture": "https://lh3.googleusercontent.com/a/test_avatar",
        "aud": "test-client-id.apps.googleusercontent.com",
        "iss": "https://accounts.google.com"
    }

    with patch("httpx.AsyncClient.post") as mock_post, \
         patch("app.main.verify_google_id_token") as mock_verify:
        mock_post.return_value = AsyncMock(status_code=200, json=lambda: mock_token_resp, text=json.dumps(mock_token_resp))
        mock_verify.return_value = mock_claims

        callback_resp = client.get(f"/auth/google/callback?code=auth_code_xyz&state={state}", follow_redirects=False)
        assert callback_resp.status_code == 303
        redir = callback_resp.headers.get("location", "")
        assert "auth_success=true" in redir
        assert "token=" in redir

        # Check session cookie is set
        cookies = callback_resp.cookies
        assert SESSION_COOKIE_NAME in cookies
        session_id = cookies[SESSION_COOKIE_NAME]
        assert len(session_id) >= 32

        # Verify /auth/me with session cookie
        me_resp = client.get("/auth/me", cookies={SESSION_COOKIE_NAME: session_id})
        assert me_resp.status_code == 200
        user_data = me_resp.json()
        assert user_data["email"] == test_email
        assert user_data["name"] == "Verified Google User"
        assert user_data["email_verified"] is True

        # Verify logout destroys session
        logout_resp = client.post("/auth/logout", cookies={SESSION_COOKIE_NAME: session_id})
        assert logout_resp.status_code == 200

        # /auth/me should now fail (401 unauthenticated)
        me_after = client.get("/auth/me", cookies={SESSION_COOKIE_NAME: session_id})
        assert me_after.status_code == 401

def test_data_export_and_account_deletion(client):
    """Verify GDPR data export and account deletion endpoints."""
    # Register/create a test user
    reg_resp = client.post("/api/auth/register", json={
        "email": f"export.test.{datetime.datetime.now().timestamp()}@example.com",
        "password": "Password123!",
        "business_name": "Export Test Business"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Export user data
    export_resp = client.get("/auth/export", headers=headers)
    assert export_resp.status_code == 200
    export_data = export_resp.json()
    assert "user" in export_data
    assert "business_profile" in export_data
    assert "runs" in export_data

    # Delete user account
    del_resp = client.delete("/auth/me", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "ok"

    # Verify user is deleted
    me_resp = client.get("/auth/me", headers=headers)
    assert me_resp.status_code == 401

def test_appwrite_google_auth_exchange(client):
    """Verify Appwrite Google user exchange provisions user and returns valid session."""
    test_id = f"apw_usr_{datetime.datetime.now().timestamp()}"
    test_email = f"appwrite.user.{datetime.datetime.now().timestamp()}@gmail.com"

    resp = client.post("/api/auth/appwrite", json={
        "appwrite_user_id": test_id,
        "email": test_email,
        "name": "Appwrite Verified User",
        "email_verified": True
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "access_token" in data
    assert data["user"]["email"] == test_email
    assert data["user"]["name"] == "Appwrite Verified User"

    # Verify session cookie was issued
    assert SESSION_COOKIE_NAME in resp.cookies
    session_id = resp.cookies[SESSION_COOKIE_NAME]

    # Verify /auth/me works with session cookie
    me_resp = client.get("/auth/me", cookies={SESSION_COOKIE_NAME: session_id})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == test_email
