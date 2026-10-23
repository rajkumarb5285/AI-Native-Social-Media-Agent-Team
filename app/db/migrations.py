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
          full_name TEXT,
          business_name TEXT,
          is_verified INTEGER NOT NULL DEFAULT 0
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
        if "full_name" not in u_cols:
            con.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
        if "business_name" not in u_cols:
            con.execute("ALTER TABLE users ADD COLUMN business_name TEXT")
        if "is_verified" not in u_cols:
            con.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER NOT NULL DEFAULT 0")

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

        # Business profiles table (Dhanda AI Marketing profile, GMB details, local branding)
        con.execute("""CREATE TABLE IF NOT EXISTS business_profiles (
          tenant_id TEXT PRIMARY KEY,
          business_name TEXT NOT NULL,
          category TEXT NOT NULL DEFAULT 'General Business',
          phone TEXT NOT NULL DEFAULT '',
          address TEXT NOT NULL DEFAULT '',
          website TEXT NOT NULL DEFAULT '',
          tagline TEXT NOT NULL DEFAULT '',
          rating TEXT NOT NULL DEFAULT '4.9 ★★★★★',
          review_count TEXT NOT NULL DEFAULT '120+ Google Reviews',
          logo_url TEXT,
          primary_color TEXT NOT NULL DEFAULT '#6366f1',
          gmb_location_id TEXT,
          updated_at TEXT NOT NULL
        )""")

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
