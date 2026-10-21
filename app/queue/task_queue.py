import asyncio
import json
import sqlite3
import datetime
import os
from typing import Any, Optional
from app.queue.broadcaster import broadcaster
from app.agents.graph import AgentGraph

def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

class DurableTaskQueue:
    """Persistent task queue managing background execution, cancellation, retries, and real-time broadcasts."""

    def __init__(self, db_path_getter):
        self._db_path_getter = db_path_getter
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._graph = AgentGraph()
        self._running = False

    def _db(self):
        con = sqlite3.connect(self._db_path_getter())
        con.row_factory = sqlite3.Row
        return con

    def start(self):
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._worker_loop())

    async def stop(self):
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    async def enqueue(self, run_id: str):
        # Update run status to queued
        with self._db() as con:
            con.execute("UPDATE runs SET status='queued', updated_at=? WHERE id=?", (now_iso(), run_id))
        await broadcaster.broadcast(run_id, "status_change", {"status": "queued", "message": "Run queued for worker execution."})
        await self._queue.put(run_id)

    async def cancel(self, run_id: str) -> bool:
        with self._db() as con:
            row = con.execute("SELECT status FROM runs WHERE id=?", (run_id,)).fetchone()
            if not row:
                return False
            if row["status"] in ("approved", "succeeded", "failed", "cancelled"):
                return False
            con.execute("UPDATE runs SET status='cancelled', updated_at=? WHERE id=?", (now_iso(), run_id))
        
        await broadcaster.broadcast(run_id, "status_change", {
            "status": "cancelled",
            "message": "Workflow run was cancelled by user request."
        })
        return True

    async def retry(self, run_id: str) -> bool:
        with self._db() as con:
            row = con.execute("SELECT status, retry_count FROM runs WHERE id=?", (run_id,)).fetchone()
            if not row:
                return False
            if row["status"] not in ("failed", "cancelled"):
                return False
            new_retry = (row["retry_count"] or 0) + 1
            con.execute("UPDATE runs SET status='queued', retry_count=?, updated_at=? WHERE id=?", (new_retry, now_iso(), run_id))
        
        await broadcaster.broadcast(run_id, "status_change", {
            "status": "queued",
            "retry_count": new_retry,
            "message": f"Run re-queued (retry attempt #{new_retry})."
        })
        await self._queue.put(run_id)
        return True

    def _is_cancelled(self, run_id: str) -> bool:
        with self._db() as con:
            row = con.execute("SELECT status FROM runs WHERE id=?", (run_id,)).fetchone()
            return bool(row and row["status"] == "cancelled")

    async def _worker_loop(self):
        while self._running:
            try:
                run_id = await self._queue.get()
                try:
                    await self._process_run(run_id)
                finally:
                    self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                await asyncio.sleep(0.5)

    async def _process_run(self, run_id: str):
        if self._is_cancelled(run_id):
            return

        with self._db() as con:
            row = con.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            if not row:
                return
            req_data = json.loads(row["request_json"])
            current_logs = json.loads(row["logs_json"]) if row["logs_json"] else []

        # Mark running
        with self._db() as con:
            con.execute("UPDATE runs SET status='running', updated_at=? WHERE id=?", (now_iso(), run_id))
        await broadcaster.broadcast(run_id, "status_change", {"status": "running"})

        def append_log(agent_name: str, message: str, status: str = "completed"):
            entry = {"time": now_iso(), "agent": agent_name, "message": message, "status": status}
            current_logs.append(entry)
            with self._db() as con:
                con.execute("UPDATE runs SET logs_json=?, updated_at=? WHERE id=?",
                            (json.dumps(current_logs), now_iso(), run_id))
            asyncio.create_task(broadcaster.broadcast(run_id, "log", entry))

        try:
            append_log("Orchestrator", "Task worker started pipeline execution.", "started")

            if self._is_cancelled(run_id):
                append_log("Orchestrator", "Workflow execution halted due to cancellation.", "failed")
                return

            # Execute pipeline
            execution = await self._graph.run(
                brand=req_data["brand"],
                goal=req_data["goal"],
                platforms=req_data["platforms"],
                audience=req_data.get("audience", "general audience"),
                tone=req_data.get("tone", "clear and helpful"),
                offer=req_data.get("offer", ""),
                context=req_data.get("context", ""),
                approval_required=req_data.get("approval_required", True),
                live_search_enabled=os.getenv("ENABLE_LIVE_SEARCH", "false").lower() == "true"
            )

            # Check if cancelled during graph execution
            if self._is_cancelled(run_id):
                append_log("Orchestrator", "Execution cancelled before finalizing result.", "failed")
                return

            # Format result
            platform_posts = []
            for post in execution.repurposer.posts:
                platform_posts.append({
                    "platform": post.platform,
                    "format": post.format,
                    "copy": post.copy,
                    "hashtags": post.hashtags,
                    "character_count": post.character_count,
                    "char_limit": post.char_limit,
                    "within_limits": post.within_limits,
                    "media_prompt": post.media_prompt,
                    "status": post.status
                })

            result = {
                "workflow_id": execution.workflow_id,
                "research_brief": execution.market_radar.hypothesis_summary,
                "research_citations": [citation.model_dump() for citation in execution.market_radar.citations],
                "research_is_live": execution.market_radar.is_live_search,
                "content_generation_mode": execution.content_engine.generation_mode,
                "content": platform_posts,
                "flagship_narrative": {
                    "headline": execution.content_engine.flagship_headline,
                    "core_copy": execution.content_engine.flagship_copy,
                    "call_to_action": execution.content_engine.call_to_action
                },
                "quality_review": {
                    "score": execution.quality_gate.compliance_score,
                    "passed": execution.quality_gate.passed,
                    "checks": [f"{c.check_name}: {c.details}" for c in execution.quality_gate.checks],
                    "blockers": execution.quality_gate.blockers,
                    "warnings": execution.quality_gate.warnings
                },
                "approval_status": {
                    "status": execution.approval_gate.status,
                    "notes": execution.approval_gate.audit_notes
                },
                "publishing_summary": {
                    "draft_only_mode": execution.publishing.draft_only_mode,
                    "audit_summary": execution.publishing.audit_summary
                },
                "measurement_plan": {
                    "primary_kpi": execution.analytics.primary_kpi,
                    "secondary_kpis": execution.analytics.secondary_kpis,
                    "note": execution.analytics.measurement_plan_notes
                },
                "next_actions": execution.reporting.recommended_next_actions
            }

            final_status = "awaiting_approval" if req_data.get("approval_required", True) else "draft_ready"
            
            with self._db() as con:
                con.execute(
                    "UPDATE runs SET status=?, result_json=?, logs_json=?, updated_at=? WHERE id=?",
                    (final_status, json.dumps(result), json.dumps(current_logs), now_iso(), run_id)
                )

            append_log("Orchestrator", f"Workflow completed with status: {final_status}.", "completed")
            await broadcaster.broadcast(run_id, "status_change", {
                "status": final_status,
                "result": result
            })

        except Exception as e:
            err_msg = f"Execution error: {str(e)}"
            append_log("System", err_msg, "failed")
            with self._db() as con:
                con.execute("UPDATE runs SET status='failed', logs_json=?, updated_at=? WHERE id=?",
                            (json.dumps(current_logs), now_iso(), run_id))
            await broadcaster.broadcast(run_id, "status_change", {
                "status": "failed",
                "error": err_msg
            })
