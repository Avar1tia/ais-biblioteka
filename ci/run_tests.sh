#!/usr/bin/env bash
set -euo pipefail
umask 077

tools=$(mktemp -d)
trap 'rm -rf -- "$tools"' EXIT
python3 -m venv "$tools/python"
"$tools/python/bin/python" -m pip install --disable-pip-version-check -r requirements.txt
"$tools/python/bin/python" manage.py test library --settings=library_system.test_settings -v 2
