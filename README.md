# AI Native Social Media Agent Team

A buildable starter for a multi-agent social media operations platform inspired by the visible concepts in the supplied video. This is an original implementation, not a source-code clone of the Claude artifact. The artifact source was not retrievable from the provided link.

## What is included
- FastAPI backend and responsive dashboard
- Persistent SQLite run history
- Six cooperating workflow roles: Orchestrator, MarketRadar, Content Engine, Repurposing, Quality Gate, Analytics Planner
- OpenAI-compatible model API integration (optional; configured by environment variables)
- Honest demo mode when no model key is configured
- Run states, logs, approval status, health endpoint
- Dockerfile and Docker Compose
- Antigravity build brief, architecture, test checklist, and deployment guide

## Important production boundary
This starter can generate plans and content drafts. It does **not** pretend to publish posts, read live social metrics, or connect to social accounts without platform-specific OAuth/API credentials and adapters. Real publishing must be implemented and tested against the official API for each platform. Do not scrape sites or automate account actions in ways that violate platform terms. Keep human approval enabled until the integration has been tested.

## Run locally
Requires Python 3.11+.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000

If no API key is configured, the app runs in clearly labelled demo mode. For real LLM generation, set `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL` in `.env` to a provider and model you are authorized to use.

## Run with Docker
```bash
docker compose up --build
```
Open http://localhost:8000

## API
- `GET /api/health` — health and mode
- `GET /api/agents` — available workflow roles
- `GET /api/runs` — recent persisted runs
- `POST /api/runs` — run a content workflow
- `GET /api/runs/{run_id}` — retrieve run result/logs
- `POST /api/runs/{run_id}/approve` — approve a draft (does not publish it)

Example:
```bash
curl -X POST http://localhost:8000/api/runs \
  -H "Content-Type: application/json" \
  -d '{"brand":"Acme Coffee","goal":"Launch a new cold brew","platforms":["LinkedIn","Instagram"],"audience":"young professionals","tone":"confident and friendly","offer":"first order discount","approval_required":true}'
```

## Production checklist before selling
1. Replace local SQLite with managed PostgreSQL.
2. Add user authentication, tenant isolation, role-based access, CSRF protection where relevant, rate limits, and audit trails.
3. Add a durable queue/worker (Celery/RQ/Temporal or equivalent) for long-running jobs.
4. Implement platform-specific OAuth and official API adapters; store tokens in a secret manager and encrypt at rest.
5. Add idempotency, retries with backoff, token refresh, quotas, webhook verification, and duplicate-post prevention.
6. Add monitoring, structured logs, alerts, backups, data deletion/export, privacy policy, terms, and incident response.
7. Run security scans, dependency updates, load tests, and provider/platform policy reviews.
8. Keep approval gates for publishing, paid promotion, messaging, deletion, and any spend-bearing action.
9. Verify every capability with live sandbox/test accounts before advertising it to customers.
10. Obtain customer consent for data sources and use least-privilege OAuth scopes.

## Commercial positioning
Sell a measurable outcome such as “approved weekly social content and campaign reporting for small marketing teams,” not “62 fully autonomous agents” unless the implemented system truly provides that capability. Start with a paid pilot, define supported platforms and usage limits, measure time saved and content approval rate, then expand.
