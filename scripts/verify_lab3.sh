#!/bin/sh
# Запуск на library-test из корня проекта после docker compose up -d --build
set -eu
echo '--- Docker version ---'
sudo docker --version
sudo docker compose version
echo '--- Running services ---'
sudo docker compose ps
echo '--- HTTP response ---'
curl --fail --silent --show-error -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:8000/
echo '--- DB check ---'
sudo docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT COUNT(*) AS books FROM library_book;"'
echo '--- Django check ---'
sudo docker compose exec -T web python manage.py check
