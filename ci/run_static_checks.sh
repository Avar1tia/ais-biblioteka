#!/usr/bin/env bash
set -euo pipefail
umask 077

tools=$(mktemp -d)
trap 'rm -rf -- "$tools"' EXIT
version=8.30.1
asset="gitleaks_${version}_linux_x64.tar.gz"
checksum=551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb
curl --fail --silent --show-error --location \
  "https://github.com/gitleaks/gitleaks/releases/download/v$version/$asset" -o "$tools/$asset"
(
  cd "$tools"
  printf '%s  %s\n' "$checksum" "$asset" | sha256sum --check --status
  tar -xzf "$asset" gitleaks
)
python3 -m venv "$tools/python"
"$tools/python/bin/python" -m pip install --disable-pip-version-check -r ci/requirements-static.txt
PATH="$tools:$PATH" "$tools/python/bin/python" ci/static_checks.py --reports static-reports
