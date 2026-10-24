import sqlite3
import os
import sys

def purge_database(db_path: str = "agent_runs.db"):
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist.")
        return

    print(f"Purging all demo data from {db_path}...")
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    tables_to_wipe = [
        "runs",
        "audit_events",
        "connections",
        "sessions",
        "oauth_states",
        "otp_codes",
        "publish_idempotency",
        "offerings",
        "brand_assets",
        "scheduled_posts",
        "business_profiles"
    ]

    for table in tables_to_wipe:
        try:
            cur.execute(f"DELETE FROM {table}")
            print(f"  [OK] Cleared table: {table}")
        except sqlite3.OperationalError as e:
            print(f"  [-] Table {table} not found or error: {e}")

    # For users: reset onboarding status and business names
    try:
        cur.execute("UPDATE users SET business_name = NULL, last_login_at = NULL")
        print("  [OK] Reset users business_name and session state.")
    except Exception as e:
        print(f"  - User reset error: {e}")

    con.commit()
    con.close()
    print("Database purged cleanly. Ready for fresh onboarding!")

if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "agent_runs.db"
    purge_database(db_file)
