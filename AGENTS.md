# ANTIGRAVITY: PRODUCTION BUILD INSTRUCTIONS
### AI-Native Social Media Team: remove all demo behavior, enforce real auth, make the poster/pamphlet agents business-aware

> **How to use:** Save this file in the project root as `AGENTS.md` (or paste it as the project instructions). Tell Antigravity: *"Read this entire file. Do Phase 0 first and show me AUDIT.md before changing anything."*

---

## 0. CONTEXT AND GOAL

We are building a **production, multi-tenant SaaS** for real clients. A client signs in with a real Google account, registers **their own business from scratch**, connects their real social accounts, and a team of LangGraph agents researches, designs (posters, social posts, pamphlets/flyers), schedules and publishes content **specific to that business**.

Current stack (keep unless there is a strong reason): Next.js (App Router, TypeScript, Tailwind, shadcn/ui) on Vercel, FastAPI backend, PostgreSQL + pgvector, Redis, LangGraph, Playwright renderer.

### The four defects to fix (reported by the product owner)
1. **One template for every business.** The poster agent always outputs the coffee-shop design, even after registering a sneaker business and regenerating several times.
2. **Demo behavior everywhere.** The app shows pre-filled demo data (a pre-created business, a Diwali festival banner, a sample poster, "0 connected channels" placeholders, etc.), like a demo account.
3. **Authentication is not strict or persistent.** Sign-in does not reliably authorize; the session breaks when switching browser tabs; the app is usable in a demo state without real login.
4. **Businesses are pre-registered.** A client must start from an empty state and enter their business details themselves.

### Definition of done (summary)
A brand-new Google user sees an empty workspace, registers a sneaker store, uploads product photos, and receives visually distinct, correctly aligned, sneaker-appropriate posters and a pamphlet. A second brand-new user registers a salon and receives completely different designs. **No coffee content, no demo content, no pre-filled data anywhere.** Logging in is impossible without real Google OAuth, and the session works across tabs.

---

## 1. NON-NEGOTIABLE RULES

1. **No demo mode. Anywhere.** No seeded users, businesses, posters, campaigns, analytics, festivals, channels or sample copy in dev, staging or production. The only allowed fixtures live in `tests/` and are loaded only by the test runner into a throwaway test database.
2. **No default business.** The system must never fall back to a default brand, default industry, default template, or default copy. If information is missing, **ask the user** or **fail loudly with a clear message**.
3. **No hardcoded industry content in prompts or code.** Prompts use placeholders (`{{business_name}}`, `{{industry}}`) and receive real data at runtime. Example content from one industry must never be placed in a shared prompt, because models copy examples. Few-shot examples are retrieved dynamically from the same industry and labeled "style reference only, do not copy content".
4. **No auth bypass.** No `SKIP_AUTH`, `DEMO_USER`, dev backdoor, guest mode, magic query params, or email-only login. Every API route except `/health` and the OAuth endpoints requires a valid server-verified session.
5. **Tenant isolation.** Every row has `workspace_id`; every query is scoped by it; enforce with Postgres Row-Level Security as a second layer. LangGraph threads, caches and memory are keyed by `workspace_id` + `campaign_id`.
6. **Fail loudly, never fake success.** If an image fails, a platform call fails, or the model returns bad JSON, show the real error and a retry path. Do not substitute sample content.
7. **Secrets** only in environment variables / secret manager. Never log tokens, secrets or personal data.
8. **Every change is verified** by running the app, tests and the acceptance matrix in section 9. Report results honestly; if something fails, say so.

---

## 2. PHASE 0: AUDIT AND PURGE (do this first; produce `AUDIT.md`)

Before writing new features, search the entire repo (frontend, backend, agents, prompts, assets, seed scripts, env files, CI) and list every place that causes demo or single-template behavior. Suggested searches (case-insensitive):

