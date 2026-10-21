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

---

## 6. Render Backend & Vercel Frontend Deployment

This SaaS is architected as a decoupled system: the FastAPI backend runs on **Render** (or Docker container hosts), and the dashboard frontend runs on **Vercel** (or any static edge CDN).

### Part A: Deploying Backend & Multi-Agent Team to Render

#### Method 1: Using the Render Blueprint (Recommended)
1. Go to [dashboard.render.com](https://dashboard.render.com/) and click **New > Blueprint**.
2. Connect your GitHub repository (`AI-Native-Social-Media-Agent-Team`).
3. Render automatically detects [`render.yaml`](file:///c:/Users/Rajkumar%20Pandey/Downloads/ai-native-social-agent-team/ai-native-social-agent-team/render.yaml) and configures:
   - **Service Name**: `ai-native-social-agent-team`
   - **Runtime**: Python 3.11
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/api/health`
4. If you have an OpenAI/LLM API key, set `LLM_API_KEY` under Environment Variables. (If left blank, the backend operates in transparent demo mode).
5. Click **Apply**. Once built, Render will assign a public HTTPS URL (e.g. `https://ai-native-social-agent-team.onrender.com`).

#### Method 2: Manual Web Service Creation on Render
1. Click **New > Web Service**.
2. Connect `https://github.com/rajkumarb5285/AI-Native-Social-Media-Agent-Team`.
3. Set configuration:
   - **Name**: `ai-native-social-agent-team`
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add Environment Variables:
   - `ENVIRONMENT` = `production`
   - `CORS_ORIGINS` = `*` (or your Vercel URL)
   - `JWT_SECRET` = *(Generate random string)*
   - `SECRET_ENCRYPTION_KEY` = *(Generate random 32-byte string)*
   - `LLM_API_KEY` = *(Optional)*
5. Click **Create Web Service**.

---

### Part B: Deploying Frontend Dashboard to Vercel

#### Method 1: Direct GitHub Integration
1. Log in to [vercel.com](https://vercel.com/) and click **Add New > Project**.
2. Import `https://github.com/rajkumarb5285/AI-Native-Social-Media-Agent-Team`.
3. In Project Settings:
   - **Framework Preset**: `Other`
   - **Root Directory**: `frontend` (or leave as `.` since root `vercel.json` maps to `frontend`)
4. Click **Deploy**. Vercel will build and assign a production URL (e.g. `https://ai-native-social-agent-team.vercel.app`).

#### Method 2: Command Line Deployment
```bash
cd frontend
npx vercel --prod
```

---

### Part C: Connecting the Vercel Frontend to the Render Backend

The frontend supports zero-downtime dynamic backend binding:
1. **Interactive UI Switcher**:
   - Open your deployed Vercel URL.
   - Click **change** next to **API:** in the top header.
   - Paste your Render URL (e.g. `https://ai-native-social-agent-team.onrender.com`). The browser will save this in `localStorage` and immediately query your cloud backend.
2. **One-Click Shareable Link**:
   - Append `?api=https://your-backend.onrender.com` to your Vercel URL:
     `https://your-frontend.vercel.app?api=https://ai-native-social-agent-team.onrender.com`
   - The dashboard will auto-configure and remember the backend endpoint.

