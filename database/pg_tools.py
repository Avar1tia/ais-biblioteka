"""Compare schema dumps and create verified PostgreSQL backups without overwriting."""

import argparse
import difflib
import hashlib
import os
import re
import subprocess
import tempfile
from pathlib import Path

NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]*\Z")
DUMP_METADATA = re.compile(
    r"^(?:-- Dumped (?:from|by) database version .+|-- Dumped by pg_dump version .+"
    r"|\\(?:un)?restrict [A-Za-z0-9]+)$"
)


def run(*command, service=None, **kwargs):
    env = os.environ.copy()
    env["PGCLIENTENCODING"] = "UTF8"
    if service:
        if not NAME.fullmatch(service):
            raise ValueError("Invalid pg_service.conf name")
        for variable in (
            "PGDATABASE", "PGHOST", "PGHOSTADDR", "PGPORT", "PGUSER", "PGPASSWORD",
        ):
            env.pop(variable, None)
        env["PGSERVICE"] = service
    return subprocess.run(command, check=True, env=env, **kwargs)


def schema(service):
    result = run(
        "pg_dump", "--no-password", "--schema-only", "--schema=public",
        "--no-owner", "--no-privileges", service=service, capture_output=True,
    )
    lines = result.stdout.decode("utf-8").splitlines()
    return [line for line in lines if not DUMP_METADATA.fullmatch(line)]


def compare(left, right):
    diff = list(difflib.unified_diff(schema(left), schema(right), left, right, lineterm=""))
    if diff:
        print("\n".join(diff))
        return 1
    print(f"Schemas match: {left} and {right}")
    return 0


def backup(service, destination):
    with tempfile.NamedTemporaryFile(
        prefix=f".{destination.name}.", dir=destination.parent, delete=False
    ) as output:
        staged = Path(output.name)
        try:
            run(
                "pg_dump", "--no-password", "--format=custom",
                service=service, stdout=output,
            )
            output.flush()
            os.fsync(output.fileno())
            output.close()
            run("pg_restore", "--list", str(staged), stdout=subprocess.DEVNULL)
            with staged.open("rb") as archive:
                digest = hashlib.file_digest(archive, "sha256").hexdigest()
            os.link(staged, destination)
        finally:
            output.close()
            staged.unlink()
    print(f"Backup verified (archive index): {destination} ({destination.stat().st_size} bytes)")
    print(f"SHA256 {digest}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    diff = sub.add_parser("compare")
    diff.add_argument("left", help="pg_service.conf entry")
    diff.add_argument("right", help="pg_service.conf entry")
    dump = sub.add_parser("backup")
    dump.add_argument("service", help="pg_service.conf entry")
    dump.add_argument("destination", type=Path)
    args = parser.parse_args()
    if args.command == "compare":
        return compare(args.left, args.right)
    os.umask(0o077)
    backup(args.service, args.destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
