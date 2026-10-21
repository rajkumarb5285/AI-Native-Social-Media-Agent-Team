import abc
import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field

def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

class ConnectionRecord(BaseModel):
    connection_id: str
    tenant_id: str
    platform: str
    account_name: str
    encrypted_access_token: str
    encrypted_refresh_token: Optional[str] = None
    expires_at: Optional[str] = None
    scopes: list[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

class PlatformPublishResult(BaseModel):
    success: bool
    platform: str
    external_post_id: Optional[str] = None
    idempotency_key: str
    timestamp: str = Field(default_factory=now_iso)
    error_message: Optional[str] = None
    raw_response: Optional[dict[str, Any]] = None

class PlatformMetricsResult(BaseModel):
    platform: str
    post_id: str
    impressions: int = 0
    clicks: int = 0
    likes: int = 0
    shares: int = 0
    comments: int = 0
    engagement_rate: float = 0.0
    fetched_at: str = Field(default_factory=now_iso)
    is_live_data: bool = True

class BaseSocialAdapter(abc.ABC):
    platform_name: str

    @abc.abstractmethod
    def connect_url(self, tenant_id: str, scopes: list[str], redirect_uri: str, state: str) -> str:
        """Generates the OAuth 2.0 authorization URL."""
        pass

    @abc.abstractmethod
    async def handle_oauth_callback(
        self, code: str, redirect_uri: str, state: str, tenant_id: str
    ) -> ConnectionRecord:
        """Exchanges auth code for access token and returns encrypted connection record."""
        pass

    @abc.abstractmethod
    async def refresh_credentials(self, connection: ConnectionRecord) -> ConnectionRecord:
        """Refreshes expired OAuth token with platform token endpoint."""
        pass

    @abc.abstractmethod
    async def validate_connection(self, connection: ConnectionRecord) -> bool:
        """Validates that current access token has active API access and valid scopes."""
        pass

    @abc.abstractmethod
    async def publish_draft(
        self,
        connection: ConnectionRecord,
        copy: str,
        media_urls: list[str],
        idempotency_key: str
    ) -> PlatformPublishResult:
        """Publishes post via official API endpoint with strict idempotency."""
        pass

    @abc.abstractmethod
    async def fetch_metrics(
        self,
        connection: ConnectionRecord,
        post_ids: list[str],
        date_range_days: int = 7
    ) -> list[PlatformMetricsResult]:
        """Fetches real performance analytics from official metrics endpoints."""
        pass

    @abc.abstractmethod
    async def disconnect(self, connection: ConnectionRecord) -> bool:
        """Revokes token and deactivates connection."""
        pass
