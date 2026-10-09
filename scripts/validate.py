"""Validate everything in data/ against schemas/ plus the rules a schema can't express.

Run:  python scripts/validate.py
Exit code is 0 when the data is valid and 1 otherwise, so CI can block bad changes.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCHEMAS = ROOT / "schemas"


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def check_schema(name: str, instance, schema_file: str) -> list[str]:
    schema = load_json(SCHEMAS / schema_file)
    validator = Draft202012Validator(schema)
    return [
        f"{name}: {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
        for e in sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    ]


def check_sources(sources: list[dict]) -> list[str]:
    errors = []
    seen = set()
    for s in sources:
        sid = s.get("id")
        if sid in seen:
            errors.append(f"sources.json: duplicate id {sid!r}")
        seen.add(sid)
        for key, value in s.items():
            if isinstance(value, str) and value != value.strip():
                errors.append(f"sources.json: {sid}: {key} has leading/trailing whitespace")
        retrieved = s.get("retrieved")
        if retrieved:
            try:
                if date.fromisoformat(retrieved) > date.today():
                    errors.append(f"sources.json: {sid}: retrieved date is in the future")
            except ValueError:
                errors.append(f"sources.json: {sid}: retrieved is not a real date")
    return errors


def validate() -> list[str]:
    sources = load_json(DATA / "sources.json")
    errors = check_schema("sources.json", sources, "sources.schema.json")
    errors += check_sources(sources)
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print(f"Data validation FAILED ({len(errors)} problem(s)):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("Data validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
