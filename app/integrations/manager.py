"""Platform adapter registry with tenant-scoped persistent connections."""
from typing import Optional
from app.integrations.base import BaseSocialAdapter, ConnectionRecord, PlatformPublishResult, PlatformMetricsResult
from app.integrations.linkedin import LinkedInAdapter
from app.integrations.twitter import TwitterAdapter
from app.integrations.crypto import decrypt_token
from app.db.migrations import run_migrations
import os
import json
import sqlite3
import uuid
import datetime


class PlatformManager:
    """Load persisted, encrypted OAuth connections from the configured database."""

    def __init__(self, db_path_getter=None):
        self._db_path_getter = db_path_getter or (lambda: os.getenv("DATABASE_PATH", "./agent_runs.db"))
        self._adapters: dict[str, BaseSocialAdapter] = {
            "linkedin": LinkedInAdapter(),
            "twitter": TwitterAdapter(),
            "x": TwitterAdapter()
        }
        self._connections: dict[str, ConnectionRecord] = {}

    def _db(self):
        path = self._db_path_getter()
        run_migrations(path)
        con = sqlite3.connect(path)
        con.row_factory = sqlite3.Row
        return con

    def get_adapter(self, platform: str) -> Optional[BaseSocialAdapter]:
        return self._adapters.get(platform.lower())

    def save_connection(self, connection: ConnectionRecord) -> None:
        """Persist encrypted connection and refresh in-memory cache."""
        with self._db() as con:
            con.execute(
                """INSERT INTO connections
                   (id, created_at, updated_at, tenant_id, platform, account_name,
                    encrypted_access_token, encrypted_refresh_token, expires_at, scopes_json, is_active)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET
                    updated_at=excluded.updated_at,
                    account_name=excluded.account_name,
                    encrypted_access_token=excluded.encrypted_access_token,
                    encrypted_refresh_token=excluded.encrypted_refresh_token,
                    expires_at=excluded.expires_at,
                    scopes_json=excluded.scopes_json,
                    is_active=excluded.is_active""",
                (connection.connection_id, connection.created_at, connection.updated_at,
                 connection.tenant_id, connection.platform, connection.account_name,
                 connection.encrypted_access_token, connection.encrypted_refresh_token,
                 connection.expires_at, json.dumps(connection.scopes), int(connection.is_active))
            )
        self._connections[connection.connection_id] = connection

    def register_connection(self, connection: ConnectionRecord):
        """Compatibility alias; connection is stored durably."""
        self.save_connection(connection)

    def get_connection(self, connection_id: str, tenant_id: Optional[str] = None) -> Optional[ConnectionRecord]:
        """Read one connection from durable storage, scoped to a tenant when supplied."""
        with self._db() as con:
            if tenant_id is None:
                row = con.execute("SELECT * FROM connections WHERE id=?", (connection_id,)).fetchone()
            else:
                row = con.execute("SELECT * FROM connections WHERE id=? AND tenant_id=?", (connection_id, tenant_id)).fetchone()
        if not row:
            return None
        return ConnectionRecord(
            connection_id=row["id"], tenant_id=row["tenant_id"], platform=row["platform"],
            account_name=row["account_name"], encrypted_access_token=row["encrypted_access_token"],
            encrypted_refresh_token=row["encrypted_refresh_token"], expires_at=row["expires_at"],
            scopes=json.loads(row["scopes_json"] or "[]"), is_active=bool(row["is_active"]),
            created_at=row["created_at"], updated_at=row["updated_at"]
        )

    def list_connections(self, tenant_id: str = "default") -> list[ConnectionRecord]:
        """Read active connections belonging to one tenant."""
        with self._db() as con:
            rows = con.execute(
                "SELECT * FROM connections WHERE tenant_id=? AND is_active=1 ORDER BY created_at DESC",
                (tenant_id,)
            ).fetchall()
        return [ConnectionRecord(
            connection_id=row["id"], tenant_id=row["tenant_id"], platform=row["platform"],
            account_name=row["account_name"], encrypted_access_token=row["encrypted_access_token"],
            encrypted_refresh_token=row["encrypted_refresh_token"], expires_at=row["expires_at"],
            scopes=json.loads(row["scopes_json"] or "[]"), is_active=bool(row["is_active"]),
            created_at=row["created_at"], updated_at=row["updated_at"]
        ) for row in rows]

    async def publish(
        self, platform: str, connection_id: str, copy: str,
        idempotency_key: str, media_urls: Optional[list[str]] = None,
        tenant_id: Optional[str] = None
    ) -> PlatformPublishResult:
        adapter = self.get_adapter(platform)
        if not adapter:
            return PlatformPublishResult(success=False, platform=platform,
                idempotency_key=idempotency_key, error_message=f"No supported official adapter for platform '{platform}'.")
        conn = self.get_connection(connection_id, tenant_id=tenant_id)
        expected_platform = "twitter" if platform.lower() == "x" else platform.lower()
        if not conn or not conn.is_active or conn.platform.lower() != expected_platform:
            return PlatformPublishResult(success=False, platform=platform,
                idempotency_key=idempotency_key, error_message="Active connection for this tenant and platform not found.")
        return await adapter.publish_draft(connection=conn, copy=copy, media_urls=media_urls or [], idempotency_key=idempotency_key)

    async def fetch_metrics(self, platform: str, connection_id: str, post_ids: list[str], tenant_id: Optional[str] = None) -> list[PlatformMetricsResult]:
        adapter = self.get_adapter(platform)
        conn = self.get_connection(connection_id, tenant_id=tenant_id)
        if not adapter or not conn or not conn.is_active:
            return []
        return await adapter.fetch_metrics(connection=conn, post_ids=post_ids)


platform_manager = PlatformManager()
