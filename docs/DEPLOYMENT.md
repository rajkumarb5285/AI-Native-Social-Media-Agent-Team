# Production Deployment & Infrastructure Guide

This guide details the procedures for local, staging, and production multi-tenant deployments of the AI Native Social Media Agent Team SaaS.

---

## 1. Local Development Deployment

### Prerequisites
- Python 3.11+ or Docker Desktop
- `uv` (recommended) or standard `pip`

### Running with Virtual Environment
```bash
# Clone and enter workspace
cd ai-native-social-agent-team

# Create virtual environment and install dependencies
uv venv .venv --python 3.11
.venv\Scripts\activate       # Windows PowerShell
# source .venv/bin/activate  # macOS / Linux
uv pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Run development server
uvicorn app.main:app --reload --port 8000
```
Open `http://localhost:8000` to access the live dashboard.

### Running with Docker Compose
```bash
docker compose up --build
```
Open `http://localhost:8000`. Database data is persisted inside the named volume `agent_data`.

---

## 2. Staging Deployment

### Staging Checklist
1. **Host on Container Platform**: Deploy container image to staging cluster (e.g. AWS ECS / Fargate, Google Cloud Run, or Kubernetes).
2. **Dedicated Staging Database**: Connect to a staging PostgreSQL instance (or persistent SQLite volume for single-instance tests).
3. **Environment Secrets**: Configure environment variables via Staging Secrets Manager (AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault):
   - `JWT_SECRET`: Random 256-bit key.
   - `SECRET_ENCRYPTION_KEY`: 32-byte encryption key for token storage.
   - `LINKEDIN_CLIENT_ID` & `LINKEDIN_CLIENT_SECRET`: Configured with LinkedIn Developer App in Development/Sandbox tier.
   - `TWITTER_CLIENT_ID` & `TWITTER_CLIENT_SECRET`: Configured with Twitter Developer Portal (Free/Basic tier or Sandbox).
4. **Integration Validation**:
   - Run automated test suite: `pytest -v`.
   - Perform end-to-end OAuth connection test with authorized staging test accounts.
   - Verify approval gates block drafts until sign-off.
   - Verify audit trail entries in `audit_events`.

---

## 3. Production Infrastructure Architecture

```
[Browser / Mobile Client]
          │ (HTTPS / TLS 1.3)
          ▼
   [Cloudflare / WAF]
          │ (Rate limiting & DDoS protection)
          ▼
   [Application Load Balancer]
          │
    ┌─────┴────────────────┐
    ▼                      ▼
[FastAPI Instance A]  [FastAPI Instance B]
    │                      │
    ├──────────────────────┼──────────────────────┐
    ▼                      ▼                      ▼
[PostgreSQL Primary]  [Redis Task Queue]  [Cloud Secret Manager]
(Tenant-scoped data)  (Durable worker)     (Encrypted tokens)
```

### Infrastructure Components
- **API Nodes**: FastAPI container instances with autoscaling (min 2, max 10 based on CPU/memory).
- **Relational Storage**: Managed PostgreSQL (AWS RDS / GCP Cloud SQL) with automated daily snapshots, multi-AZ failover, and point-in-time recovery (PITR).
- **Task Queue**: Managed Redis (AWS ElastiCache / Redis Cloud) for background workflow workers.
- **Key & Secret Management**: Store all OAuth client secrets, LLM keys, and database credentials in AWS Secrets Manager or GCP Secret Manager. Never commit secrets to source control.

---

## 4. Backups, Recovery & Business Continuity

### Database Backup Schedule
- **Continuous Archiving**: WAL (Write-Ahead Logging) archiving to encrypted S3 / GCS bucket.
- **Daily Full Snapshot**: Retained for 30 days.
- **Weekly Snapshot**: Retained for 90 days.

### Disaster Recovery Procedure (RTO < 30 min, RPO < 5 min)
1. In case of primary database failure, trigger automated failover to the replica in secondary Availability Zone.
2. If total region failure occurs:
   - Restore database from latest PITR snapshot in secondary region.
   - Update DNS records via Cloudflare / Route 53 to point to secondary region load balancer.
   - Execute database migration verification: `python -m app.db.migrations`.
   - Run health checks: `GET /api/health`.

---

## 5. External Integration Status & Audit

| Integration Service | Status | Live Credentials Required | Honesty / Fallback Boundary |
|---|---|---|---|
| **LLM Inference** | Implemented (OpenAI-compatible) | `LLM_API_KEY` | When omitted, runs in clearly labeled Demo Mode; parses and validates schemas |
| **Market Research** | Implemented (Tavily/Search Adapter) | `TAVILY_API_KEY` | Sanitizes prompt injections; when unconfigured, derives hypotheses from supplied context without fake citations |
| **LinkedIn Adapter** | Implemented (OAuth2 + ugcPosts) | Client ID & Secret | OAuth URL generation, token refresh, and connection validation active; publishing blocked without verified connection and human approval |
| **Twitter / X Adapter** | Implemented (OAuth2 PKCE + Tweets v2) | Client ID & Secret | Token encryption at rest active; publishing blocked without verified connection and human approval |
| **Analytics Engine** | Implemented | Platform API tokens | Labels baseline planning targets vs real API metrics |
