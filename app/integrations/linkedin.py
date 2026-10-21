"""LinkedIn OAuth and text-post adapter.

Uses the versioned REST Posts API for text posts. Media upload flows are intentionally
not claimed as supported yet; they need LinkedIn asset upload registration and media
URNs before publishing an image or video.
"""
import os
import uuid
import urllib.parse
import httpx
from typing import Optional
from app.integrations.base import (
    BaseSocialAdapter, ConnectionRecord, PlatformPublishResult, PlatformMetricsResult, now_iso
)
from app.integrations.crypto import encrypt_token, decrypt_token


class LinkedInAdapter(BaseSocialAdapter):
    platform_name = "linkedin"

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id or os.getenv("LINKEDIN_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("LINKEDIN_CLIENT_SECRET", "")
        self.auth_url = "https://www.linkedin.com/oauth/v2/authorization"
        self.token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        self.api_base = "https://api.linkedin.com/rest"
        self.api_version = os.getenv("LINKEDIN_API_VERSION", "202601")

    def connect_url(self, tenant_id: str, scopes: list[str], redirect_uri: str, state: str) -> str:
        effective_scopes = " ".join(scopes or ["w_member_social", "openid", "profile", "email"])
        params = {
            "response_type": "code", "client_id": self.client_id,
            "redirect_uri": redirect_uri, "state": state, "scope": effective_scopes
        }
        return f"{self.auth_url}?{urllib.parse.urlencode(params)}"

    async def handle_oauth_callback(self, code: str, redirect_uri: str, state: str, tenant_id: str) -> ConnectionRecord:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                self.token_url,
                data={
                    "grant_type": "authorization_code", "code": code,
                    "redirect_uri": redirect_uri, "client_id": self.client_id,
                    "client_secret": self.client_secret
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            resp.raise_for_status()
            data = resp.json()
        access_token = data["access_token"]
        expires_in = data.get("expires_in", 5184000)
        import datetime
        expiry = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expires_in)).isoformat()
        return ConnectionRecord(
            connection_id=f"conn_li_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id, platform="linkedin", account_name="LinkedIn Account",
            encrypted_access_token=encrypt_token(access_token),
            encrypted_refresh_token=encrypt_token(data["refresh_token"]) if data.get("refresh_token") else None,
            expires_at=expiry, scopes=data.get("scope", "").split(" "), is_active=True
        )

    async def refresh_credentials(self, connection: ConnectionRecord) -> ConnectionRecord:
        if not connection.encrypted_refresh_token:
            return connection
        refresh_token = decrypt_token(connection.encrypted_refresh_token)
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                self.token_url,
                data={
                    "grant_type": "refresh_token", "refresh_token": refresh_token,
                    "client_id": self.client_id, "client_secret": self.client_secret
                },
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
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.api_base}/userinfo",
                    headers={
                        "Authorization": f"Bearer {decrypt_token(connection.encrypted_access_token)}",
                        "Linkedin-Version": self.api_version,
                        "X-Restli-Protocol-Version": "2.0.0"
                    }
                )
                return response.status_code == 200
        except Exception:
            return False

    async def publish_draft(self, connection: ConnectionRecord, copy: str, media_urls: list[str], idempotency_key: str) -> PlatformPublishResult:
        if not connection.is_active:
            return PlatformPublishResult(success=False, platform="linkedin", idempotency_key=idempotency_key, error_message="Connection is inactive or revoked.")
        if media_urls:
            return PlatformPublishResult(
                success=False, platform="linkedin", idempotency_key=idempotency_key,
                error_message="LinkedIn media posting is not implemented yet; upload media and resolve an approved media URN first."
            )
        token = decrypt_token(connection.encrypted_access_token)
        headers = {
            "Authorization": f"Bearer {token}", "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0", "Linkedin-Version": self.api_version
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                profile_response = await client.get(
                    f"{self.api_base}/userinfo",
                    headers=headers
                )
                if profile_response.status_code != 200:
                    return PlatformPublishResult(success=False, platform="linkedin", idempotency_key=idempotency_key, error_message=f"LinkedIn profile verification failed ({profile_response.status_code}).")
                person_id = profile_response.json().get("sub")
                if not person_id:
                    return PlatformPublishResult(success=False, platform="linkedin", idempotency_key=idempotency_key, error_message="LinkedIn userinfo returned no member identifier.")
                response = await client.post(
                    f"{self.api_base}/posts",
                    headers=headers,
                    json={
                        "author": f"urn:li:person:{person_id}",
                        "commentary": copy,
                        "visibility": "PUBLIC",
                        "distribution": {
                            "feedDistribution": "MAIN_FEED",
                            "targetEntities": [],
                            "thirdPartyDistributionChannels": []
                        },
                        "lifecycleState": "PUBLISHED",
                        "isReshareDisabledByAuthor": False
                    }
                )
                if response.status_code in (200, 201):
                    post_id = response.headers.get("x-restli-id")
                    if not post_id:
                        return PlatformPublishResult(success=False, platform="linkedin", idempotency_key=idempotency_key, error_message="LinkedIn accepted the request but no post ID was returned; reconcile before retrying.")
                    return PlatformPublishResult(success=True, platform="linkedin", external_post_id=post_id, idempotency_key=idempotency_key)
                return PlatformPublishResult(success=False, platform="linkedin", idempotency_key=idempotency_key, error_message=f"LinkedIn API error {response.status_code}: {response.text[:500]}")
        except Exception as exc:
            return PlatformPublishResult(success=False, platform="linkedin", idempotency_key=idempotency_key, error_message=f"{type(exc).__name__}: {exc}")

    async def fetch_metrics(self, connection: ConnectionRecord, post_ids: list[str], date_range_days: int = 7) -> list[PlatformMetricsResult]:
        # LinkedIn metrics require platform/product permissions and the corresponding
        # author/organization-specific analytics endpoint. Do not return fake data.
        return [
            PlatformMetricsResult(platform="linkedin", post_id=post_id, is_live_data=False)
            for post_id in post_ids
        ]

    async def disconnect(self, connection: ConnectionRecord) -> bool:
        connection.is_active = False
        connection.updated_at = now_iso()
        return True
