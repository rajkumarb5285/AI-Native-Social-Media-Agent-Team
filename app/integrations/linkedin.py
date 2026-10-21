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

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        self.client_id = client_id or os.getenv("LINKEDIN_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("LINKEDIN_CLIENT_SECRET", "")
        self.auth_url = "https://www.linkedin.com/oauth/v2/authorization"
        self.token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        self.api_base = "https://api.linkedin.com/v2"

    def connect_url(self, tenant_id: str, scopes: list[str], redirect_uri: str, state: str) -> str:
        default_scopes = ["w_member_social", "openid", "profile", "email"]
        effective_scopes = " ".join(scopes if scopes else default_scopes)
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": effective_scopes
        }
        return f"{self.auth_url}?{urllib.parse.urlencode(params)}"

    async def handle_oauth_callback(
        self, code: str, redirect_uri: str, state: str, tenant_id: str
    ) -> ConnectionRecord:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                self.token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            resp.raise_for_status()
            data = resp.json()

        access_token = data["access_token"]
        refresh_token = data.get("refresh_token")
        expires_in = data.get("expires_in", 5184000) # ~60 days default

        import datetime
        expiry = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expires_in)).isoformat()

        conn_id = f"conn_li_{uuid.uuid4().hex[:12]}"
        return ConnectionRecord(
            connection_id=conn_id,
            tenant_id=tenant_id,
            platform="linkedin",
            account_name="LinkedIn Account",
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
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            resp.raise_for_status()
            data = resp.json()

        connection.encrypted_access_token = encrypt_token(data["access_token"])
        if "refresh_token" in data:
            connection.encrypted_refresh_token = encrypt_token(data["refresh_token"])
        connection.updated_at = now_iso()
        return connection

    async def validate_connection(self, connection: ConnectionRecord) -> bool:
        if not connection.encrypted_access_token:
            return False
        token = decrypt_token(connection.encrypted_access_token)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.api_base}/userinfo",
                    headers={"Authorization": f"Bearer {token}"}
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def publish_draft(
        self,
        connection: ConnectionRecord,
        copy: str,
        media_urls: list[str],
        idempotency_key: str
    ) -> PlatformPublishResult:
        if not connection.is_active:
            return PlatformPublishResult(
                success=False,
                platform="linkedin",
                idempotency_key=idempotency_key,
                error_message="Connection is inactive or revoked."
            )

        token = decrypt_token(connection.encrypted_access_token)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "X-Idempotency-Key": idempotency_key
        }

        # LinkedIn ugcPosts payload format
        payload = {
            "author": "urn:li:person:me",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": copy},
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    f"{self.api_base}/ugcPosts",
                    headers=headers,
                    json=payload
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    post_id = data.get("id", f"li_{uuid.uuid4().hex[:10]}")
                    return PlatformPublishResult(
                        success=True,
                        platform="linkedin",
                        external_post_id=post_id,
                        idempotency_key=idempotency_key,
                        raw_response=data
                    )
                else:
                    return PlatformPublishResult(
                        success=False,
                        platform="linkedin",
                        idempotency_key=idempotency_key,
                        error_message=f"LinkedIn API error {resp.status_code}: {resp.text}"
                    )
        except Exception as e:
            return PlatformPublishResult(
                success=False,
                platform="linkedin",
                idempotency_key=idempotency_key,
                error_message=str(e)
            )

    async def fetch_metrics(
        self,
        connection: ConnectionRecord,
        post_ids: list[str],
        date_range_days: int = 7
    ) -> list[PlatformMetricsResult]:
        results = []
        token = decrypt_token(connection.encrypted_access_token)
        for pid in post_ids:
            # Query post metrics endpoint
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(
                        f"{self.api_base}/organizationalEntityShareStatistics?q=organizationalEntity&shares=List({pid})",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    if resp.status_code == 200:
                        stats = resp.json().get("elements", [{}])[0]
                        results.append(PlatformMetricsResult(
                            platform="linkedin",
                            post_id=pid,
                            impressions=stats.get("impressionCount", 0),
                            clicks=stats.get("clickCount", 0),
                            likes=stats.get("likeCount", 0),
                            shares=stats.get("shareCount", 0),
                            comments=stats.get("commentCount", 0),
                            engagement_rate=stats.get("engagement", 0.0),
                            is_live_data=True
                        ))
                    else:
                        results.append(PlatformMetricsResult(
                            platform="linkedin",
                            post_id=pid,
                            is_live_data=False
                        ))
            except Exception:
                results.append(PlatformMetricsResult(
                    platform="linkedin",
                    post_id=pid,
                    is_live_data=False
                ))
        return results

    async def disconnect(self, connection: ConnectionRecord) -> bool:
        connection.is_active = False
        connection.updated_at = now_iso()
        return True
