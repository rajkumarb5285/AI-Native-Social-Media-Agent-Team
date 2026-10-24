import sqlite3
from pathlib import Path

def run_migrations(db_path: str):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as con:
        # Runs table
        con.execute("""CREATE TABLE IF NOT EXISTS runs (
          id TEXT PRIMARY KEY, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          status TEXT NOT NULL, request_json TEXT NOT NULL, result_json TEXT,
          logs_json TEXT NOT NULL, approved INTEGER NOT NULL DEFAULT 0,
          retry_count INTEGER NOT NULL DEFAULT 0, tenant_id TEXT NOT NULL DEFAULT 'default'
        )""")
        
        # Check columns
        cursor = con.execute("PRAGMA table_info(runs)")
        cols = {row[1] for row in cursor.fetchall()}
        if "retry_count" not in cols:
            con.execute("ALTER TABLE runs ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 0")
        if "tenant_id" not in cols:
            con.execute("ALTER TABLE runs ADD COLUMN tenant_id TEXT NOT NULL DEFAULT 'default'")

        # Audit events table
        con.execute("""CREATE TABLE IF NOT EXISTS audit_events (
          id TEXT PRIMARY KEY, created_at TEXT NOT NULL, tenant_id TEXT NOT NULL,
          user_id TEXT NOT NULL, action TEXT NOT NULL, entity_id TEXT NOT NULL,
          details_json TEXT NOT NULL
        )""")

        # Social connections table
        con.execute("""CREATE TABLE IF NOT EXISTS connections (
          id TEXT PRIMARY KEY, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          tenant_id TEXT NOT NULL, platform TEXT NOT NULL, account_name TEXT NOT NULL,
          encrypted_access_token TEXT NOT NULL, encrypted_refresh_token TEXT,
          expires_at TEXT, scopes_json TEXT NOT NULL, is_active INTEGER NOT NULL DEFAULT 1
        )""")

        # Users table with strict security, MFA, and Google OAuth bindings
        con.execute("""CREATE TABLE IF NOT EXISTS users (
          id TEXT PRIMARY KEY, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
          role TEXT NOT NULL DEFAULT 'editor', tenant_id TEXT NOT NULL DEFAULT 'default',
          is_active INTEGER NOT NULL DEFAULT 1,
          mfa_enabled INTEGER NOT NULL DEFAULT 0,
          mfa_secret TEXT,
          mfa_backup_codes TEXT,
          google_id TEXT,
          google_sub TEXT UNIQUE,
          name TEXT,
          full_name TEXT,
          avatar_url TEXT,
          business_name TEXT,
          is_verified INTEGER NOT NULL DEFAULT 0,
          email_verified INTEGER NOT NULL DEFAULT 0,
          last_login_at TEXT
        )""")

        # Add columns if migrating existing DB
        user_cursor = con.execute("PRAGMA table_info(users)")
        u_cols = {row[1] for row in user_cursor.fetchall()}
        if "mfa_enabled" not in u_cols:
            con.execute("ALTER TABLE users ADD COLUMN mfa_enabled INTEGER NOT NULL DEFAULT 0")
        if "mfa_secret" not in u_cols:
            con.execute("ALTER TABLE users ADD COLUMN mfa_secret TEXT")
        if "mfa_backup_codes" not in u_cols:
            con.execute("ALTER TABLE users ADD COLUMN mfa_backup_codes TEXT")
        if "google_id" not in u_cols:
            con.execute("ALTER TABLE users ADD COLUMN google_id TEXT")
        if "google_sub" not in u_cols:
            con.execute("ALTER TABLE users ADD COLUMN google_sub TEXT")
        if "name" not in u_cols:
            con.execute("ALTER TABLE users ADD COLUMN name TEXT")
        if "full_name" not in u_cols:
            con.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
        if "avatar_url" not in u_cols:
            con.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
        if "business_name" not in u_cols:
            con.execute("ALTER TABLE users ADD COLUMN business_name TEXT")
        if "is_verified" not in u_cols:
            con.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER NOT NULL DEFAULT 0")
        if "email_verified" not in u_cols:
            con.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0")
        if "last_login_at" not in u_cols:
            con.execute("ALTER TABLE users ADD COLUMN last_login_at TEXT")

        # Unique index on google_sub
        con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_sub ON users(google_sub) WHERE google_sub IS NOT NULL")

        # Sessions table for stateful server-side sessions & secure cookie management
        con.execute("""CREATE TABLE IF NOT EXISTS sessions (
          id TEXT PRIMARY KEY,
          user_id TEXT NOT NULL,
          expires_at TEXT NOT NULL,
          user_agent TEXT,
          ip TEXT,
          created_at TEXT NOT NULL,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )""")
        con.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")

        # Short-lived OAuth state store with PKCE code_verifier (10 min TTL)
        con.execute("""CREATE TABLE IF NOT EXISTS oauth_states (
          state TEXT PRIMARY KEY,
          nonce TEXT NOT NULL,
          code_verifier TEXT NOT NULL,
          redirect_url TEXT NOT NULL,
          expires_at TEXT NOT NULL,
          created_at TEXT NOT NULL
        )""")

        # OTP Codes table for strict Multi-Factor Authentication & verification
        con.execute("""CREATE TABLE IF NOT EXISTS otp_codes (
          id TEXT PRIMARY KEY,
          user_id TEXT NOT NULL,
          challenge_token TEXT NOT NULL,
          otp_code TEXT NOT NULL,
          purpose TEXT NOT NULL,
          expires_at TEXT NOT NULL,
          used INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL
        )""")

        # Durable publication idempotency ledger. A reserved key is never silently retried
        # after an uncertain outcome, because the platform may already have created the post.
        con.execute("""CREATE TABLE IF NOT EXISTS publish_idempotency (
          tenant_id TEXT NOT NULL, platform TEXT NOT NULL, idempotency_key TEXT NOT NULL,
          status TEXT NOT NULL, result_json TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          PRIMARY KEY (tenant_id, platform, idempotency_key)
        )""")

        # Business profiles table (Multi-tenant business intake, brand kit, source facts & guardrails)
        con.execute("""CREATE TABLE IF NOT EXISTS business_profiles (
          tenant_id TEXT PRIMARY KEY,
          business_name TEXT NOT NULL,
          legal_name TEXT DEFAULT '',
          category TEXT NOT NULL DEFAULT '',
          industry_primary TEXT NOT NULL DEFAULT '',
          industry_sub TEXT DEFAULT '',
          offerings_description TEXT DEFAULT '',
          business_model TEXT NOT NULL DEFAULT 'physical_products',
          phone TEXT NOT NULL DEFAULT '',
          address TEXT NOT NULL DEFAULT '',
          website TEXT NOT NULL DEFAULT '',
          tagline TEXT NOT NULL DEFAULT '',
          rating TEXT NOT NULL DEFAULT '',
          review_count TEXT NOT NULL DEFAULT '',
          logo_url TEXT,
          primary_color TEXT NOT NULL DEFAULT '#6366f1',
          secondary_color TEXT DEFAULT '#f59e0b',
          accent_color TEXT DEFAULT '#10b981',
          background_color TEXT DEFAULT '#0f172a',
          display_font TEXT DEFAULT 'Inter',
          body_font TEXT DEFAULT 'Inter',
          positioning TEXT DEFAULT 'mid',
          personality_json TEXT DEFAULT '{}',
          audience_json TEXT DEFAULT '{}',
          goals_json TEXT DEFAULT '[]',
          competitors_json TEXT DEFAULT '[]',
          source_facts_json TEXT DEFAULT '{}',
          guardrails_json TEXT DEFAULT '{}',
          region TEXT DEFAULT 'US',
          timezone TEXT DEFAULT 'UTC',
          onboarding_status TEXT NOT NULL DEFAULT 'pending',
          approval_mode TEXT NOT NULL DEFAULT 'human',
          gmb_location_id TEXT,
          creative_direction_json TEXT DEFAULT '{}',
          updated_at TEXT NOT NULL
        )""")

        # Add missing columns to business_profiles dynamically
        bp_cursor = con.execute("PRAGMA table_info(business_profiles)")
        bp_cols = {row[1] for row in bp_cursor.fetchall()}
        columns_to_ensure = [
            ("legal_name", "TEXT DEFAULT ''"),
            ("industry_primary", "TEXT NOT NULL DEFAULT ''"),
            ("industry_sub", "TEXT DEFAULT ''"),
            ("offerings_description", "TEXT DEFAULT ''"),
            ("business_model", "TEXT NOT NULL DEFAULT 'physical_products'"),
            ("secondary_color", "TEXT DEFAULT '#f59e0b'"),
            ("accent_color", "TEXT DEFAULT '#10b981'"),
            ("background_color", "TEXT DEFAULT '#0f172a'"),
            ("display_font", "TEXT DEFAULT 'Inter'"),
            ("body_font", "TEXT DEFAULT 'Inter'"),
            ("positioning", "TEXT DEFAULT 'mid'"),
            ("personality_json", "TEXT DEFAULT '{}'"),
            ("audience_json", "TEXT DEFAULT '{}'"),
            ("goals_json", "TEXT DEFAULT '[]'"),
            ("competitors_json", "TEXT DEFAULT '[]'"),
            ("source_facts_json", "TEXT DEFAULT '{}'"),
            ("guardrails_json", "TEXT DEFAULT '{}'"),
            ("region", "TEXT DEFAULT 'US'"),
            ("timezone", "TEXT DEFAULT 'UTC'"),
            ("onboarding_status", "TEXT NOT NULL DEFAULT 'pending'"),
            ("approval_mode", "TEXT NOT NULL DEFAULT 'human'"),
            ("creative_direction_json", "TEXT DEFAULT '{}'")
        ]
        for col_name, col_def in columns_to_ensure:
            if col_name not in bp_cols:
                con.execute(f"ALTER TABLE business_profiles ADD COLUMN {col_name} {col_def}")

        # Offerings table (Products or Services per tenant)
        con.execute("""CREATE TABLE IF NOT EXISTS offerings (
          id TEXT PRIMARY KEY,
          tenant_id TEXT NOT NULL,
          name TEXT NOT NULL,
          description TEXT DEFAULT '',
          price TEXT DEFAULT '',
          is_bestseller INTEGER NOT NULL DEFAULT 0,
          image_url TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          FOREIGN KEY (tenant_id) REFERENCES business_profiles(tenant_id) ON DELETE CASCADE
        )""")
        con.execute("CREATE INDEX IF NOT EXISTS idx_offerings_tenant ON offerings(tenant_id)")

        # Brand Assets table (Logos, Cutouts, Photos, Style references)
        con.execute("""CREATE TABLE IF NOT EXISTS brand_assets (
          id TEXT PRIMARY KEY,
          tenant_id TEXT NOT NULL,
          asset_type TEXT NOT NULL,
          url TEXT NOT NULL,
          meta_json TEXT DEFAULT '{}',
          created_at TEXT NOT NULL,
          FOREIGN KEY (tenant_id) REFERENCES business_profiles(tenant_id) ON DELETE CASCADE
        )""")
        con.execute("CREATE INDEX IF NOT EXISTS idx_brand_assets_tenant ON brand_assets(tenant_id)")

        # Scheduled festival & promotional posts queue
        con.execute("""CREATE TABLE IF NOT EXISTS scheduled_posts (
          id TEXT PRIMARY KEY,
          tenant_id TEXT NOT NULL,
          festival_id TEXT,
          title TEXT NOT NULL,
          content TEXT NOT NULL,
          poster_url TEXT,
          platforms_json TEXT NOT NULL,
          scheduled_date TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'scheduled',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )""")

        # System settings for runtime secrets & OAuth client credentials
        con.execute("""CREATE TABLE IF NOT EXISTS system_settings (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )""")
