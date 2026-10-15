"""Build data/phone_area_codes.csv and data/phone_number_blocks.csv from official NCC documents.

Sources
- NCC "Area Codes by Zone & Primary Centre" page: the 56 geographic area codes.
- NCC National Numbering Plan (October 2022): every block of numbers allocated to each operator
  (fixed lines by area, mobile prefixes, and the 0700/0800 special number ranges).
- Numbering Regulations 2008 (Official Gazette No. 68): the trunk prefix 0 is not part of the
  number; the example Lagos number 12691531 shows that a fixed national number has 8 digits.

Ranges are stored as full national significant numbers (without the trunk 0), so a block can be
checked with a string comparison of equal-length numbers.

Run:  python scripts/build/import_numbering.py
"""

from __future__ import annotations

import csv
import html
import re
import sys
from pathlib import Path

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / ".cache" / "raw" / "ncc"
DATA = ROOT / "data"

ZONES = {"Lagos Zone": "Lagos", "North West Zone": "North West", "Central Zone": "Central",
         "North-East Zone": "North East", "South-West Zone": "South West", "South-East": "South East"}

# The two NCC documents disagree on these: the area code page has Benin 053 and Warri 052, the
# numbering plan has Benin 052 and Warri 053. Both codes are valid; the centre name is unverified.
CONFLICTING_CENTRES = {"052", "053"}


def area_codes() -> list[dict]:
    page = (RAW / "area-codes.html").read_text(encoding="utf-8", errors="replace")
    table = re.search(r"<table.*?</table>", page, re.S).group(0)
    text = lambda c: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", c))).strip()
    rows, zone = [], None
    for tr in re.findall(r"<tr.*?</tr>", table, re.S):
        heading = re.search(r"<th[^>]*>(.*?)</th>", tr, re.S)  # zone names are row headings
        if heading and text(heading.group(1)):
            zone = text(heading.group(1))
        cells = [text(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(cells) != 2 or cells[1] == "Area Code":
            continue
        centre, code = cells
        if not re.fullmatch(r"0\d{1,2}", code):
            raise SystemExit(f"Unexpected area code {code!r}")
        rows.append({"area_code": code, "primary_centre": centre, "ncc_zone": ZONES[zone],
                     "unverified_fields": "primary_centre" if code in CONFLICTING_CENTRES else "",
                     "sources": "ncc-area-codes|ncc-numbering-plan-2022"})
    return rows


def blocks(codes: list[dict], report: list[str]) -> list[dict]:
    known = {c["area_code"] for c in codes}
    pdf = pdfium.PdfDocument(RAW / "numbering-plan-2022.pdf")
    lines = [l.strip() for i in range(len(pdf)) for l in pdf[i].get_textpage().get_text_range().splitlines()]
    # A row is: number, allottee, area ("National" or a place), code, ["shared"], access code,
    # range start, range end, total. Anchor on the code: the first token shaped like 0X, 0XX or 0XXX
    # that follows a place name or "National".
    row_re = re.compile(r"^(?P<n>\d+) (?P<rest>.+) (?P<total>[\d,]+)$")
    out = []
    for line in lines:
        m = row_re.match(line)
        if not m or not re.search(r" 0\d{1,3} ", line):
            continue
        tokens = m["rest"].split(" ")
        idx = next((i for i, t in enumerate(tokens) if re.fullmatch(r"0\d{1,3}", t) and i >= 2), None)
        if idx is None:
            report.append(f"unparsed row: {line}")
            continue
        code = tokens[idx]
        after = [t for t in tokens[idx + 1:] if t.lower() != "shared"]
        before = tokens[:idx]
        national = before[-1] == "National"
        if national:
            allottee, area = " ".join(before[:-1]), "National"
        else:
            # The place name is one or two words (e.g. "Port Harcourt", "Ijebu-Ode").
            two = " ".join(before[-2:])
            area_words = 2 if two in ("Port Harcourt", "New Bussa", "Birnin Kebbi") else 1
            allottee, area = " ".join(before[:-area_words]), " ".join(before[-area_words:])
        access, numbers = after[0], after[1:]
        if len(numbers) == 2:
            start, end = numbers
        elif len(numbers) == 4:  # written with a space inside each number: "227 0000 227 9999"
            start, end = numbers[0] + numbers[1], numbers[2] + numbers[3]
        else:
            report.append(f"row {m['n']}: cannot read the range: {line}")
            continue
        lead = code[1:]  # without the trunk 0: "1", "64", "803"
        if national:
            if len(start) != 10 or len(end) != 10 or not start.startswith(lead):
                report.append(f"row {m['n']}: unexpected national range: {line}")
                continue
            kind = {"700": "non_toll_free", "800": "toll_free"}.get(lead, "mobile")
            nsn_start, nsn_end, area_code = start, end, ""
        else:
            if code not in known:
                report.append(f"row {m['n']}: area code {code} is not in the NCC area code list; excluded: {line}")
                continue
            want = 8 - len(lead)
            if len(start) == 8 and start.startswith(lead):  # range written with the area code included
                start, end = start[len(lead):], end[len(lead):]
            if len(start) != want or len(end) != want:
                report.append(f"row {m['n']}: range length does not fit area code {code}; excluded: {line}")
                continue
            if not (start.startswith(access) and end.startswith(access)):
                report.append(f"row {m['n']}: range {start}-{end} does not start with access code {access}; excluded: {line}")
                continue
            kind, nsn_start, nsn_end, area_code = "fixed", lead + start, lead + end, code
        total = int(m["total"].replace(",", ""))
        if int(nsn_end) - int(nsn_start) + 1 != total:
            report.append(f"row {m['n']}: range holds {int(nsn_end) - int(nsn_start) + 1:,} numbers but 'Total Lines' says {total:,} (range kept): {line}")
        out.append({"number_type": kind, "area_code": area_code, "range_start": nsn_start, "range_end": nsn_end,
                    "allottee": allottee, "area": area, "sources": "ncc-numbering-plan-2022"})
    out.sort(key=lambda r: (len(r["range_start"]), r["range_start"], r["range_end"]))
    # The plan lists some blocks twice with differently spelled allottees (e.g. "Nationwave Telecom
    # Nig. Limited" / "Nationwaves Telcom Nigeria Limited"); keep one row per identical range.
    merged: list[dict] = []
    for r in out:
        prev = merged[-1] if merged else None
        if prev and (prev["range_start"], prev["range_end"]) == (r["range_start"], r["range_end"]):
            report.append(f"duplicate block {r['range_start']}-{r['range_end']}: '{prev['allottee']}' and '{r['allottee']}' (kept the first)")
            continue
        merged.append(r)
    return merged


def write(name: str, fields: list[str], rows: list[dict]) -> None:
    with (DATA / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    report: list[str] = []
    codes = area_codes()
    rows = blocks(codes, report)
    write("phone_area_codes.csv", ["area_code", "primary_centre", "ncc_zone", "unverified_fields", "sources"], codes)
    write("phone_number_blocks.csv", ["number_type", "area_code", "range_start", "range_end", "allottee", "area", "sources"], rows)
    by_type: dict[str, int] = {}
    for r in rows:
        by_type[r["number_type"]] = by_type.get(r["number_type"], 0) + 1
    print(f"{len(codes)} area codes; {len(rows)} number blocks {by_type}")
    for line in report:
        print("  " + line)


if __name__ == "__main__":
    main()
