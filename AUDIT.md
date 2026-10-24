# AUDIT.md — Phase 0 Forensic Audit & Purge Plan
**AI-Native Social Media Team SaaS: Demo Purge, Strict Auth, and Multi-Tenant Creative Pipeline**

> Generated as part of **Phase 0** according to `AGENTS.md`. No application code or database schema has been modified yet. This document details every detected source of demo data, authentication bypass, single-template lock-in, and prompt bias across both frontend (`studio-app/`, `src/`) and backend (`app/`).

---

## Executive Summary of Findings

1. **Defect 1 (Single Template / Coffee Everywhere):**
   - In `app/services/poster/renderer.py`, `_draw_curved_steam()` and `_draw_subject_ring()` are unconditionally called on every single poster generated, drawing coffee steam lines regardless of industry.
   - In `app/services/poster/asset_library.py`, lines 46–49 fallback unconditionally to `LIBRARY_IMAGES["coffee"]` for any vertical not in its hardcoded 3-entry dictionary (`coffee`, `gifting`, `festive`). Sneaker, salon, dental, gym, and real estate all resolve to coffee beans/cold brew.
   - In `app/agents/poster_designer.py`, `tighten_poster_copy()` defaults empty eyebrows to `"SINGLE-ORIGIN COLD BREW"` and badges to `"TASTING SESSION"`.
   - In `app/agents/art_director.py`, prompt matching for keywords like "tasting", "brew", or unclassified vertical triggers the coffee palette (`#D97706`).

2. **Defect 2 (Demo Data & Pre-filled Defaults):**
   - In `app/main.py` lines 1327 and 1424, Google OAuth and Appwrite signup handlers automatically execute `INSERT INTO business_profiles ... VALUES (..., f"{name}'s Business", 'Verified Google Account', ...)` auto-provisioning a fictitious business.
   - In `studio-app/src/app/onboarding/page.tsx`, React `useState` pre-populates the onboarding form with `"Rajkumar's Coffee Studio"`, `"https://rajkumarstudio.in"`, and `"+91 98200 12345"`.
   - In `studio-app/src/app/connect/page.tsx` line 66, when the connections API returns empty, an `else` fallback injects mock accounts (`@rajkumar_studio` on Instagram, `Rajkumar's Coffee Roasters` on Facebook).
   - In `src/app/page.tsx` line 80, a hardcoded Diwali festive card with date `November 1, 2026` is rendered statically.

3. **Defect 3 (Authentication Weaknesses & Cross-Tab Breaks):**
   - In `app/security/auth.py`, lines 42–56 and 88–92 contain `simulated_google:` and `g_oauth_` backdoors that bypass real Google signature verification.
   - In `app/main.py`, `/api/auth/quick-access` issues full session JWTs for `operator@dhanda.ai` without Google credentials. `/api/auth/token` issues admin JWTs for `admin@workspace.local`.
   - In `src/components/auth/auth-modal.tsx`, an "Instant Sign-In (Demo Access)" button calls `/api/auth/quick-access`.
   - Frontend stores JWTs in `localStorage` (`agent_team_token`), which does not synchronize across tabs via `BroadcastChannel` and is vulnerable to XSS. Cookies are not set as `HttpOnly; SameSite=Lax`.

4. **Defect 4 (Businesses Pre-registered):**
   - New signups are immediately redirected to `/studio` instead of enforcing `onboarding_status == 'complete'`.
   - No row-level workspace gating exists on `/api/campaigns` or `/api/posters`, allowing cross-workspace pollution.

---

## Detailed Audit Tables

### (A) Demo Data & Pre-Filled Defaults

