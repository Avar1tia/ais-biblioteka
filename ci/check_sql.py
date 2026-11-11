"""Allow reviewed, additive PostgreSQL schema changes in database/changes/."""

from pathlib import Path

from pglast import ast, enums, parse_sql
from pglast.parser import ParseError

CHANGES = Path(__file__).resolve().parents[1] / "database" / "changes"


def check(path):
    statements = parse_sql(path.read_text(encoding="utf-8"))
    if not statements:
        raise ValueError("empty change")
    for entry in statements:
        statement = entry.stmt
        if not isinstance(statement, ast.AlterTableStmt):
            raise ValueError("expected ALTER TABLE")
        if statement.relation.schemaname != "public":
            raise ValueError("expected an explicit public schema")
        if not statement.relation.relname.startswith("library_"):
            raise ValueError("expected an application table")
        for command in statement.cmds:
            if command.subtype != enums.AlterTableType.AT_AddColumn:
                raise ValueError("only ADD COLUMN is allowed")
            column = command.def_
            constraints = {constraint.contype for constraint in (column.constraints or ())}
            if (
                constraints - {enums.ConstrType.CONSTR_NULL}
                or column.is_not_null
                or column.raw_default is not None
                or column.typeName.arrayBounds
            ):
                raise ValueError("expected a nullable scalar column without a default")
            names = tuple(part.sval for part in column.typeName.names)
            if names != ("pg_catalog", "varchar"):
                raise ValueError("expected varchar")


def main():
    changes = sorted(CHANGES.glob("*.sql"))
    if not changes:
        print("No schema change files found")
        return 1
    failed = False
    for path in changes:
        try:
            check(path)
        except (ParseError, ValueError) as exc:
            print(f"{path.name}: {exc}")
            failed = True
        else:
            print(f"{path.name}: OK")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
