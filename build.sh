#!/usr/bin/env bash
set -e
mkdir -p /var/data || true
export PYTHONUNBUFFERED=1
export USE_SQLITE=true
export SQLITE_DB_PATH=/var/data/db.sqlite3
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
