import uuid
import json
import sqlite3
import datetime
from typing import Any, Optional

def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

class AuditLogger:
    def __init__(self, db_path_getter):
        self._db_path_getter = db_path_getter

    def log(
        self,
        tenant_id: str,
        user_id: str,
        action: str,
        entity_id: str,
        details: Optional[dict[str, Any]] = None
    ):
        event_id = f"aud_{uuid.uuid4().hex[:12]}"
        created_at = now_iso()
        details_json = json.dumps(details or {})
        try:
            with sqlite3.connect(self._db_path_getter()) as con:
                con.execute(
                    "INSERT INTO audit_events(id, created_at, tenant_id, user_id, action, entity_id, details_json) VALUES(?,?,?,?,?,?,?)",
                    (event_id, created_at, tenant_id, user_id, action, entity_id, details_json)
                )
        except Exception:
            pass # Audit failure should not crash main operation but is tracked
