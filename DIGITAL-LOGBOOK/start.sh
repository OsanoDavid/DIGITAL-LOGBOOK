#!/usr/bin/env bash
set -euo pipefail

# Run migrations only when RUN_MIGRATIONS is set to "1" (default: 1)
if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  echo "Running migrations..."
  python manage.py migrate --noinput
else
  echo "RUN_MIGRATIONS != 1, skipping migrations"
  # Safety: if the database has no applied migrations, abort to avoid running
  # an app against an empty DB unintentionally. This prevents accidental
  # deployments that skip migrations on a fresh database.
    # Print diagnostics: resolved DB path and applied migration count
    echo "--- DATABASE DIAGNOSTICS ---"
    python - <<PY
  import os
  from django.conf import settings
  try:
    db_name = settings.DATABASES['default'].get('NAME')
  except Exception:
    db_name = os.environ.get('SQLITE_DB_PATH', 'unknown')
  print('Resolved DB path:', db_name)
  try:
    from django.db.migrations.recorder import MigrationRecorder
    print('Applied migrations:', MigrationRecorder.Migration.objects.count())
  except Exception as exc:
    print('Applied migrations: (unavailable)', exc)
  PY

    APPLIED_COUNT=$(python - <<PY
  from django.db.migrations.recorder import MigrationRecorder
  try:
    print(MigrationRecorder.Migration.objects.count())
  except Exception:
    print(0)
  PY
  )
  if [ "${APPLIED_COUNT}" = "0" ]; then
    echo "ERROR: No migrations are recorded in the database and RUN_MIGRATIONS=0." >&2
    echo "This looks like a fresh or uninitialized database. Aborting start to avoid data loss." >&2
    echo "If you really intend to skip migrations, set RUN_MIGRATIONS=1 or initialize the DB first." >&2
    exit 1
  fi
fi

# Start the application
exec gunicorn --bind 0.0.0.0:${PORT} sist_project.wsgi:application
