# Database Migrations

This directory contains SQL migration files that automatically run when the backend container starts.

## How It Works

1. **Automatic on Startup**: When you start the backend container (`docker-compose up`), migrations run automatically
2. **Migration Tracking**: A `schema_migrations` table tracks which migrations have been applied
3. **Safe to Restart**: Running migrations multiple times is safe - already-applied migrations are skipped
4. **Sequential Order**: Migrations run in filename order (001, 002, 003, etc.)

## When You Pull Updates

If you pull new code with database changes, just restart your containers:

```bash
docker-compose down
docker-compose up --build
```

The migrations will run automatically during startup.

## Migration Files

Migration files are simple SQL files with sequential numbering:

- `001_add_scanner_enhancements.sql`
- `002_add_email_sending_fields.sql`
- `003_add_broker_responses.sql`
- `004_add_request_retry_fields.sql`
- `005_add_is_admin_to_users.sql`

## Creating New Migrations

1. Create a new `.sql` file with the next number: `006_your_migration_name.sql`
2. Write your SQL (ALTER TABLE, CREATE TABLE, etc.)
3. Commit the file
4. The migration will run automatically when users restart their containers

## Manual Migration Run

If you need to run migrations manually without restarting:

```bash
docker exec -it antispam-backend-1 python migrations/run_migrations.py
```

## Checking Migration Status

The migration runner shows:
- How many migrations are already applied
- How many are pending
- Which migrations were just applied

Example output:
```
==========================================================
Database Migration Runner
==========================================================

Connecting to database...
✓ Connected
✓ Migrations tracking table ready

Migrations status:
  Already applied: 5
  Pending: 0

✓ All migrations are up to date!
==========================================================
```

## Troubleshooting

**Migration fails**: Check the backend container logs:
```bash
docker-compose logs backend
```

**Start fresh**: If you need to reset the database completely:
```bash
docker-compose down -v  # WARNING: Deletes all data!
docker-compose up --build
```

**Check which migrations are applied**:
```bash
docker exec -it antispam-db-1 psql -U postgres -d antispam -c "SELECT * FROM schema_migrations ORDER BY applied_at;"
```
