#!/usr/bin/env bash
set -euo pipefail

# Create data dir if needed
mkdir -p /data

# Run migrations only when RUN_MIGRATIONS is set to "1" (default: 1)
if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  echo "Running migrations..."
  python manage.py migrate --noinput
else
  echo "RUN_MIGRATIONS != 1, skipping migrations"
fi

# Start the application
exec gunicorn --bind 0.0.0.0:${PORT} sist_project.wsgi:application
