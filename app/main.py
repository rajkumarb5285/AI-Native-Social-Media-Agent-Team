import os, json, sqlite3, uuid, datetime, asyncio
from pathlib import Path
from typing import Any
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()
APP_NAME = os.getenv("APP_NAME", "AI Native Social Agent Team")
DB_PATH = os.getenv("DATABASE_PATH", "./agent_runs.db")
API_KEY = os.getenv("LLM_API_KEY", "").strip()
BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
MODEL = os.getenv("LLM_MODEL", "gpt-4.1-mini")
TIMEOUT = float(os.getenv("LLM_TIMEOUT_SECONDS", "45"))
DEMO_MODE = not bool(API_KEY)

AGENTS = [
    {"id": "orchestrator", "name": "Orchestrator", "department": "Operations", "purpose": "Plans, validates, and coordinates multi-agent workflow execution.", "status": "ready"},
    {"id": "market-radar", "name": "MarketRadar", "department": "Research", "purpose": "Synthesizes audience research, market hypotheses, and content angles.", "status": "ready"},
    {"id": "brand-memory", "name": "BrandMemory", "department": "Governance", "purpose": "Enforces tenant-scoped brand guidelines, tone rules, and banned vocabulary.", "status": "ready"},
    {"id": "content-engine", "name": "Content Engine", "department": "Content", "purpose": "Drafts authoritative flagship messaging and campaign narratives.", "status": "ready"},
    {"id": "repurposer", "name": "Repurposing Agent", "department": "Content", "purpose": "Adapts core messaging into channel-optimized formats with length verification.", "status": "ready"},
    {"id": "quality-gate", "name": "Quality Gate", "department": "Governance", "purpose": "Automated checks for character limits, compliance, tone, and prohibited terms.", "status": "ready"},
    {"id": "approval-gate", "name": "Approval Gate", "department": "Governance", "purpose": "Enforces authorized human review and sign-off before external writes.", "status": "ready"},
    {"id": "publishing", "name": "Publishing Agent", "department": "Operations", "purpose": "Dispatches approved drafts to verified official APIs with idempotency keys.", "status": "ready"},
    {"id": "analytics", "name": "Analytics Agent", "department": "Analytics", "purpose": "Defines KPI frameworks and retrieves verified metrics via platform APIs.", "status": "ready"},
    {"id": "reporting", "name": "Reporting Agent", "department": "Operations", "purpose": "Synthesizes continuous performance audits and strategic next actions.", "status": "ready"},
]

from contextlib import asynccontextmanager
from app.agents.graph import AgentGraph

agent_graph = AgentGraph()

def clean_and_parse_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)

class RunRequest(BaseModel):
    brand: str = Field(min_length=1, max_length=120)
    goal: str = Field(min_length=1, max_length=600)
    platforms: list[str] = Field(default_factory=lambda: ["LinkedIn"], min_length=1, max_length=6)
    audience: str = Field(default="general audience", max_length=300)
    tone: str = Field(default="clear and helpful", max_length=120)
    offer: str = Field(default="", max_length=400)
    context: str = Field(default="", max_length=4000)
    approval_required: bool = True

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

from fastapi import Depends
from app.db.migrations import run_migrations
from app.security.auth import get_current_user, require_role, AuthenticatedUser
from app.security.audit import AuditLogger
from app.security.rate_limit import check_rate_limit
from app.integrations.manager import platform_manager
from app.integrations.base import ConnectionRecord
from urllib.parse import urlparse

audit_logger = AuditLogger(lambda: DB_PATH)

def init_db():
    run_migrations(DB_PATH)

async def call_llm(system: str, user: str) -> str:
    if not API_KEY:
        return ""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(
            f"{BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type":"application/json"},
            json={"model": MODEL, "temperature": 0.4, "messages":[
                {"role":"system","content":system},{"role":"user","content":user}
            ]},
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

async def run_workflow(req: RunRequest):
    execution = await agent_graph.run(
        brand=req.brand,
        goal=req.goal,
        platforms=req.platforms,
        audience=req.audience,
        tone=req.tone,
        offer=req.offer,
        context=req.context,
        approval_required=req.approval_required,
        live_search_enabled=os.getenv("ENABLE_LIVE_SEARCH", "false").lower() == "true"
    )

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

    logs = [
        {"time": l.time, "agent": l.agent, "message": l.message, "status": l.status}
        for l in execution.logs
    ]
    return result, logs

from fastapi.responses import HTMLResponse, StreamingResponse
from app.queue.task_queue import DurableTaskQueue
from app.queue.broadcaster import broadcaster

task_queue = DurableTaskQueue(lambda: DB_PATH)

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    init_db()
    task_queue.start()
    yield
    await task_queue.stop()

