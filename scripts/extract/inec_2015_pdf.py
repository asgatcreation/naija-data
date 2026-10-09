"""Extract LGA and registration-area (ward) lists from INEC's 2015 Polling Unit Directories.

The PDFs were removed from inecnigeria.org; we use the Internet Archive copies of the
official files (see .cache/raw/wayback-inec/index.json for the snapshot of each one).
These serve as an independent cross-check for the live INEC CVR data.

Output: .cache/extract/inec2015.json
  {state: {"lgas": {lga_code: {"name", "ra_count", "pu_count"}},
           "ras":  {lga_code: {ra_code: {"name", "pu_count"}}}}}
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / ".cache" / "raw" / "wayback-inec"
OUT = ROOT / ".cache" / "extract" / "inec2015.json"

DASHES = dict.fromkeys(map(ord, "‐‑‒–—−"), "-")
ROW = re.compile(r"^(?P<name>.+?)\s+(?P<code>\d{2,3})\s+(?P<count>[\d,]+)(?:\s+(?P<count2>[\d,]+))?$")


def clean(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text.translate(DASHES)).strip()


def parse_pdf(path: Path) -> dict:
    pdf = pdfium.PdfDocument(path)
    lgas: dict[str, dict] = {}
    ras: dict[str, dict] = {}
    current_lga = None
    mode = None
    pending = False  # a list started on an earlier page and its TOTAL line hasn't appeared yet
    for page in pdf:
        lines = [clean(l) for l in page.get_textpage().get_text_range().splitlines() if l.strip()]
        joined = " ".join(lines[:8]).upper()
        if pending:
            pass  # continuation page of the current list: keep the same mode
        elif "THE LIST OF LOCAL GOVERNMENT AREAS" in joined or "LIST OF AREA COUNCILS" in joined:
            mode = "lgas"
        elif "THE LIST OF REGISTRATION AREAS" in joined or "LIST OF WARDS" in joined:
            mode = "ras"
            for l in lines[:6]:
                m = re.match(r"^Code:\s*(\d+)", l, re.I)
                if m:
                    current_lga = m.group(1).zfill(2)
                    ras.setdefault(current_lga, {})
        elif mode is not None and not any(k in joined for k in ("CONTINUED", "CONT'D", "CONT.")):
            # PU detail pages: stop collecting until the next list page.
            mode = None
            continue
        if mode is None:
            continue
        pending = not any(l.upper().startswith("TOTAL") for l in lines)
        for l in lines:
            if l.upper().startswith(("TOTAL", "NAME", "INEC NIGERIA", "LGA:", "AC:", "CODE:")):
                continue
            m = ROW.match(l)
            if not m:
                continue
            name, code = m.group("name").strip(), m.group("code").zfill(2)
            if mode == "lgas" and m.group("count2"):
                lgas[code] = {"name": name, "ra_count": int(m.group("count").replace(",", "")),
                              "pu_count": int(m.group("count2").replace(",", ""))}
            elif mode == "ras" and current_lga and not m.group("count2"):
                ras[current_lga][code] = {"name": name, "pu_count": int(m.group("count").replace(",", ""))}
    return {"lgas": lgas, "ras": ras}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    result = {}
    for pdf in sorted(SRC.glob("*.pdf")):
        state = pdf.stem.replace("PU_Directory_Revised_January_2015_", "").rstrip("0123456789").replace("_", " ")
        data = parse_pdf(pdf)
        result[state] = data
        n_ra = sum(len(v) for v in data["ras"].values())
        expected = sum(v["ra_count"] for v in data["lgas"].values())
        flag = "" if n_ra == expected else f"  <-- parsed {n_ra} RA rows, summary says {expected}"
        print(f"{state:12} LGAs {len(data['lgas']):3}  RAs {n_ra:4}{flag}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
