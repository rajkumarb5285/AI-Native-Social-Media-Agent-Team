from typing import Optional
from app.integrations.base import BaseSocialAdapter, ConnectionRecord, PlatformPublishResult, PlatformMetricsResult
from app.integrations.linkedin import LinkedInAdapter
from app.integrations.twitter import TwitterAdapter

class PlatformManager:
    """Central registry and dispatcher for all official social media platform adapters."""

    def __init__(self):
        self._adapters: dict[str, BaseSocialAdapter] = {
            "linkedin": LinkedInAdapter(),
            "twitter": TwitterAdapter(),
            "x": TwitterAdapter()
        }
        # In-memory connection cache (synced with DB)
        self._connections: dict[str, ConnectionRecord] = {}

    def get_adapter(self, platform: str) -> Optional[BaseSocialAdapter]:
        return self._adapters.get(platform.lower())

    def register_connection(self, connection: ConnectionRecord):
        self._connections[connection.connection_id] = connection

    def get_connection(self, connection_id: str) -> Optional[ConnectionRecord]:
        return self._connections.get(connection_id)

    def list_connections(self, tenant_id: str = "default") -> list[ConnectionRecord]:
        return [c for c in self._connections.values() if c.tenant_id == tenant_id and c.is_active]

    async def publish(
        self,
        platform: str,
        connection_id: str,
        copy: str,
        idempotency_key: str,
        media_urls: Optional[list[str]] = None
    ) -> PlatformPublishResult:
        adapter = self.get_adapter(platform)
        if not adapter:
            return PlatformPublishResult(
                success=False,
                platform=platform,
                idempotency_key=idempotency_key,
                error_message=f"No supported official adapter for platform '{platform}'."
            )
        
        conn = self.get_connection(connection_id)
        if not conn or not conn.is_active:
            return PlatformPublishResult(
                success=False,
                platform=platform,
                idempotency_key=idempotency_key,
                error_message="Active verified connection not found for this platform."
            )

        return await adapter.publish_draft(
            connection=conn,
            copy=copy,
            media_urls=media_urls or [],
            idempotency_key=idempotency_key
        )

    async def fetch_metrics(
        self,
        platform: str,
        connection_id: str,
        post_ids: list[str]
    ) -> list[PlatformMetricsResult]:
        adapter = self.get_adapter(platform)
        if not adapter:
            return []
        conn = self.get_connection(connection_id)
        if not conn or not conn.is_active:
            return []
        return await adapter.fetch_metrics(connection=conn, post_ids=post_ids)

platform_manager = PlatformManager()