app = FastAPI(title=APP_NAME, version="0.1.0", description="Multi-agent social content workflow starter", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent/"static")), name="static")

@app.get("/", response_class=HTMLResponse)
def home():
    return (Path(__file__).parent/"static"/"index.html").read_text(encoding="utf-8")

@app.get("/api/health")
def health():
    return {"status":"ok","mode":"demo" if DEMO_MODE else "llm-enabled","model":MODEL if API_KEY else None,"time":now(),
            "integrations":{"social_publishing":False,"live_market_research":False,"live_analytics":False}}

@app.get("/api/agents")
def agents():
    return {"agents":AGENTS,"note":"Ten implemented specialist workflow roles."}

@app.get("/api/runs")
def list_runs(user: AuthenticatedUser = Depends(get_current_user)):
    with db() as con:
        rows = con.execute(
            "SELECT id,created_at,updated_at,status,request_json,approved,retry_count FROM runs WHERE tenant_id=? ORDER BY created_at DESC LIMIT 50",
            (user.tenant_id,)
        ).fetchall()
    return {"runs":[{"id":r["id"],"created_at":r["created_at"],"updated_at":r["updated_at"],"status":r["status"],
                     "request":json.loads(r["request_json"]),"approved":bool(r["approved"]),
                     "retry_count":r["retry_count"] if "retry_count" in r.keys() else 0} for r in rows]}

@app.post("/api/runs")
async def create_run(req: RunRequest, sync: bool = True, user: AuthenticatedUser = Depends(get_current_user)):
    run_id=str(uuid.uuid4())
    with db() as con:
        con.execute(
            "INSERT INTO runs(id,created_at,updated_at,status,request_json,logs_json,approved,retry_count,tenant_id) VALUES(?,?,?,?,?,?,?,?,?)",
            (run_id,now(),now(),"queued" if not sync else "running",req.model_dump_json(),"[]",0,0,user.tenant_id)
        )

    audit_logger.log(user.tenant_id, user.user_id, "WORKFLOW_CREATED", run_id, {"brand": req.brand, "platforms": req.platforms})

    if not sync:
        await task_queue.enqueue(run_id)
        return {
            "id": run_id,
            "status": "queued",
            "stream_url": f"/api/runs/{run_id}/stream",
            "mode": "demo" if DEMO_MODE else "llm-enabled"
        }

    try:
        result, logs = await run_workflow(req)
        status = "awaiting_approval" if req.approval_required else "draft_ready"
        with db() as con:
            con.execute("UPDATE runs SET updated_at=?,status=?,result_json=?,logs_json=? WHERE id=?",
                        (now(),status,json.dumps(result),json.dumps(logs),run_id))
        return {"id":run_id,"status":status,"request":req.model_dump(),"result":result,"logs":logs,"mode":"demo" if DEMO_MODE else "llm-enabled"}
    except httpx.HTTPError as e:
        with db() as con:
            con.execute("UPDATE runs SET updated_at=?,status=?,logs_json=? WHERE id=?",
                        (now(),"failed",json.dumps([{"time":now(),"agent":"system","message":str(e),"status":"failed"}]),run_id))
        raise HTTPException(502, "LLM provider request failed. Check API key, base URL, model access, and provider status.")
    except Exception as e:
        with db() as con:
            con.execute("UPDATE runs SET updated_at=?,status=?,logs_json=? WHERE id=?",
                        (now(),"failed",json.dumps([{"time":now(),"agent":"system","message":str(e),"status":"failed"}]),run_id))
        raise HTTPException(500, f"Workflow failed: {str(e)}")

@app.get("/api/runs/{run_id}")
def get_run(run_id: str, user: AuthenticatedUser = Depends(get_current_user)):
    with db() as con:
        r=con.execute("SELECT * FROM runs WHERE id=? AND tenant_id=?",(run_id, user.tenant_id)).fetchone()
    if not r: raise HTTPException(404,"Run not found")
    return {"id":r["id"],"created_at":r["created_at"],"updated_at":r["updated_at"],"status":r["status"],
            "request":json.loads(r["request_json"]),"result":json.loads(r["result_json"]) if r["result_json"] else None,
            "logs":json.loads(r["logs_json"]),"approved":bool(r["approved"]),
            "retry_count":r["retry_count"] if "retry_count" in r.keys() else 0}

