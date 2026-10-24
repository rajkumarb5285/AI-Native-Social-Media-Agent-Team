"""Phase 6: Learning Loop & Telemetry Service.

Implements Section 8.1 & Section 9 of the Poster Design Agent specification:
- Logs generation runs with brief, initial spec, final spec, critic scores, and iterations
- Records human feedback: approvals, rejections, and manual coordinate/text edits
- Provides dataset exporter for DPO/SFT model fine-tuning
"""
import sqlite3
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path


def init_poster_telemetry_table(db_path: str = "agent_runs.db"):
    """Ensures poster_training_logs table exists in SQLite database."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS poster_training_logs (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            brief_json TEXT NOT NULL,
            archetype TEXT NOT NULL,
            initial_spec_json TEXT NOT NULL,
            final_spec_json TEXT NOT NULL,
            scores_json TEXT NOT NULL,
            iterations INTEGER NOT NULL DEFAULT 0,
            critic_verdict TEXT NOT NULL,
            human_status TEXT NOT NULL DEFAULT 'pending', -- pending | approved | rejected | edited
            human_edits_json TEXT,
            tenant_id TEXT NOT NULL DEFAULT 'default'
        )""")
        con.execute("CREATE INDEX IF NOT EXISTS idx_poster_status ON poster_training_logs(human_status)")


def log_poster_generation(
    brief: Dict[str, Any],
    archetype: str,
    initial_spec: Dict[str, Any],
    final_spec: Dict[str, Any],
    scores: Dict[str, Any],
    iterations: int,
    verdict: str,
    db_path: str = "agent_runs.db",
    tenant_id: str = "default"
) -> str:
    """Logs an agent generation run for learning and quality tracking."""
    init_poster_telemetry_table(db_path)
    run_id = f"post_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(db_path) as con:
        con.execute("""
            INSERT INTO poster_training_logs (
                id, created_at, brief_json, archetype, initial_spec_json,
                final_spec_json, scores_json, iterations, critic_verdict,
                human_status, human_edits_json, tenant_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', NULL, ?)
        """, (
            run_id, now_iso, json.dumps(brief), archetype,
            json.dumps(initial_spec), json.dumps(final_spec),
            json.dumps(scores), iterations, verdict, tenant_id
        ))
    return run_id


def record_human_feedback(
    log_id: str,
    status: str,  # approved | rejected | edited
    human_edits: Optional[Dict[str, Any]] = None,
    db_path: str = "agent_runs.db"
) -> bool:
    """Records human sign-off or coordinate adjustments for the learning loop."""
    init_poster_telemetry_table(db_path)
    with sqlite3.connect(db_path) as con:
        cur = con.execute("""
            UPDATE poster_training_logs
            SET human_status = ?, human_edits_json = ?
            WHERE id = ?
        """, (status, json.dumps(human_edits or {}), log_id))
        return cur.rowcount > 0


def export_training_dataset(
    db_path: str = "agent_runs.db",
    min_score: float = 8.0,
    only_approved: bool = False
) -> List[Dict[str, Any]]:
    """Exports paired (brief -> spec) training samples for SFT or DPO."""
    init_poster_telemetry_table(db_path)
    dataset = []
    with sqlite3.connect(db_path) as con:
        con.row_factory = sqlite3.Row
        cur = con.execute("SELECT * FROM poster_training_logs ORDER BY created_at DESC")
        for row in cur.fetchall():
            scores = json.loads(row["scores_json"]) if row["scores_json"] else {}
            overall = scores.get("overall", 0.0)
            status = row["human_status"]

            if only_approved and status != "approved":
                continue
            if overall < min_score and status != "approved":
                continue

            dataset.append({
                "id": row["id"],
                "created_at": row["created_at"],
                "brief": json.loads(row["brief_json"]),
                "archetype": row["archetype"],
                "chosen_spec": json.loads(row["final_spec_json"]),
                "human_status": status,
                "overall_score": overall
            })
    return dataset
