#!/bin/sh
set -eu
echo '[lab3] Checking project migrations...'
# У учебного исходного проекта отсутствовал файл начальной миграции.
# Автоматическая генерация здесь сохраняет возможность запуска без ручных шагов.
python manage.py makemigrations library --noinput
python manage.py migrate --noinput
if [ "${SEED_DEMO:-0}" = "1" ]; then
  echo '[lab3] Loading demo data (requested by SEED_DEMO=1)...'
  python manage.py seed_demo
fi
echo '[lab3] Starting Django at 0.0.0.0:8000...'
exec python manage.py runserver 0.0.0.0:8000
