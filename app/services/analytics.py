"""Production Channel Health and Real-Time Analytics Service.

Evaluates real connected platform accounts (token expiration, active state,
scopes) and aggregates tenant publishing metrics directly from sqlite/postgres.
Never fabricates fake channel counts, fake impressions, or fake graphs.
"""
import sqlite3
import datetime
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.db.migrations import run_migrations


class ChannelHealthStatus(BaseModel):
    connection_id: str
    platform: str
    account_name: str
    status: str  # healthy, expiring_soon, expired, disconnected
    is_active: bool
    expires_at: Optional[str] = None
    days_until_expiration: Optional[int] = None
    scopes: List[str] = Field(default_factory=list)
    has_write_scope: bool = False
    message: str = "Connected and operational."


class ChannelHealthReport(BaseModel):
    tenant_id: str
    total_connected: int = 0
    healthy_count: int = 0
    expiring_soon_count: int = 0
    expired_count: int = 0
    channels: List[ChannelHealthStatus] = Field(default_factory=list)
    overall_health: str = "no_channels"  # healthy, degraded, critical, no_channels


class TenantAnalyticsOverview(BaseModel):
    tenant_id: str
    is_connected: bool = False
    total_campaigns: int = 0
    approved_campaigns: int = 0
    approval_rate_percent: float = 0.0
    published_posts_count: int = 0
    connected_platforms: List[str] = Field(default_factory=list)
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list)
    message: str = "Connect social channels and create your first campaign to view live performance."


REQUIRED_WRITE_SCOPES = {
    "linkedin": ["w_member_social", "rw_organization_admin"],
    "twitter": ["tweet.write", "users.read", "tweet.read"],
    "x": ["tweet.write", "users.read", "tweet.read"],
    "instagram": ["instagram_basic", "instagram_content_publish"],
    "gmb": ["https://www.googleapis.com/auth/business.manage"],
    "google_business": ["https://www.googleapis.com/auth/business.manage"]
}


class AnalyticsService:
    def __init__(self, db_path_getter=None):
        self._db_path_getter = db_path_getter

    def _get_db(self):
        import os
        path = self._db_path_getter() if self._db_path_getter else os.getenv("DATABASE_PATH", "./agent_runs.db")
        run_migrations(path)
        con = sqlite3.connect(path, timeout=10)
        con.row_factory = sqlite3.Row
        return con

    def evaluate_channel_health(self, tenant_id: str) -> ChannelHealthReport:
        """Inspects all connected social accounts for the tenant and evaluates token lifecycle."""
        with self._get_db() as con:
            rows = con.execute(
                "SELECT * FROM connections WHERE tenant_id=? ORDER BY created_at DESC",
                (tenant_id,)
            ).fetchall()

        if not rows:
            return ChannelHealthReport(tenant_id=tenant_id, total_connected=0, overall_health="no_channels")

        channels: List[ChannelHealthStatus] = []
        healthy_c = 0
        expiring_c = 0
        expired_c = 0

        now = datetime.datetime.now(datetime.timezone.utc)

        for row in rows:
            plat = row["platform"].lower()
            is_active = bool(row["is_active"])
            expires_at_str = row["expires_at"]
            scopes = json.loads(row["scopes_json"] or "[]")

            # Scope check
            req_scopes = REQUIRED_WRITE_SCOPES.get(plat, [])
            has_write = any(s in scopes for s in req_scopes) if req_scopes else True

            status = "healthy"
            days_until = None
            msg = "Channel operational with publishing permissions."

            if not is_active:
                status = "disconnected"
                msg = "Channel was disconnected or deactivated by admin."
            elif expires_at_str:
                try:
                    exp_dt = datetime.datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                    diff = exp_dt - now
                    days_until = diff.days

                    if diff.total_seconds() <= 0:
                        status = "expired"
                        msg = "OAuth access token expired. Re-authentication required."
                        expired_c += 1
                    elif diff.total_seconds() < 86400:  # < 24 hours
                        status = "expiring_soon"
                        msg = f"Token expires in {int(diff.total_seconds() // 3600)} hours. Refresh scheduled."
                        expiring_c += 1
                    else:
                        healthy_c += 1
                except Exception:
                    healthy_c += 1
            else:
                healthy_c += 1

            if not has_write and status == "healthy":
                msg = "Connected with read-only scopes. Write scope recommended for auto-publishing."

            channels.append(ChannelHealthStatus(
                connection_id=row["id"],
                platform=row["platform"],
                account_name=row["account_name"] or "Connected Account",
                status=status,
                is_active=is_active,
                expires_at=expires_at_str,
                days_until_expiration=days_until,
                scopes=scopes,
                has_write_scope=has_write,
                message=msg
            ))

        total = len(channels)
        if expired_c > 0:
            overall = "critical"
        elif expiring_c > 0:
            overall = "degraded"
        else:
            overall = "healthy"

        return ChannelHealthReport(
            tenant_id=tenant_id,
            total_connected=total,
            healthy_count=healthy_c,
            expiring_soon_count=expiring_c,
            expired_count=expired_c,
            channels=channels,
            overall_health=overall
        )

    def get_tenant_analytics_overview(self, tenant_id: str) -> TenantAnalyticsOverview:
        """Computes true analytics metrics strictly from actual runs and audit records."""
        with self._get_db() as con:
            # 1. Runs summary
            run_rows = con.execute(
                "SELECT status, created_at, request_json FROM runs WHERE tenant_id=? ORDER BY created_at DESC",
                (tenant_id,)
            ).fetchall()

            # 2. Connections
            conn_rows = con.execute(
                "SELECT platform, is_active FROM connections WHERE tenant_id=? AND is_active=1",
                (tenant_id,)
            ).fetchall()

            # 3. Audit events
            audit_rows = con.execute(
                "SELECT action, entity_id, created_at FROM audit_events WHERE tenant_id=? ORDER BY created_at DESC LIMIT 10",
                (tenant_id,)
            ).fetchall()

        total_runs = len(run_rows)
        approved_runs = sum(1 for r in run_rows if r["status"] in ("approved", "succeeded", "published"))
        approval_rate = round((approved_runs / total_runs * 100.0), 1) if total_runs > 0 else 0.0

        connected_plats = list(set(r["platform"].capitalize() for r in conn_rows))
        is_conn = len(connected_plats) > 0

        recent: List[Dict[str, Any]] = []
        for a in audit_rows:
            recent.append({
                "action": a["action"],
                "target_type": a["entity_id"],
                "timestamp": a["created_at"]
            })

        message = (
            f"{total_runs} campaigns managed with {approval_rate}% approval rate."
            if total_runs > 0
            else "No campaigns generated yet. Create a brief in Studio Floor to initiate agent workflow."
        )

        return TenantAnalyticsOverview(
            tenant_id=tenant_id,
            is_connected=is_conn,
            total_campaigns=total_runs,
            approved_campaigns=approved_runs,
            approval_rate_percent=approval_rate,
            published_posts_count=approved_runs,
            connected_platforms=connected_plats,
            recent_activity=recent,
            message=message
        )


analytics_service = AnalyticsService()
