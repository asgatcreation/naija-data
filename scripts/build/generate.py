"""Generate the packaged data files from data/*.csv.

The same JSON files are written into every package, so all languages ship identical data:
  packages/python/src/naija_data/_data/
  packages/js/src/data/
  go/data/

Run:  python scripts/build/generate.py          (write files)
      python scripts/build/generate.py --check  (fail if the packaged files are out of date; used in CI)
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
TARGETS = [
    ROOT / "packages" / "python" / "src" / "naija_data" / "_data",
    ROOT / "packages" / "js" / "src" / "data",
    ROOT / "go" / "data",
]


def rows(name: str) -> list[dict]:
    with (DATA / f"{name}.csv").open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def lst(value: str) -> list[str]:
    return [v for v in value.split("|") if v] if value else []


def num(value: str) -> float | None:
    return float(value) if value else None


def build() -> dict[str, object]:
    sources = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
    states = [{
        "code": r["code"], "iso_code": r["iso_code"], "name": r["name"], "slug": r["slug"],
        "inec_code": r["inec_code"], "pcode": r["pcode"], "capital": r["capital"], "zone": r["zone"],
        "created": r["created"] or None, "lat": num(r["lat"]), "lon": num(r["lon"]),
        "aliases": lst(r["aliases"]), "unverified_fields": lst(r["unverified_fields"]), "sources": lst(r["sources"]),
    } for r in rows("states")]
    lgas = [{
        "code": r["code"], "state_code": r["state_code"], "inec_code": r["inec_code"], "name": r["name"],
        "slug": r["slug"], "headquarters": r["headquarters"] or None,
        "senatorial_district": r["senatorial_district"] or None, "lat": num(r["lat"]), "lon": num(r["lon"]),
        "aliases": lst(r["aliases"]), "unverified_fields": lst(r["unverified_fields"]), "sources": lst(r["sources"]),
    } for r in rows("lgas")]
    # Wards are the largest table: stored as columns + rows to keep the files small.
    ward_fields = ["code", "lga_code", "state_code", "name", "slug", "aliases"]
    wards = {"fields": ward_fields,
             "rows": [[r["code"], r["lga_code"], r["state_code"], r["name"], r["slug"], lst(r["aliases"])] for r in rows("wards")]}
    banks = [{
        "id": r["id"], "name": r["name"], "short_name": r["short_name"] or None, "type": r["type"],
        "cbn_code": r["cbn_code"] or None, "nip_code": r["nip_code"] or None, "ussd": r["ussd"] or None,
        "status": r["status"], "status_date": r["status_date"] or None, "merged_into": r["merged_into"] or None,
        "aliases": lst(r["aliases"]), "unverified_fields": lst(r["unverified_fields"]), "sources": lst(r["sources"]),
    } for r in rows("banks")]
    phone = [{
        "prefix": r["prefix"], "range_start": r["range_start"], "range_end": r["range_end"],
        "operator": r["operator"] or None, "status": r["status"],
    } for r in rows("phone_prefixes")]
    meta = {
        "data_version": max(s["retrieved"] for s in sources),
        "counts": {"states": len(states), "lgas": len(lgas), "wards": len(wards["rows"]), "banks": len(banks),
                   "phone_blocks": len(phone)},
        "licence": "CC-BY-4.0",
        "attribution": "naija-data by Akanji Oluwaseun Gabriel (https://github.com/asgatcreation/naija-data), CC BY 4.0",
        "sources": [{"id": s["id"], "name": s["name"], "url": s["url"], "retrieved": s["retrieved"], "licence": s["licence"]}
                    for s in sources],
    }
    return {"meta": meta, "states": states, "lgas": lgas, "wards": wards, "banks": banks, "phone": phone}


# Licence files every published package must carry.
LICENCE_TARGETS = [ROOT / "packages" / "python", ROOT / "packages" / "js"]
LICENCE_FILES = ["LICENSE", "LICENSE-DATA"]


def encode(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def main() -> int:
    check = "--check" in sys.argv
    files = {f"{name}.json": encode(obj) for name, obj in build().items()}
    stale = []
    planned = [(t / f, c) for t in TARGETS for f, c in files.items()]
    planned += [(t / f, (ROOT / f).read_bytes()) for t in LICENCE_TARGETS for f in LICENCE_FILES]
    for path, content in planned:
        if check:
            if not path.exists() or path.read_bytes() != content:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    if check:
        if stale:
            print("Packaged data is out of date. Run: python scripts/build/generate.py")
            for s in stale:
                print(f"  - {s}")
            return 1
        print("Packaged data is up to date.")
        return 0
    sizes = ", ".join(f"{k} {len(v) / 1024:.0f} KB" for k, v in files.items())
    print(f"Wrote {len(files)} files to {len(TARGETS)} packages ({sizes})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
