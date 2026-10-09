"""Validate everything in data/ against schemas/ plus the rules a schema can't express.

Run:  python scripts/validate.py
Exit code is 0 when the data is valid and 1 otherwise, so CI can block bad changes.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCHEMAS = ROOT / "schemas"

# Official totals. Changing these needs a source (e.g. a new INEC delimitation).
EXPECTED = {
    "states": 37,  # 36 states + FCT (Constitution s.2(2) and s.3(1))
    "lgas": 774,  # 768 LGAs + 6 FCT area councils (Constitution s.3(6), First Schedule)
    "wards": 8809,  # INEC registration areas (inecnigeria.org/polling-units)
}
CSV_FILES = ["states", "lgas", "wards", "banks", "phone_prefixes"]


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_csv(name: str) -> list[dict]:
    path = DATA / f"{name}.csv"
    raw = path.read_bytes()
    if b"\r\n" in raw:
        raise ValueError(f"{name}.csv has Windows line endings (CRLF); use LF")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"{name}.csv starts with a byte-order mark; save as UTF-8 without BOM")
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def check_schema(name: str, instance, schema_file: str) -> list[str]:
    schema = load_json(SCHEMAS / schema_file)
    validator = Draft202012Validator(schema)
    return [
        f"{name}: {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
        for e in sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    ]


def check_rows(name: str, rows: list[dict]) -> list[str]:
    schema = load_json(SCHEMAS / f"{name}.schema.json")
    validator = Draft202012Validator(schema)
    errors = []
    for i, row in enumerate(rows, start=2):  # line 1 is the header
        for e in validator.iter_errors(row):
            field = "/".join(map(str, e.absolute_path)) or "<row>"
            errors.append(f"{name}.csv line {i}: {field}: {e.message}")
    return errors


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


def unique(name: str, rows: list[dict], *fields: str) -> list[str]:
    counts = Counter(tuple(r[f] for f in fields) for r in rows)
    return [f"{name}.csv: duplicate {'+'.join(fields)} {k}" for k, n in counts.items() if n > 1]


def split(value: str) -> list[str]:
    return [v for v in value.split("|") if v] if value else []


def name_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def check_common(name: str, rows: list[dict], source_ids: set[str], name_field: str | None = "name") -> list[str]:
    errors = []
    for i, r in enumerate(rows, start=2):
        for f, v in r.items():
            if v != v.strip() or "  " in v:
                errors.append(f"{name}.csv line {i}: {f} has stray whitespace: {v!r}")
        for sid in split(r.get("sources", "")):
            if sid not in source_ids:
                errors.append(f"{name}.csv line {i}: unknown source id {sid!r}")
        if "aliases" in r:
            aliases = split(r["aliases"])
            keys = [name_key(a) for a in aliases]
            if len(keys) != len(set(keys)):
                errors.append(f"{name}.csv line {i}: duplicate aliases {aliases}")
            if name_field and name_key(r[name_field]) in keys:
                errors.append(f"{name}.csv line {i}: alias repeats the name {r[name_field]!r}")
        for field in split(r.get("unverified_fields", "")):
            if not r.get(field):
                errors.append(f"{name}.csv line {i}: {field} is marked unverified but is empty")
    return errors


def check_dates(name: str, rows: list[dict], field: str) -> list[str]:
    errors = []
    for i, r in enumerate(rows, start=2):
        if r.get(field):
            try:
                if date.fromisoformat(r[field]) > date.today():
                    errors.append(f"{name}.csv line {i}: {field} is in the future")
            except ValueError:
                errors.append(f"{name}.csv line {i}: {field} is not a real date: {r[field]!r}")
    return errors


def check_admin(states, lgas, wards) -> list[str]:
    errors = []
    for name, rows in (("states", states), ("lgas", lgas), ("wards", wards)):
        if len(rows) != EXPECTED[name]:
            errors.append(f"{name}.csv: expected {EXPECTED[name]} rows, found {len(rows)}")
    errors += unique("states", states, "code") + unique("states", states, "slug") + unique("states", states, "inec_code")
    errors += unique("states", states, "pcode") + unique("states", states, "name")
    errors += unique("lgas", lgas, "code") + unique("lgas", lgas, "inec_code") + unique("lgas", lgas, "state_code", "slug")
    errors += unique("wards", wards, "code") + unique("wards", wards, "lga_code", "slug")

    state_by_code = {s["code"]: s for s in states}
    for s in states:
        if s["iso_code"] != f"NG-{s['code']}":
            errors.append(f"states.csv: {s['code']}: iso_code {s['iso_code']} does not match code")
    lga_by_code = {l["code"]: l for l in lgas}
    for l in lgas:
        st = state_by_code.get(l["state_code"])
        if not st:
            errors.append(f"lgas.csv: {l['code']} {l['name']}: unknown state {l['state_code']}")
            continue
        if not l["inec_code"].startswith(st["inec_code"] + "-"):
            errors.append(f"lgas.csv: {l['code']} {l['name']}: INEC code {l['inec_code']} not under state {st['inec_code']}")
        if not l["code"].startswith(st["pcode"]):
            errors.append(f"lgas.csv: {l['code']} {l['name']}: P-code not under state {st['pcode']}")
    per_state = Counter(l["state_code"] for l in lgas)
    for s in states:
        if per_state[s["code"]] == 0:
            errors.append(f"states.csv: {s['name']} has no LGAs")
    for w in wards:
        lga = lga_by_code.get(w["lga_code"])
        if not lga:
            errors.append(f"wards.csv: {w['code']} {w['name']}: unknown LGA {w['lga_code']}")
            continue
        if w["state_code"] != lga["state_code"]:
            errors.append(f"wards.csv: {w['code']}: state {w['state_code']} differs from its LGA's state {lga['state_code']}")
        if not w["code"].startswith(lga["inec_code"] + "-"):
            errors.append(f"wards.csv: {w['code']} {w['name']}: code not under LGA {lga['inec_code']}")
    per_lga = Counter(w["lga_code"] for w in wards)
    for l in lgas:
        if per_lga[l["code"]] == 0:
            errors.append(f"lgas.csv: {l['name']} ({l['code']}) has no wards")
    return errors


def check_banks(banks) -> list[str]:
    errors = unique("banks", banks, "id")
    ids = {b["id"] for b in banks}
    active_codes = defaultdict(list)
    for b in banks:
        if b["merged_into"] and b["merged_into"] not in ids:
            errors.append(f"banks.csv: {b['id']}: merged_into {b['merged_into']!r} does not exist")
        if b["status"] == "merged" and not b["merged_into"]:
            errors.append(f"banks.csv: {b['id']}: status merged needs merged_into")
        if b["status"] != "active" and not b["status_date"]:
            errors.append(f"banks.csv: {b['id']}: status {b['status']} needs status_date")
        if b["cbn_code"]:
            want = 3 if b["type"] in ("commercial", "merchant", "non_interest") else 5
            if len(b["cbn_code"]) != want:
                errors.append(f"banks.csv: {b['id']}: a {b['type']} cbn_code must have {want} digits")
            if b["status"] == "active":
                active_codes[("cbn", b["cbn_code"])].append(b["id"])
        if b["nip_code"] and b["status"] == "active":
            active_codes[("nip", b["nip_code"])].append(b["id"])
    for (kind, code), owners in active_codes.items():
        if len(owners) > 1:
            errors.append(f"banks.csv: {kind}_code {code} used by several active institutions: {owners}")
    return errors + check_dates("banks", banks, "status_date")


def check_phone(prefixes) -> list[str]:
    errors = []
    by_prefix = defaultdict(list)
    for p in prefixes:
        if p["range_start"] > p["range_end"]:
            errors.append(f"phone_prefixes.csv: {p['prefix']} {p['range_start']}: start is after end")
        if (p["status"] == "allocated") != bool(p["operator"]):
            errors.append(f"phone_prefixes.csv: {p['prefix']} {p['range_start']}: operator must be set exactly when allocated")
        by_prefix[p["prefix"]].append(p)
    for prefix, blocks in by_prefix.items():
        blocks.sort(key=lambda b: b["range_start"])
        for a, b in zip(blocks, blocks[1:]):
            if b["range_start"] <= a["range_end"]:
                errors.append(f"phone_prefixes.csv: {prefix}: blocks {a['range_start']} and {b['range_start']} overlap")
    return errors


def validate() -> list[str]:
    sources = load_json(DATA / "sources.json")
    errors = check_schema("sources.json", sources, "sources.schema.json")
    errors += check_sources(sources)
    source_ids = {s["id"] for s in sources}

    tables = {}
    for name in CSV_FILES:
        try:
            tables[name] = load_csv(name)
        except (OSError, ValueError) as e:
            errors.append(str(e))
            continue
        errors += check_rows(name, tables[name])
        errors += check_common(name, tables[name], source_ids, None if name == "phone_prefixes" else "name")
    if errors:  # structural problems make the cross-file checks noisy
        return errors

    errors += check_admin(tables["states"], tables["lgas"], tables["wards"])
    errors += check_dates("states", tables["states"], "created")
    errors += check_banks(tables["banks"])
    errors += check_phone(tables["phone_prefixes"])
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print(f"Data validation FAILED ({len(errors)} problem(s)):")
        for e in errors[:200]:
            print(f"  - {e}")
        if len(errors) > 200:
            print(f"  ... and {len(errors) - 200} more")
        return 1
    print("Data validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
