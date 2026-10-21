import os
import uuid
import urllib.parse
import secrets
import hashlib
import base64
import json
import sqlite3
import datetime
from app.db.migrations import run_migrations
import httpx
from typing import Optional
from app.integrations.base import (
    BaseSocialAdapter, ConnectionRecord, PlatformPublishResult, PlatformMetricsResult, now_iso
)
from app.integrations.crypto import encrypt_token, decrypt_token


class TwitterAdapter(BaseSocialAdapter):
    platform_name = "twitter"

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id or os.getenv("TWITTER_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("TWITTER_CLIENT_SECRET", "")
        self.auth_url = "https://twitter.com/i/oauth2/authorize"
        self.token_url = "https://api.twitter.com/2/oauth2/token"
        self.api_base = "https://api.twitter.com/2"
        # OAuth PKCE values must be generated per attempt and stored server-side.
        self._pending_pkce: dict[str, str] = {}
        self._db_path_getter = lambda: os.getenv("DATABASE_PATH", "./agent_runs.db")

    def connect_url(self, tenant_id: str, scopes: list[str], redirect_uri: str, state: str, pkce_verifier: Optional[str] = None) -> str:
        verifier = pkce_verifier or secrets.token_urlsafe(64)[:96]
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        # The caller persists the verifier encrypted alongside the one-time OAuth state.
        self._pending_pkce[state] = verifier
        effective_scopes = " ".join(scopes or ["tweet.read", "tweet.write", "users.read", "offline.access"])
        params = {
            "response_type": "code", "client_id": self.client_id,
            "redirect_uri": redirect_uri, "scope": effective_scopes, "state": state,
            "code_challenge": challenge, "code_challenge_method": "S256"
        }
        return f"{self.auth_url}?{urllib.parse.urlencode(params)}"

    async def handle_oauth_callback(self, code: str, redirect_uri: str, state: str, tenant_id: str, pkce_verifier: Optional[str] = None) -> ConnectionRecord:
        verifier = pkce_verifier or self._pending_pkce.pop(state, None)
        if not verifier:
            db_path = self._db_path_getter()
            run_migrations(db_path)
            with sqlite3.connect(db_path) as con:
                con.row_factory = sqlite3.Row
                row = con.execute("SELECT verifier_encrypted, created_at FROM oauth_pkce WHERE state=?", (state,)).fetchone()
                con.execute("DELETE FROM oauth_pkce WHERE state=?", (state,))
            if row:
                created = datetime.datetime.fromisoformat(row["created_at"])
                if (datetime.datetime.now(datetime.timezone.utc) - created).total_seconds() > 600:
                    raise ValueError("OAuth PKCE verifier expired. Restart account connection.")
                verifier = decrypt_token(row["verifier_encrypted"])
        if not verifier:
            raise ValueError("OAuth PKCE verifier missing or expired. Restart account connection.")
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                self.token_url,
                data={
                    "code": code,
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "redirect_uri": redirect_uri,
                    "code_verifier": verifier
                },
                auth=(self.client_id, self.client_secret) if self.client_secret else None,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            resp.raise_for_status()
            data = resp.json()

        access_token = data["access_token"]
        refresh_token = data.get("refresh_token")
        expires_in = data.get("expires_in", 7200)
        import datetime
        expiry = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expires_in)).isoformat()
        return ConnectionRecord(
            connection_id=f"conn_tw_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            platform="twitter",
            account_name="X / Twitter Account",
            encrypted_access_token=encrypt_token(access_token),
            encrypted_refresh_token=encrypt_token(refresh_token) if refresh_token else None,
            expires_at=expiry,
            scopes=data.get("scope", "").split(" "),
            is_active=True
        )

    async def refresh_credentials(self, connection: ConnectionRecord) -> ConnectionRecord:
        if not connection.encrypted_refresh_token:
            return connection
        refresh_token = decrypt_token(connection.encrypted_refresh_token)
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                self.token_url,
                data={"grant_type": "refresh_token", "refresh_token": refresh_token, "client_id": self.client_id},
                auth=(self.client_id, self.client_secret) if self.client_secret else None,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            resp.raise_for_status()
            data = resp.json()
        connection.encrypted_access_token = encrypt_token(data["access_token"])
        if data.get("refresh_token"):
            connection.encrypted_refresh_token = encrypt_token(data["refresh_token"])
        connection.updated_at = now_iso()
        return connection

    async def validate_connection(self, connection: ConnectionRecord) -> bool:
        if not connection.encrypted_access_token:
            return False
        token = decrypt_token(connection.encrypted_access_token)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.api_base}/users/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                return response.status_code == 200
        except Exception:
            return False

    async def publish_draft(self, connection: ConnectionRecord, copy: str, media_urls: list[str], idempotency_key: str) -> PlatformPublishResult:
        if not connection.is_active:
            return PlatformPublishResult(success=False, platform="twitter", idempotency_key=idempotency_key, error_message="Connection is inactive or revoked.")
        token = decrypt_token(connection.encrypted_access_token)
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {"text": copy[:280]}
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(f"{self.api_base}/tweets", headers=headers, json=payload)
                if resp.status_code in (200, 201):
                    data = resp.json().get("data", {})
                    post_id = data.get("id")
                    if not post_id:
                        return PlatformPublishResult(success=False, platform="twitter", idempotency_key=idempotency_key, error_message="API returned success without a post ID; outcome requires reconciliation.")
                    return PlatformPublishResult(success=True, platform="twitter", external_post_id=post_id, idempotency_key=idempotency_key, raw_response=data)
                return PlatformPublishResult(success=False, platform="twitter", idempotency_key=idempotency_key, error_message=f"Twitter API error {resp.status_code}: {resp.text[:500]}")
        except Exception as exc:
            return PlatformPublishResult(success=False, platform="twitter", idempotency_key=idempotency_key, error_message=f"{type(exc).__name__}: {exc}")

    async def fetch_metrics(self, connection: ConnectionRecord, post_ids: list[str], date_range_days: int = 7) -> list[PlatformMetricsResult]:
        results = []
        token = decrypt_token(connection.encrypted_access_token)
        async with httpx.AsyncClient(timeout=10.0) as client:
            for post_id in post_ids:
                try:
                    resp = await client.get(
                        f"{self.api_base}/tweets",
                        params={"ids": post_id, "tweet.fields": "public_metrics"},
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    if resp.status_code == 200 and resp.json().get("data"):
                        data = resp.json()["data"][0]
                        metrics = data.get("public_metrics", {})
                        results.append(PlatformMetricsResult(
                            platform="twitter", post_id=post_id,
                            likes=metrics.get("like_count", 0),
                            shares=metrics.get("retweet_count", 0),
                            comments=metrics.get("reply_count", 0),
                            is_live_data=True
                        ))
                    else:
                        results.append(PlatformMetricsResult(platform="twitter", post_id=post_id, is_live_data=False))
                except Exception:
                    results.append(PlatformMetricsResult(platform="twitter", post_id=post_id, is_live_data=False))
        return results

    async def disconnect(self, connection: ConnectionRecord) -> bool:
        connection.is_active = False
        connection.updated_at = now_iso()
        return True
