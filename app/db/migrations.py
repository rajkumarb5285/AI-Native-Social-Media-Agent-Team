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

        # Users table
        con.execute("""CREATE TABLE IF NOT EXISTS users (
          id TEXT PRIMARY KEY, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
          role TEXT NOT NULL DEFAULT 'editor', tenant_id TEXT NOT NULL DEFAULT 'default',
          is_active INTEGER NOT NULL DEFAULT 1
        )""")
