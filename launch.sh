#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py makemigrations library --noinput
python manage.py migrate --noinput
python manage.py seed_demo
python manage.py runserver 0.0.0.0:8000
