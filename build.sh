#!/usr/bin/env bash
set -e
mkdir -p /var/data || true
export PYTHONUNBUFFERED=1
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
