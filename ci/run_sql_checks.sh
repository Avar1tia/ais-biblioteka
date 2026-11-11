#!/usr/bin/env bash
set -euo pipefail
umask 077

tools=$(mktemp -d)
trap 'rm -rf -- "$tools"' EXIT
python3 -m venv "$tools/python"
"$tools/python/bin/python" -m pip install --disable-pip-version-check \
  -r requirements.txt -r ci/requirements-sql.txt
"$tools/python/bin/python" ci/check_sql.py
"$tools/python/bin/python" manage.py makemigrations --check --dry-run
