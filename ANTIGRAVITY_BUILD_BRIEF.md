# Antigravity Build Brief — Productionize the AI Native Social Agent Team

## Mission
Continue from this repository. Build an original, production-grade multi-tenant social media operations agent inspired by the *visible workflow concepts* in the supplied demo video. Do not claim to have copied the unavailable Claude artifact or its source. Do not invent capabilities. The starter is an honest working prototype with draft generation and approval; the following work is required before commercial production.

## First steps
1. Read `README.md`, inspect every source file, and run the app.
2. Run tests and add missing tests before refactoring.
3. Keep the visible dark dashboard style but improve responsive accessibility and keyboard navigation.
4. Preserve demo-mode labels. Never display fake live agents, metrics, search results, publishing successes, or social connections.
5. Produce a `BUILD_STATUS.md` separating completed, partially implemented, and blocked items.

## Target architecture
- Frontend: Next.js + TypeScript + accessible component library, responsive live dashboard.
- API: FastAPI, typed request/response schemas, versioned REST endpoints.
- Durable execution: Redis + Celery/RQ or Temporal; persist each job, step, attempt, output, duration, cost, and failure.
- Database: PostgreSQL with Alembic migrations and tenant-scoped queries.
- LLM layer: provider interface, structured outputs/schema validation, timeouts, retry/backoff, token/cost tracking, model configuration per tenant.
- Integrations: separate official API adapter for each supported platform. OAuth, encrypted tokens, least privilege, refresh, quotas, webhook signature checks, and revocation.
- Observability: structured logs, OpenTelemetry-compatible traces, metrics, alerting, health/readiness endpoints.
- Deployment: Docker Compose for local development; production deployment instructions for managed Postgres, queue, secret manager, TLS, backups, and monitoring.

## Agent graph
Implement explicit typed stages, not 62 fake independent agents:
1. Orchestrator — validates goal, decomposes work, selects allowed tools.
2. MarketRadar — research hypotheses from supplied facts; add a search adapter only when configured and cite retrieved sources.
3. BrandMemory — retrieves approved brand guidelines and campaign history with tenant isolation.
4. ContentEngine — produces structured channel-specific drafts.
5. Repurposer — adapts the approved core message per platform.
6. QualityGate — checks schema, tone, policy, claims, links, duplicate content, platform limits.
7. ApprovalGate — waits for authorized human approval before external actions.
8. Publisher — publishes only through an official API adapter with explicit tenant connection and idempotency key.
9. Analytics — fetches real metrics through connected official APIs and labels refresh timestamps.
10. Learning/Reporting — proposes improvements from observed results without silently changing brand policy.

Each step must have a real state machine (`queued`, `running`, `needs_approval`, `succeeded`, `failed`, `cancelled`), timestamps, retry count, input/output references, and audit history. Provide cancellation and safe retry. Prevent duplicate publication.

## Human approval and safety
- Require explicit approval for publishing, deleting, sending DMs, launching paid promotions, or actions that spend money.
- Never store credentials in source code, browser local storage, logs, or plain database columns.
- Treat retrieved webpages and uploaded text as untrusted prompt-injection-prone content.
- Scope every DB query by tenant and enforce role-based access.
- Keep an audit trail of who approved each external action and what exact payload was approved.
- Provide pause-all, disconnect account, revoke token, export data, and delete tenant data flows.
- Do not bypass CAPTCHA, platform rate limits, OAuth, access controls, or platform terms.

## Implementation order
Phase 1: Stabilize current FastAPI prototype, unit tests, schema validation, and run history.
Phase 2: Add PostgreSQL migrations, tenant/auth model, RBAC, audit events.
Phase 3: Add durable queue, retries, cancellation, real-time WebSocket/SSE updates.
Phase 4: Add LLM provider abstraction and structured outputs with evaluation tests.
Phase 5: Add one official social platform adapter end-to-end in sandbox/test account. Do not add more platforms until token refresh, idempotency, error mapping, and tests pass.
Phase 6: Add official analytics adapter and real trend search integration with source citations.
Phase 7: Add billing, usage quotas, onboarding, support, privacy/terms, deployment/monitoring.
Phase 8: Security review, threat model, load tests, disaster recovery test, production acceptance checklist.

## Required tests
- Request schema validation and prompt injection resilience.
- Demo mode clearly labels all simulated/non-live functions.
- LLM timeout, invalid JSON, rate limit, and provider error behavior.
- Database persistence across restarts.
- Tenant isolation and RBAC tests.
- OAuth state validation, token encryption, token refresh and revocation.
- Duplicate post prevention / idempotency under retry.
- Approval gate blocks every external write until approval.
- Integration adapter tests with mocked provider and one live sandbox test.
- Accessibility checks, responsive mobile layout, API contract tests.
- Secrets scanning, dependency audit, container scan, backup/restore test.

## Definition of done
Do not label the system production-ready until all release-blocking tests pass and the supported platforms are named explicitly. Give the user a report with actual commands run, results, known gaps, and exact deployment steps. Never claim a test passed unless it was executed.
