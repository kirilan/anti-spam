#!/bin/bash
set -e

echo "Starting backend entrypoint..."

# Extract database connection info from DATABASE_URL
# Format: postgresql://user:password@host:port/dbname
DB_HOST=$(echo $DATABASE_URL | sed -n 's|.*@\([^:]*\):.*|\1|p')
DB_USER=$(echo $DATABASE_URL | sed -n 's|.*://\([^:]*\):.*|\1|p')
DB_PASS=$(echo $DATABASE_URL | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p')
DB_NAME=$(echo $DATABASE_URL | sed -n 's|.*/\([^?]*\).*|\1|p')

# Wait for database to be ready
echo "Waiting for database at $DB_HOST..."
until PGPASSWORD=$DB_PASS psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "  Database is unavailable - sleeping"
  sleep 2
done
echo "✓ Database is ready"

RUN_DB_MIGRATIONS=${RUN_DB_MIGRATIONS:-true}

if [ "$RUN_DB_MIGRATIONS" = "true" ] || [ "$RUN_DB_MIGRATIONS" = "1" ]; then
  echo ""
  echo "Running database migrations..."
  if python migrations/run_migrations.py; then
      echo "✓ Migrations complete"
  else
      echo "✗ Migrations failed"
      exit 1
  fi
else
  echo ""
  echo "Skipping database migrations (RUN_DB_MIGRATIONS=$RUN_DB_MIGRATIONS)"
fi

echo ""
echo "Starting application server..."
exec "$@"
