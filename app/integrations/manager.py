"""Persistent tenant-scoped adapter manager with safe publishing idempotency."""
from typing import Optional
import os
import json
import sqlite3
import datetime
from app.integrations.base import BaseSocialAdapter, ConnectionRecord, PlatformPublishResult, PlatformMetricsResult, now_iso
from app.integrations.linkedin import LinkedInAdapter
from app.integrations.twitter import TwitterAdapter
from app.integrations.instagram import InstagramAdapter
from app.db.migrations import run_migrations


class PlatformManager:
    def __init__(self, db_path_getter=None):
        self._db_path_getter = db_path_getter or (lambda: os.getenv("DATABASE_PATH", "./agent_runs.db"))
        self._adapters: dict[str, BaseSocialAdapter] = {
            "linkedin": LinkedInAdapter(),
            "twitter": TwitterAdapter(),
            "x": TwitterAdapter(),
            "instagram": InstagramAdapter(),
        }

    def _db(self):
        path = self._db_path_getter()
        run_migrations(path)
        con = sqlite3.connect(path, timeout=10)
        con.row_factory = sqlite3.Row
        return con

    def get_adapter(self, platform: str) -> Optional[BaseSocialAdapter]:
        return self._adapters.get(platform.lower())

    @staticmethod
    def _from_row(row) -> ConnectionRecord:
        return ConnectionRecord(
            connection_id=row["id"], tenant_id=row["tenant_id"], platform=row["platform"],
            account_name=row["account_name"], encrypted_access_token=row["encrypted_access_token"],
            encrypted_refresh_token=row["encrypted_refresh_token"], expires_at=row["expires_at"],
            scopes=json.loads(row["scopes_json"] or "[]"), is_active=bool(row["is_active"]),
            created_at=row["created_at"], updated_at=row["updated_at"],
        )

    def save_connection(self, connection: ConnectionRecord) -> None:
        with self._db() as con:
            con.execute(
                """INSERT INTO connections
                   (id, created_at, updated_at, tenant_id, platform, account_name,
                    encrypted_access_token, encrypted_refresh_token, expires_at, scopes_json, is_active)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET
                     updated_at=excluded.updated_at, account_name=excluded.account_name,
                     encrypted_access_token=excluded.encrypted_access_token,
                     encrypted_refresh_token=excluded.encrypted_refresh_token,
                     expires_at=excluded.expires_at, scopes_json=excluded.scopes_json,
                     is_active=excluded.is_active
                   WHERE connections.tenant_id=excluded.tenant_id
                     AND connections.platform=excluded.platform""",
                (connection.connection_id, connection.created_at, connection.updated_at,
                 connection.tenant_id, connection.platform, connection.account_name,
                 connection.encrypted_access_token, connection.encrypted_refresh_token,
                 connection.expires_at, json.dumps(connection.scopes), int(connection.is_active)),
            )
            stored = con.execute("SELECT tenant_id, platform FROM connections WHERE id=?", (connection.connection_id,)).fetchone()
            if not stored or stored["tenant_id"] != connection.tenant_id or stored["platform"] != connection.platform:
                raise ValueError("Connection ID already belongs to a different tenant or platform.")

    def register_connection(self, connection: ConnectionRecord) -> None:
        """Compatibility alias; always persists the connection."""
        self.save_connection(connection)

    def get_connection(self, connection_id: str, tenant_id: Optional[str] = None) -> Optional[ConnectionRecord]:
        if not tenant_id:
            return None
        with self._db() as con:
            row = con.execute(
                "SELECT * FROM connections WHERE id=? AND tenant_id=?", (connection_id, tenant_id)
            ).fetchone()
        return self._from_row(row) if row else None

    def list_connections(self, tenant_id: str = "default") -> list[ConnectionRecord]:
        with self._db() as con:
            rows = con.execute(
                "SELECT * FROM connections WHERE tenant_id=? AND is_active=1 ORDER BY created_at DESC",
                (tenant_id,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def get_connection_by_platform(self, platform: str, tenant_id: str = "default") -> Optional[ConnectionRecord]:
        norm = "twitter" if platform.lower() == "x" else platform.lower()
        with self._db() as con:
            row = con.execute(
                "SELECT * FROM connections WHERE tenant_id=? AND LOWER(platform)=? AND is_active=1 ORDER BY created_at DESC LIMIT 1",
                (tenant_id, norm),
            ).fetchone()
        return self._from_row(row) if row else None

    def delete_connection(self, platform: str, tenant_id: str = "default") -> bool:
        norm = "twitter" if platform.lower() == "x" else platform.lower()
        with self._db() as con:
            con.execute(
                "UPDATE connections SET is_active=0 WHERE tenant_id=? AND LOWER(platform)=?",
                (tenant_id, norm)
            )
        return True

    @staticmethod
    def _expiry(connection: ConnectionRecord) -> Optional[datetime.datetime]:
        if not connection.expires_at:
            return None
        try:
            expiry = datetime.datetime.fromisoformat(connection.expires_at.replace("Z", "+00:00"))
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=datetime.timezone.utc)
            return expiry
        except (TypeError, ValueError):
            # Treat malformed expiry as expired; never assume a malformed token is valid.
            return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)

    async def _refresh_if_needed(self, adapter: BaseSocialAdapter, connection: ConnectionRecord) -> Optional[str]:
        expiry = self._expiry(connection)
        now = datetime.datetime.now(datetime.timezone.utc)
        if expiry is None or expiry > now + datetime.timedelta(seconds=60):
            return None
        if not connection.encrypted_refresh_token:
            if expiry <= now:
                return "Access token has expired and this platform connection has no refresh token. Reconnect the account."
            return None
        try:
            refreshed = await adapter.refresh_credentials(connection)
            # A refresh response should establish a new expiry; do not persist a stale expiry.
            refreshed_expiry = self._expiry(refreshed)
            if not refreshed.encrypted_access_token or (refreshed_expiry and refreshed_expiry <= now):
                return "Token refresh did not return a usable access token and expiry. Reconnect the account."
            self.save_connection(refreshed)
            connection.encrypted_access_token = refreshed.encrypted_access_token
            connection.encrypted_refresh_token = refreshed.encrypted_refresh_token
            connection.expires_at = refreshed.expires_at
            connection.updated_at = refreshed.updated_at
            return None
        except Exception as exc:
            return f"Token refresh failed ({type(exc).__name__}). Reconnect the account if the issue persists."

    async def publish(self, platform: str, connection_id: str, copy: str,
                      idempotency_key: str, media_urls: Optional[list[str]] = None,
                      tenant_id: Optional[str] = None) -> PlatformPublishResult:
        normalized_platform = "twitter" if platform.lower() == "x" else platform.lower()
        if not tenant_id:
            return PlatformPublishResult(
                success=False, platform=platform, idempotency_key=idempotency_key,
                error_message="Tenant ID is required for safe publishing.",
            )
        if not idempotency_key or not idempotency_key.strip():
            return PlatformPublishResult(
                success=False, platform=platform, idempotency_key=idempotency_key or "",
                error_message="A non-empty idempotency key is required.",
            )
        adapter = self.get_adapter(platform)
        if not adapter:
            return PlatformPublishResult(
                success=False, platform=platform, idempotency_key=idempotency_key,
                error_message=f"No supported official adapter for platform '{platform}'.",
            )
        conn = self.get_connection(connection_id, tenant_id=tenant_id)
        if not conn or not conn.is_active or conn.platform.lower() != normalized_platform:
            return PlatformPublishResult(
                success=False, platform=platform, idempotency_key=idempotency_key,
                error_message="Active connection for this tenant and platform not found.",
            )

        # Reserve atomically before contacting an external API. Existing keys are never
        # resent: a process may have crashed after the platform accepted the post.
        now = now_iso()
        with self._db() as con:
            existing = con.execute(
                "SELECT status, result_json FROM publish_idempotency WHERE tenant_id=? AND platform=? AND idempotency_key=?",
                (tenant_id, normalized_platform, idempotency_key),
            ).fetchone()
            if existing:
                if existing["status"] == "succeeded" and existing["result_json"]:
                    return PlatformPublishResult.model_validate(json.loads(existing["result_json"]))
                return PlatformPublishResult(
                    success=False, platform=platform, idempotency_key=idempotency_key,
                    error_message=f"A prior publish attempt is recorded as '{existing['status']}'. It was not resent to prevent duplicate posts; reconcile the platform account before retrying with a new key.",
                )
            try:
                con.execute(
                    "INSERT INTO publish_idempotency(tenant_id, platform, idempotency_key, status, result_json, created_at, updated_at) VALUES(?,?,?,?,?,?,?)",
                    (tenant_id, normalized_platform, idempotency_key, "in_progress", None, now, now),
                )
            except sqlite3.IntegrityError:
                return PlatformPublishResult(
                    success=False, platform=platform, idempotency_key=idempotency_key,
                    error_message="A concurrent publish is using this idempotency key; this request was not sent.",
                )

        refresh_error = await self._refresh_if_needed(adapter, conn)
        if refresh_error:
            result = PlatformPublishResult(success=False, platform=platform, idempotency_key=idempotency_key, error_message=refresh_error)
            self._store_publish_result(tenant_id, normalized_platform, idempotency_key, "failed", result)
            return result
        try:
            result = await adapter.publish_draft(
                connection=conn, copy=copy, media_urls=media_urls or [], idempotency_key=idempotency_key
            )
            # A failed adapter result may still represent an uncertain network outcome.
            # Keep the key consumed; never automatically resend the same operation.
            status = "succeeded" if result.success and result.external_post_id else "failed"
            self._store_publish_result(tenant_id, normalized_platform, idempotency_key, status, result)
            return result
        except Exception as exc:
            result = PlatformPublishResult(
                success=False, platform=platform, idempotency_key=idempotency_key,
                error_message=f"Publish outcome is uncertain ({type(exc).__name__}); it was not automatically retried to avoid duplicates.",
            )
            self._store_publish_result(tenant_id, normalized_platform, idempotency_key, "unknown", result)
            return result

    def _store_publish_result(self, tenant_id: str, platform: str, idempotency_key: str,
                              status: str, result: PlatformPublishResult) -> None:
        with self._db() as con:
            con.execute(
                "UPDATE publish_idempotency SET status=?, result_json=?, updated_at=? WHERE tenant_id=? AND platform=? AND idempotency_key=?",
                (status, result.model_dump_json(), now_iso(), tenant_id, platform, idempotency_key),
            )

    async def fetch_metrics(self, platform: str, connection_id: str, post_ids: list[str],
                            tenant_id: Optional[str] = None) -> list[PlatformMetricsResult]:
        adapter = self.get_adapter(platform)
        conn = self.get_connection(connection_id, tenant_id=tenant_id)
        if not adapter or not conn or not conn.is_active:
            return []
        return await adapter.fetch_metrics(connection=conn, post_ids=post_ids)


platform_manager = PlatformManager()