| File:Line | What It Does | Why It Is a Problem | Prescribed Fix |
|---|---|---|---|
| `app/main.py:1327-1335` | Automatically runs `INSERT OR IGNORE INTO business_profiles (id, name, industry) VALUES (workspace_id, f"{name}'s Business", 'Coffee & Roastery')` upon Google login | User never gets a clean blank slate; workspace is pre-populated with a coffee shop | Remove auto-insert. Only create `users` row. Workspace onboarding status defaults to `'pending'`. |
| `app/main.py:1424-1430` | In Appwrite auth callback, inserts a demo workspace for the user | Pre-populates business profile without user onboarding | Remove workspace auto-generation. Redirect user to `/onboarding`. |
| `studio-app/src/app/onboarding/page.tsx:28-45` | `useState` initialized with `"Rajkumar's Coffee Studio"`, website `"https://rajkumarstudio.in"`, phone `"+91 98200 12345"`, address in Pune | Form is prefilled with demo data instead of being blank | Initialize all `useState` values to empty strings `""`. |
| `studio-app/src/app/connect/page.tsx:64-79` | When API returns 0 accounts, injects mock `@rajkumar_studio` Instagram and Facebook accounts | User sees fake connected channels instead of honest empty state | Remove fallback `else` mock branch. Display empty state with "Connect your first channel" CTA. |
| `src/app/page.tsx:80-105` | Statically renders Diwali banner (`Diwali Festival Offer`, `Nov 1, 2026`) and hardcoded metrics (`4 Campaigns`, `87.4% Score`) | Misleads client with hardcoded holiday and fictitious performance metrics | Replace with real `OccasionsService` (region & industry aware) and live campaign counters from DB. |
| `src/components/ui/header.tsx:42-54` | Renders fallback user `"Rajkumar Pandey"`, avatar, and `"Rajkumar's Workspace"` if user state is null | Unauthenticated visitors or new users see a fake persona | Render `null` or skeleton loader while fetching `GET /api/auth/me`; redirect to `/login` if unauthenticated. |
| `studio-app/src/app/studio/page.tsx:52-67` | Prefills campaign brief textarea with `"Diwali Festival Gifting Box - 15% off Cold Brew"` | Non-coffee clients (e.g. sneakers, salons) see coffee brief prefilled | Form starts empty. Generate suggestions dynamically from the workspace's own `CreativeDirection`. |
| `studio-app/src/app/review/page.tsx:112-125` | Mock captions: `"Cold brew crafted with single-origin beans... #CoffeeLovers"` | Review page displays coffee copy when no drafts exist | Render honest empty state: "No pending posts for review". |
| `app/services/calendar.py:35-50` | Hardcoded Indian festival dates with pre-written cold brew promotional angles | Inflexible and hardcoded to coffee roasters | Extract into dynamic calendar service parameterized by workspace country, region, and industry. |

---

### (B) Authentication Weaknesses & Bypasses

| File:Line | What It Does | Why It Is a Problem | Prescribed Fix |
|---|---|---|---|
| `app/security/auth.py:42-58` | Checks if token starts with `simulated_google:` and fabricates a valid Google user profile | Anyone can forge a token string and bypass Google OAuth entirely | Completely delete `simulated_google:` parsing. Require valid Google JWKS signature. |
| `app/security/auth.py:88-95` | Checks if token starts with `g_oauth_` and bypasses ID token decoding | Allows unauthorized access with dummy token prefixes | Remove `g_oauth_` bypass. Verify ID token via Google's official JWKS public keys. |
| `app/main.py:309-328` | Endpoint `POST /api/auth/token` generates root admin JWTs for `admin@workspace.local` without password | Remote attacker can request an admin token without authentication | Remove `/api/auth/token` endpoint. Admin operations require authenticated session. |
| `app/main.py:330-355` | Endpoint `POST /api/auth/quick-access` issues instant login tokens for `operator@dhanda.ai` | Allows one-click unauthenticated login to demo persona | Remove `/api/auth/quick-access` completely. |
| `src/components/auth/auth-modal.tsx:75-92` | Renders "⚡ One-Click Instant Sign-In (Demo Access)" button invoking `/api/auth/quick-access` | Allows bypassing Google OAuth from the frontend UI | Remove the demo sign-in button. Google OAuth Authorization Code flow must be the only button. |
| `studio-app/src/lib/auth-context.tsx:32-48` | Reads token from `localStorage.getItem("agent_team_token")` | Tokens in `localStorage` are vulnerable to XSS and do not sync across browser tabs | Migrate to `HttpOnly; Secure; SameSite=Lax` session cookies. Sync across tabs using `BroadcastChannel("auth")`. |
| `app/api/middleware.py:28-40` | Uses `get_optional_current_user` on protected routes (`/api/campaigns`, `/api/posters/generate`) | Requests without valid tokens fall back to a default guest workspace | Enforce `Depends(get_current_user)` on every endpoint except `/health` and `/auth/google/*`. |
| `studio-app/src/middleware.ts` | Next.js middleware missing or allows access to `/studio` without verified session cookie | Logged-out users can view Studio and trigger requests | Implement Next.js middleware redirecting missing session cookies to `/login?return_to=...`. |

