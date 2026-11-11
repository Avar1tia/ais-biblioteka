"""Run all static checks and fail if any scanner returns a nonzero status."""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    args = parser.parse_args()
    reports = args.reports.resolve()
    reports.mkdir(parents=True, exist_ok=True)

    checks = [
        ("Ruff", [sys.executable, "-m", "ruff", "check", "--select", "E9,F63,F7,F82",
                  "--output-format", "json", "--output-file", str(reports / "ruff.json"),
                  "library", "library_system", "ci", "manage.py"]),
        ("Bandit", [sys.executable, "-m", "bandit", "-r", "library", "library_system", "ci",
                    "manage.py", "-lll", "-f", "json", "-o", str(reports / "bandit.json")]),
        ("Gitleaks", [shutil.which("gitleaks") or "gitleaks", "git", "--log-opts=HEAD",
                      "--redact=100", "--no-banner", "--report-format=json",
                      f"--report-path={reports / 'gitleaks.json'}", "."]),
    ]
    failed = []
    for name, command in checks:
        output = reports / f"{name.lower()}.log"
        with output.open("w", encoding="utf-8") as log:
            try:
                status = subprocess.run(
                    command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=False
                ).returncode
            except OSError as exc:
                print(exc, file=log)
                status = 1
        print(f"{name}: exit={status}", flush=True)
        if status != 0:
            failed.append(name)
    if failed:
        print(f"Checks failed: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
