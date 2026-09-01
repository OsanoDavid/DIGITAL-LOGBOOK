#!/usr/bin/env bash
set -euo pipefail
mkdir -p /var/data || true
export PYTHONUNBUFFERED=1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