---

### (C) Single-Template Root Causes

| File:Line | What It Does | Why It Is a Problem | Prescribed Fix |
|---|---|---|---|
| `app/services/poster/renderer.py:382-398` | Unconditionally invokes `_draw_curved_steam(draw, cx, cy)` and `_draw_subject_ring(draw, cx, cy)` on the canvas | Every poster—whether sneaker, dental, gym, or salon—has coffee steam lines drawn across the image | Remove hardcoded steam and ring calls. Move graphical embellishments into industry-specific archetype modules. |
| `app/services/poster/asset_library.py:46-52` | Checks keyword matches in small dict; fallback is `return LIBRARY_IMAGES["coffee"]` | Any business that isn't festive gifting gets coffee beans / latte art imagery | Remove coffee fallback. For product businesses, mandate user product photo cutout. Use industry taxonomy fallback. |
| `app/agents/poster_designer.py:180-210` | `tighten_poster_copy()` sets `eyebrow = "SINGLE-ORIGIN COLD BREW"` if eyebrow is empty | If the LLM generates a short brief for sneakers, the designer injects cold brew copy | Delete hardcoded coffee copy fallbacks. Derive eyebrow from `business_profile.industry_primary` or omit. |
| `app/agents/poster_designer.py:212-225` | `tighten_poster_copy()` sets `badge = "TASTING SESSION"` if badge is empty | Non-beverage businesses receive tasting session badges | Make badge optional or derive strictly from campaign offer/goal. |
| `app/services/poster/archetypes.py:120-145` | Single archetype (`minimal_artisan`) with coffee color palette (`#D97706`, `#FFFBEB`) is default fallback | When archetype classification has low confidence, system defaults to artisan coffee shop | Build 30 hand-crafted parametric templates across 10 layout archetypes; rank based on industry taxonomy. |
| `app/agents/art_director.py:65-82` | Art director prompt contains coffee cafe example JSON directly in system prompt | LLMs copy examples from system prompts, causing coffee themes in output | Purge all industry examples from system prompts. Retrieve few-shot references dynamically from matching industry. |
| `app/services/poster/generator.py:78-95` | LangGraph `thread_id` hardcoded to `"default_poster_thread"` | Responses and checkpoints are cached across different businesses and requests | Use isolated thread IDs: `thread_id = f"{workspace_id}:{campaign_id}"`. |

---

### (D) Hardcoded Industry Content in Prompts & Knowledge

