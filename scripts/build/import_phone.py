"""Build data/phone_prefixes.csv from the NCC Mobile Number Allocation Table.

Source page: https://ncc.gov.ng/operators/mobile-number-allocation-table ("as at December, 2023").
Each prefix card lists one or more number blocks with the operator (or status) for each.
A Nigerian mobile number is 0 + prefix digits + 7 subscriber digits, e.g. 0803 123 4567.

Number portability (since 2013) means the prefix shows which network a number was first
allocated to, not necessarily the network it is on today.

Run:  python scripts/build/import_phone.py
"""

from __future__ import annotations

import csv
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / ".cache" / "raw" / "ncc" / "mobile-number-allocation-table.html"
OUT = ROOT / "data" / "phone_prefixes.csv"

OPERATORS = {"MTN": "MTN", "Airtel": "Airtel", "Glo": "Glo", "EMTS (9Mobile)": "9mobile", "MAFAB": "MAFAB",
             "M-Tel": "M-Tel", "Smile": "Smile", "Visafone": "Visafone", "ICN, Openskys": "ICN/Openskys"}
STATUSES = {"Withdrawn": "withdrawn", "Returned": "returned", "Available": "available"}
FIELDS = ["prefix", "range_start", "range_end", "operator", "status", "ncc_label", "sources"]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    page = SRC.read_text(encoding="utf-8", errors="replace")
    rows, seen = [], set()
    for card in re.split(r'<div class="number-title">', page)[1:]:
        prefix = card.split("</div>")[0].strip()
        body = card.split("</div></span></div></div>")[0]
        for raw_label, raw_range in re.findall(r'<div class="company[^"]*">(.*?)</div>\s*<div class="label">(.*?)</div>', body, re.S):
            label = re.sub(r"\s+", " ", html.unescape(raw_label)).replace("�", "-").strip()
            start, end = (re.sub(r"\s", "", x) for x in raw_range.split(" to "))
            if (prefix, start) in seen:  # the NCC page lists 0702 twice
                continue
            seen.add((prefix, start))
            if label in OPERATORS:
                operator, status = OPERATORS[label], "allocated"
            elif label in STATUSES:
                operator, status = "", STATUSES[label]
            elif label.startswith("Shared by Value Added Service"):
                operator, status = "", "shared_vas"
            elif label.startswith("Reserved for Vanity"):
                operator, status = "", "reserved_vanity"
            else:
                raise SystemExit(f"Unknown NCC label for {prefix}: {label!r}")
            rows.append({"prefix": prefix, "range_start": start, "range_end": end, "operator": operator,
                         "status": status, "ncc_label": label, "sources": "ncc-mobile-allocation"})
    if not re.fullmatch(r"\d{7}", rows[0]["range_start"]):
        raise SystemExit("Unexpected range format")
    rows.sort(key=lambda r: (r["prefix"], r["range_start"]))
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} number blocks across {len({r['prefix'] for r in rows})} prefixes")
    for op in sorted({r["operator"] for r in rows if r["operator"]}):
        print(f"  {op}: {sorted({r['prefix'] for r in rows if r['operator'] == op})}")


if __name__ == "__main__":
    main()
