# Architecture and real-time behavior

## Current prototype
Browser dashboard → FastAPI → workflow runner → optional OpenAI-compatible chat completions API → SQLite run record → dashboard output.

The current workflow is request/response, not a durable background worker. It persists run history and stage logs after execution. “Live” in this version means the dashboard talks to the running API; it does not mean external social platforms are connected.

## Production target
Browser (Next.js) → API/auth → PostgreSQL → durable queue → worker/agent graph → LLM/search/brand memory → approval gate → official platform adapter → webhooks/analytics → event stream to dashboard.

Use Server-Sent Events or WebSockets for real stage updates. A job is not “running” merely because a UI counter animates. Every status must correspond to persisted backend state.

## Integration contracts
Each adapter should expose:
- `connect_url(tenant_id, scopes)` and OAuth callback validation
- `refresh_credentials(connection_id)`
- `validate_connection(connection_id)`
- `publish_draft(connection_id, approved_payload, idempotency_key)`
- `fetch_metrics(connection_id, post_ids, date_range)`
- `disconnect(connection_id)` and token revocation where supported

The base prototype intentionally contains no fake platform adapter. Confirm the current official API, supported post types, app review, account requirements, and rate limits before choosing a platform.