@app.get("/api/runs/{run_id}/stream")
async def stream_run(run_id: str):
    with db() as con:
        r = con.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
    if not r:
        raise HTTPException(404, "Run not found")

    async def event_generator():
        with db() as con:
            curr = con.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if curr:
            snapshot = {
                "event": "snapshot",
                "status": curr["status"],
                "logs": json.loads(curr["logs_json"]),
                "result": json.loads(curr["result_json"]) if curr["result_json"] else None
            }
            yield f"data: {json.dumps(snapshot)}\n\n"

        queue = await broadcaster.subscribe(run_id)
        try:
            while True:
                msg = await queue.get()
                yield f"data: {json.dumps(msg)}\n\n"
                if msg.get("event") == "status_change":
                    st = msg.get("data", {}).get("status")
                    if st in ("approved", "succeeded", "failed", "cancelled", "awaiting_approval", "draft_ready"):
                        break
        finally:
            await broadcaster.unsubscribe(run_id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/runs/{run_id}/cancel")
async def cancel_run(run_id: str, user: AuthenticatedUser = Depends(get_current_user)):
    success = await task_queue.cancel(run_id)
    if not success:
        with db() as con:
            r = con.execute("SELECT id, status FROM runs WHERE id=? AND tenant_id=?", (run_id, user.tenant_id)).fetchone()
        if not r:
            raise HTTPException(404, "Run not found")
        raise HTTPException(409, f"Cannot cancel run with status '{r['status']}'")
    audit_logger.log(user.tenant_id, user.user_id, "WORKFLOW_CANCELLED", run_id)
    return {"id": run_id, "status": "cancelled", "message": "Workflow run cancelled successfully."}

@app.post("/api/runs/{run_id}/retry")
async def retry_run(run_id: str, user: AuthenticatedUser = Depends(get_current_user)):
    success = await task_queue.retry(run_id)
    if not success:
        with db() as con:
            r = con.execute("SELECT id, status FROM runs WHERE id=? AND tenant_id=?", (run_id, user.tenant_id)).fetchone()
        if not r:
            raise HTTPException(404, "Run not found")
        raise HTTPException(409, f"Cannot retry run with status '{r['status']}'")
    audit_logger.log(user.tenant_id, user.user_id, "WORKFLOW_RETRIED", run_id)
    return {"id": run_id, "status": "queued", "message": "Workflow run re-queued for execution."}

@app.post("/api/runs/{run_id}/approve")
def approve_run(run_id: str, user: AuthenticatedUser = Depends(require_role(["admin", "editor"]))):
    with db() as con:
        r=con.execute("SELECT id,status FROM runs WHERE id=? AND tenant_id=?",(run_id, user.tenant_id)).fetchone()
        if not r: raise HTTPException(404,"Run not found")
        if r["status"] not in ("awaiting_approval","draft_ready","approved"):
            raise HTTPException(409,f"Cannot approve run with status {r['status']}")
        con.execute("UPDATE runs SET approved=1,status='approved',updated_at=? WHERE id=?",(now(),run_id))
    audit_logger.log(user.tenant_id, user.user_id, "DRAFT_APPROVED", run_id, {"approver": user.email})
    return {"id":run_id,"status":"approved","message":"Draft approved internally. This does not publish to any platform."}

@app.post("/api/runs/{run_id}/publish")
async def publish_run(run_id: str, user: AuthenticatedUser = Depends(require_role(["admin", "editor"]))):
    with db() as con:
        r = con.execute("SELECT * FROM runs WHERE id=? AND tenant_id=?", (run_id, user.tenant_id)).fetchone()
    if not r:
        raise HTTPException(404, "Run not found")
    if not r["approved"]:
        raise HTTPException(403, "Cannot publish unapproved draft. Explicit human approval is required.")
    result_data = json.loads(r["result_json"]) if r["result_json"] else {}
    posts = result_data.get("content", [])
    if not posts:
        raise HTTPException(409, "This run has no stored content to publish.")
    connections = platform_manager.list_connections(user.tenant_id)
    publish_outcomes = []
    for post in posts:
        platform = str(post.get("platform", "")).lower()
        matching = next((c for c in connections if c.platform.lower() == platform or (platform == "x" and c.platform.lower() == "twitter")), None)
        if matching is None:
            publish_outcomes.append({"success": False, "platform": post.get("platform"), "error_message": "No connected account for this platform and workspace."})
            continue
        res = await platform_manager.publish(
            platform=platform,
            connection_id=matching.connection_id,
            copy=str(post.get("copy", "")),
            idempotency_key=f"pub_{run_id}_{platform}",
            tenant_id=user.tenant_id
        )
        publish_outcomes.append(res.model_dump())
    all_success = len(publish_outcomes) == len(posts) and all(item.get("success") and item.get("external_post_id") for item in publish_outcomes)
    final_status = "published" if all_success else "publish_partial_or_failed"
    with db() as con:
        con.execute("UPDATE runs SET status=?, updated_at=? WHERE id=? AND tenant_id=?", (final_status, now(), run_id, user.tenant_id))
    audit_logger.log(user.tenant_id, user.user_id, "PUBLISH_EXECUTED" if all_success else "PUBLISH_PARTIAL_OR_FAILED", run_id, {"outcomes": publish_outcomes})
    return {"id": run_id, "status": final_status, "outcomes": publish_outcomes, "all_published": all_success}
@app.get("/api/audit")
def get_audit_trail(user: AuthenticatedUser = Depends(require_role(["admin"]))):
    with db() as con:
        rows = con.execute("SELECT * FROM audit_events WHERE tenant_id=? ORDER BY created_at DESC LIMIT 100", (user.tenant_id,)).fetchall()
    return {"events": [dict(r) for r in rows]}

def _oauth_state_table():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS oauth_states (
            state TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, platform TEXT NOT NULL,
            redirect_uri TEXT NOT NULL, created_at TEXT NOT NULL
        )""")

@app.get("/api/connections")
def list_connections(user: AuthenticatedUser = Depends(get_current_user)):
    conns = platform_manager.list_connections(user.tenant_id)
    return {"connections": [c.model_dump(exclude={"encrypted_access_token", "encrypted_refresh_token"}) for c in conns]}

@app.get("/api/connections/{platform}/connect")
def start_social_connect(platform: str, user: AuthenticatedUser = Depends(require_role(["admin", "editor"]))):
    platform = platform.lower()
    adapter = platform_manager.get_adapter(platform)
    if not adapter:
        raise HTTPException(400, "Unsupported platform. Supported for this prototype: LinkedIn and X.")
    client_id_name = "LINKEDIN_CLIENT_ID" if platform == "linkedin" else "TWITTER_CLIENT_ID"
    if not os.getenv(client_id_name, "").strip():
        raise HTTPException(503, f"{client_id_name} is not configured.")
    public_base = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    parsed_base = urlparse(public_base) if public_base else None
    if not public_base:
        raise HTTPException(503, "Set PUBLIC_BASE_URL to the HTTPS URL of this deployed API.")
    if parsed_base.scheme != "https" and os.getenv("ENVIRONMENT", "development").lower() not in {"development", "test"}:
        raise HTTPException(503, "PUBLIC_BASE_URL must use HTTPS outside development/test.")
    redirect_uri = f"{public_base}/api/connections/{platform}/callback"
    state = uuid.uuid4().hex + uuid.uuid4().hex
    _oauth_state_table()
    with db() as con:
        con.execute("INSERT INTO oauth_states(state,tenant_id,platform,redirect_uri,created_at) VALUES(?,?,?,?,?)",
                    (state, user.tenant_id, platform, redirect_uri, now()))
    if platform == "linkedin":
        scopes = ["w_member_social", "openid", "profile", "email"]
    else:
        scopes = ["tweet.read", "tweet.write", "users.read", "offline.access"]
    return {"authorization_url": adapter.connect_url(user.tenant_id, scopes, redirect_uri, state),
            "platform": platform, "redirect_uri": redirect_uri}

@app.get("/api/connections/{platform}/callback")
async def finish_social_connect(platform: str, code: str, state: str):
    platform = platform.lower()
    _oauth_state_table()
    with db() as con:
        row = con.execute("SELECT * FROM oauth_states WHERE state=? AND platform=?", (state, platform)).fetchone()
        if not row:
            raise HTTPException(400, "OAuth state is invalid, expired, or already used.")
        # One-time state prevents replay; expire stale attempts after 10 minutes.
        created = datetime.datetime.fromisoformat(row["created_at"])
        if (datetime.datetime.now(datetime.timezone.utc) - created).total_seconds() > 600:
            con.execute("DELETE FROM oauth_states WHERE state=?", (state,))
            raise HTTPException(400, "OAuth state expired. Start account connection again.")
        con.execute("DELETE FROM oauth_states WHERE state=?", (state,))
    adapter = platform_manager.get_adapter(platform)
    if not adapter:
        raise HTTPException(400, "Unsupported platform.")
    try:
        connection = await adapter.handle_oauth_callback(
            code=code, redirect_uri=row["redirect_uri"], state=state, tenant_id=row["tenant_id"]
        )
        if not await adapter.validate_connection(connection):
            raise HTTPException(502, "The platform did not verify this connection.")
        platform_manager.save_connection(connection)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"OAuth exchange or connection verification failed: {type(exc).__name__}")
    return HTMLResponse(
        "<html><body><h2>Account connected</h2><p>You can return to the Social Agent dashboard.</p></body></html>"
    )
