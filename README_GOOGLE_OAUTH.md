# Real Google OAuth 2.0 & OpenID Connect (PKCE) Setup Guide

This guide walks you through configuring **Sign in with Google** using real Google OAuth 2.0 and OpenID Connect (OIDC) with **Server-Side Authorization Code Flow and PKCE (RFC 7636)**, strict session management, and Google Authenticator TOTP Multi-Factor Authentication.

---

## 1. Google Cloud Console Setup (Step-by-Step)

### Step 1: Create a Google Cloud Project
1. Navigate to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click the project dropdown in the top navigation bar and select **New Project**.
3. Name your project (e.g. `Nexus Studio Production`) and click **Create**.

### Step 2: Configure OAuth Consent Screen
1. In the sidebar, navigate to **APIs & Services** > **OAuth consent screen**.
2. Select User Type:
   - **External**: For any Gmail or Google Workspace user.
   - **Internal**: Restricted to users in your Google Workspace organization.
3. Click **Create**.
4. Fill in the App Information:
   - **App name**: `Nexus Studio`
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
5. Click **Save and Continue**.
6. **Scopes**:
   - Click **Add or Remove Scopes**.
   - Select the 3 standard OIDC scopes:
     - `.../auth/userinfo.email` (`email`)
     - `.../auth/userinfo.profile` (`profile`)
     - `openid`
   - Click **Update** then **Save and Continue**.
7. If your app is in "Testing" mode, add your Gmail account under **Test users**.

### Step 3: Create OAuth 2.0 Client Credentials
1. In the sidebar, navigate to **APIs & Services** > **Credentials**.
2. Click **Create Credentials** > **OAuth client ID**.
3. Set **Application type** to: `Web application`.
4. Set **Name** to: `Nexus Studio Web Client`.
5. Under **Authorized JavaScript origins**, add:
   - `http://localhost:8000`
   - `http://127.0.0.1:8000`
   - *(Your production domain if deployed, e.g. `https://your-domain.com`)*
6. Under **Authorized redirect URIs**, add the exact callback URL:
   - `http://localhost:8000/auth/google/callback`
   - `http://127.0.0.1:8000/auth/google/callback`
   - *(Your production callback, e.g. `https://your-domain.com/auth/google/callback`)*
7. Click **Create**.
8. Copy your **Client ID** and **Client Secret**.

---

## 2. Environment Configuration

Add your credentials to your `.env` file (copied from `.env.example`):

```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
SESSION_SECRET=replace-with-a-random-32-byte-hex-string
FRONTEND_URL=http://localhost:8000
API_BASE_URL=http://localhost:8000
```

> **Security Rule**: `GOOGLE_CLIENT_SECRET` is stored ONLY on the backend server and never exposed to the frontend browser bundle.

---

## 3. Architecture & Authentication Flow

```
[User Browser]                   [FastAPI Backend]                 [Google OAuth 2.0]
      |                                  |                                  |
      |--- 1. Clicks "Sign in with Google"                                  |
      |    GET /auth/google/login ------>|                                  |
      |                                  |--- 2. Generates PKCE pair        |
      |                                  |    (verifier, challenge),        |
      |                                  |    state, nonce. Stores in DB    |
      |                                  |    (10 min TTL).                 |
      |<-- 3. 302 Redirect to Google ----|                                  |
      |    (with code_challenge, nonce)  |                                  |
      |                                                                     |
      |--- 4. Consents on accounts.google.com ----------------------------->|
      |                                                                     |
      |<-- 5. 302 Redirect to callback with code & state -------------------|
      |                                  |                                  |
      |--- 6. GET /auth/google/callback?code=...&state=... ---------------->|
                                         |                                  |
                                         |--- 7. Validates state in DB      |
                                         |--- 8. Exchanges code + verifier  |
                                         |       via POST /token ---------->|
                                         |<-- 9. Returns id_token & tokens -|
                                         |                                  |
                                         |--- 10. Strictly validates ID:    |
                                         |    - Google JWKS signature       |
                                         |    - iss == accounts.google.com  |
                                         |    - aud == GOOGLE_CLIENT_ID     |
                                         |    - exp in future               |
                                         |    - nonce matches DB state      |
                                         |    - email_verified == True      |
                                         |                                  |
                                         |--- 11. Lookup by 'sub' (stable)  |
                                         |    (or link safe if verified)    |
                                         |--- 12. Creates/rotates session   |
                                         |    Sets httpOnly session cookie  |
      |<-- 13. 303 Redirect to /?auth_success=true -------------------------|
      |
[Authenticated App Loaded]
```

---

## 4. Endpoints Reference

| Endpoint | Method | Auth Required | Description |
|---|---|---|---|
| `/auth/google/login` | GET | No | Initiates PKCE OAuth code flow, generates state & nonce |
| `/auth/google/callback`| GET | No | Exchanges code, verifies ID token claims, starts session |
| `/auth/me` | GET | Yes (Cookie / Bearer) | Returns profile of currently authenticated user |
| `/auth/logout` | POST | Yes | Destroys session in DB and wipes `httpOnly` cookie |
| `/auth/export` | GET | Yes | GDPR / data privacy export of user data & activity |
| `/auth/me` | DELETE | Yes | Deletes account, active sessions, and personal workspace |

---

## 5. Running Automated Tests

Run the full Google OAuth test suite:

```bash
pytest tests/test_google_oauth.py -v
```

Tests cover:
- Invalid or expired OAuth state parameter (HTTP 400 rejection).
- Expired / bad authorization code handling.
- Wrong audience / client ID mismatch in ID token (HTTP 401 rejection).
- Unverified Google email (`email_verified == False`) rejection.
- Nonce mismatch prevention (replay attack protection).
- Happy path: Code exchange, user lookup by permanent `google_sub`, session rotation, and `/auth/me`.
- Strict Multi-Factor Authentication challenge enforcement.