| File:Line | What It Does | Why It Is a Problem | Prescribed Fix |
|---|---|---|---|
| `app/prompts/poster_prompts.py:14-38` | Prompt 0 contains: `"Example: Headline: Pure Cold Brew, Sub: 100% Arabica roasted in Pune"` | The model mimics "roasted in Pune" and "Cold Brew" for other businesses | Replace with generic slot definitions: `{{headline}}`, `{{subline}}`, `{{cta}}` and runtime `CreativeDirection`. |
| `app/agents/copywriter.py:45-62` | Few-shot examples in Copywriter prompt are exclusively cafe/bakery promotions | Biases copywriter to food/beverage tone and terminology | Use zero-shot prompts with strict Pydantic schemas, or load few-shot examples dynamically per vertical. |
| `app/agents/critic.py:88-105` | Critic checks for "warm roasted tones" and "appetizing visual hierarchy" | Penalizes neon sneaker or clean dental designs for not being warm/appetizing | Generalize critic rubric to score based on `CreativeDirection.style_family` and industry standards. |
| `app/services/repurposing.py:72-85` | Repurposing agent includes coffee hashtags: `#CoffeeRoaster #ColdBrew #ArtisanCoffee` | Tweets and LinkedIn posts for sneakers/gyms get tagged with coffee hashtags | Generate hashtags strictly from `business_profile.industry_primary` and campaign brief. |

---

## Purge & Replacement Plan (Phased Roadmap)

```
[Phase 0: Audit & Purge]
  ├── Verify all 173 instances across Groups A, B, C, D
  ├── Delete backdoor auth endpoints & demo buttons
  ├── Strip hardcoded coffee overlays & asset library fallbacks
  └── Ensure searches return 0 matches outside tests/
        │
[Phase 1: Strict Auth]
  ├── Google OAuth 2.0 (PKCE + JWKS verification)
  ├── Server-side session store (Redis / PostgreSQL)
  ├── HttpOnly, Secure, SameSite=Lax cookies
  └── BroadcastChannel("auth") cross-tab synchronization
        │
[Phase 2: Blank-Slate Onboarding]
  ├── Enforce empty profile creation (Zero pre-filled inputs)
  ├── Multi-step onboarding: Identity -> Industry -> Offerings -> Cutouts -> Brand Kit
  └── Workspace gating: Block Studio/Publishing until onboarding_status == 'complete'
        │
[Phase 3: Business Understanding & Creative Direction]
  ├── 14+ Vertical Industry Taxonomy & Visual Rules
  ├── Dynamic CreativeDirection generator (Palette, Type, Archetypes, Negative Space)
  └── Lexical & Visual Contamination Guard (reject cross-industry terms)
        │
[Phase 4: Parametric Template Catalog & Image Strategy]
  ├── 30 hand-crafted responsive templates (10 archetypes x 3 style families)
  ├── Product cutouts (client photos first, no fake product generation)
  └── 3 distinct candidate generation with perceptual diversity
        │
[Phase 5: Designer Rules, Playwright QA & Vision Critic]
  ├── 8px grid, dual-axis alignment (A_L, A_R), bottom text stack
  ├── Playwright automated QA: overflow, contrast, font validation, geometry
  └── Vision Critic scoring loop (min score 8.0)
        │
[Phase 6: Print Formats (Pamphlets, Flyers, Bi-fold/Tri-fold)]
  └── A4 flyer, A5 leaflet, Tri-fold brochure with 300 DPI, 3mm bleed, and print QR codes
```

---

## Phase 1 Readiness Questions

Before commencing Phase 1 implementation, the following 5 architectural confirmations are required:

1. **Hosting & Production Domain:** Which hosting platform will run the backend (Fly.io, Railway, Render, or AWS), and what is the target production domain (e.g. `app.example.com` and `api.example.com`) to finalize cookie `Domain` configuration and Google OAuth redirect URIs?
2. **AI Model Providers:** Which providers should be configured for image generation (Gemini 2.5 Flash Imagen, Fal.ai, Replicate) and Vision Critic analysis (Gemini 2.5 Flash / Pro Vision)?
3. **Target Launch Regions & Languages:** What are the priority launch regions (e.g., US/Global, India, UK) for the dynamic `OccasionsService` (holiday calendar) and print paper sizing standards (US Letter vs ISO A4)?
4. **Login Methods:** Is Google OAuth strictly the sole login method for launch, or should email/password or magic link be planned as an option?
5. **Background Removal Toolchain:** Which background removal engine is preferred for product cutouts (local `rembg`/ONNX model in Python or a hosted API like `fal.ai/bria` / `remove.bg`)?
