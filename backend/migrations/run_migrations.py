#!/usr/bin/env python3
"""
Database migration runner - automatically applies pending migrations
"""

import os
import sys
from pathlib import Path

import psycopg2

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/antispam")


def get_db_connection():
    """Create database connection from DATABASE_URL"""
    # Parse postgres://user:pass@host:port/dbname
    url = DATABASE_URL.replace("postgresql://", "").replace("postgres://", "")

    if "@" in url:
        auth, rest = url.split("@")
        user, password = auth.split(":")
        host_port_db = rest
    else:
        user = "postgres"
        password = "postgres"
        host_port_db = url

    if "/" in host_port_db:
        host_port, dbname = host_port_db.split("/")
    else:
        host_port = host_port_db
        dbname = "antispam"

    if ":" in host_port:
        host, port = host_port.split(":")
    else:
        host = host_port
        port = "5432"

    return psycopg2.connect(host=host, port=port, database=dbname, user=user, password=password)


def create_migrations_table(conn):
    """Create migrations tracking table if it doesn't exist"""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                migration_file VARCHAR(255) NOT NULL UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()
    print("✓ Migrations tracking table ready")


def get_applied_migrations(conn):
    """Get list of already applied migrations"""
    with conn.cursor() as cur:
        cur.execute("SELECT migration_file FROM schema_migrations ORDER BY migration_file")
        return {row[0] for row in cur.fetchall()}


def get_pending_migrations(migrations_dir):
    """Get list of all .sql migration files"""
    migrations = []
    for file in sorted(Path(migrations_dir).glob("*.sql")):
        migrations.append(file.name)
    return migrations


def apply_migration(conn, migration_file, migrations_dir):
    """Apply a single migration file"""
    filepath = Path(migrations_dir) / migration_file

    print(f"  Applying {migration_file}...", end=" ")

    try:
        with open(filepath) as f:
            sql = f.read()

        with conn.cursor() as cur:
            # Execute the migration SQL
            cur.execute(sql)

            # Record that this migration was applied
            cur.execute(
                "INSERT INTO schema_migrations (migration_file) VALUES (%s)", (migration_file,)
            )

        conn.commit()
        print("✓")
        return True

    except Exception as e:
        conn.rollback()
        print(f"✗ Failed: {e}")
        return False


def run_migrations():
    """Main migration runner"""
    migrations_dir = Path(__file__).parent

    print("=" * 60)
    print("Database Migration Runner")
    print("=" * 60)

    try:
        # Connect to database
        print("\nConnecting to database...")
        conn = get_db_connection()
        print("✓ Connected")

        # Create migrations table
        create_migrations_table(conn)

        # Get applied and pending migrations
        applied = get_applied_migrations(conn)
        all_migrations = get_pending_migrations(migrations_dir)
        pending = [m for m in all_migrations if m not in applied]

        print("\nMigrations status:")
        print(f"  Already applied: {len(applied)}")
        print(f"  Pending: {len(pending)}")

        if not pending:
            print("\n✓ All migrations are up to date!")
            return True

        # Apply pending migrations
        print(f"\nApplying {len(pending)} pending migration(s):")

        success_count = 0
        for migration in pending:
            if apply_migration(conn, migration, migrations_dir):
                success_count += 1
            else:
                print("\n✗ Migration failed. Stopping.")
                return False

        print(f"\n✓ Successfully applied {success_count} migration(s)")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