```
grep -rniE "demo|mock|sample|dummy|fake|lorem|placeholder|seed|fixture|faker|stub" --include=*.{ts,tsx,js,py,json,md,yml,yaml,sql,env*} .
grep -rniE "rajkumar|coffee|brew|cafe|espresso|diwali|festival poster|single.origin" .
grep -rniE "SKIP_AUTH|DEMO_|BYPASS|guest|devUser|testUser|isDemo|demoMode|NEXT_PUBLIC_DEMO" .
grep -rniE "default(Business|Brand|Template|Workspace|Industry)|fallback(Template|Brand)" .
grep -rniE "localStorage|sessionStorage|useState\(.*(user|session|business)" src/
```
Also inspect: static JSON/data folders, `/public` sample images, MSW or API mock handlers, Storybook mocks that leak into the build, database seeds and migrations that insert rows, startup hooks that auto-create a workspace from the user's name, the festival/banner component, hardcoded "Connected Channels 0", cached LLM responses, module-level globals in the agent code, and the image library (coffee-only images).

**`AUDIT.md` must contain:** a table of `file:line | what it does | why it is a problem | fix`, grouped under: (A) demo data, (B) auth weaknesses, (C) single-template root causes, (D) hardcoded industry content in prompts. Then **delete or replace** every item and re-run the searches until they return nothing outside `tests/`.

---

## 3. AUTHENTICATION: STRICT, REAL, PERSISTENT

### 3.1 Requirements
- **Only** real **Google OAuth 2.0 / OpenID Connect** at first (Authorization Code flow + PKCE, `state`, `nonce`). No other login path exists.
- Verify the ID token server-side: signature (Google JWKS), `iss`, `aud`, `exp`, `nonce`, and `email_verified == true`. Identify users by Google `sub`, not email.
- **No account, no access.** Unauthenticated requests get `401` (API) or a redirect to `/login` (pages). There is no guest or demo view.
- Sessions are **server-side** (session ID in Postgres/Redis) delivered via an **HttpOnly, Secure, SameSite=Lax cookie**. Never keep auth state in `localStorage` or only in React state. Never store OAuth state or sessions in process memory.
- Session lifetime: 7 days sliding, absolute max 30 days, rotate session ID on login, revoke on logout, "sign out of all devices" supported.

---

## 4. BUSINESS REGISTRATION AND ONBOARDING FROM SCRATCH

### 4.1 Rules
- Signing in creates **only a user**. **Do not auto-create a workspace or business**.
- A new user lands on **"Register your business"** with **every field empty**. Nothing pre-selected, nothing prefilled except Google profile data.
- Until `workspace.onboarding_status = 'complete'`, Studio, Calendar and Publishing are blocked and redirect to onboarding. The Home screen shows an honest empty state with the next step, not demo content.
- Onboarding autosaves drafts per step; the user can resume later.

---

## 5. REAL-TIME AND DYNAMIC DATA (replace everything demo)

- **Home, Calendar, Analytics, Channels** render **only database/API data**. Zero real data means an honest empty state, never sample items.
- **Festival/occasion strip:** remove the hardcoded Diwali banner. Build an **Occasions service** that returns upcoming occasions for the workspace's region and industry from a maintained data source.
- **Agent progress:** stream run events via SSE or WebSocket using Redis pub/sub.
- **Platform data:** account names, avatars, scopes and token health come from the connected APIs.
- **Analytics:** pulled from platform insights on a schedule; unavailable metrics are labeled "not available yet".

---

## 6. THE CORE FIX: BUSINESS-AWARE CREATIVE PIPELINE

### 6.1 Pipeline
```
Business Profile (from DB)
   -> Business Understanding Agent  -> CreativeDirection (stored)
   -> Brief builder (goal + format + occasion)
   -> Template Selector (scored, diversified) -> 3 distinct candidates
   -> Copywriter (industry tone, validated limits)
   -> Image Strategy (uploaded photos first; generate only when appropriate)
   -> Designer (fills/adapts template into layout spec)
   -> Renderer (HTML/CSS -> PNG/PDF)
   -> Geometry + contrast + contamination QA
   -> Design Critic (vision) -> revise loop (max 3)
   -> Quality Gate -> Human approval -> Publish
```

---

## 7. UI CHANGES REQUIRED
- Replace Home hero with real states.
- Remove pre-filled workspace name, hardcoded campaign brief, demo poster, broken image placeholder, static Diwali card, hardcoded channel counts.
- Studio brief form starts **empty**, with suggestions generated from the workspace's own CreativeDirection.
- Add Template/Style picker in Studio showing 3 distinct candidates.
- Add Brand and Business settings page.
