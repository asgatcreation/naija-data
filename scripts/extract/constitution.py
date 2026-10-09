"""Extract the First Schedule of the 1999 Constitution (states, LGAs, capitals, FCT area councils).

Source: https://nigeriarights.gov.ng/files/constitution.pdf (National Human Rights Commission).
That copy is a retyped transcription and contains typing errors (e.g. "Tqngaza") and
missing commas. We therefore use it for capitals, the legal LGA total, and historical
spellings (aliases), not as the master list of names. Lines are split on commas and on
the few places where a full stop was typed instead of a comma.

Output: .cache/extract/constitution.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / ".cache" / "raw" / "constitution" / "constitution.pdf"
OUT = ROOT / ".cache" / "extract" / "constitution.json"

STATES = [
    "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa", "Benue", "Borno", "Cross River",
    "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu", "Gombe", "Imo", "Jigawa", "Kaduna", "Kano", "Katsina",
    "Kebbi", "Kogi", "Kwara", "Lagos", "Nasarawa", "Niger", "Ogun", "Ondo", "Osun", "Oyo", "Plateau",
    "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara",
]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    pdf = pdfium.PdfDocument(SRC)
    pages = [pdf[i].get_textpage().get_text_range() for i in range(len(pdf))]
    start = next(i for i, t in enumerate(pages) if t.lstrip().startswith("State Local Government Areas Capital City"))
    text = "\n".join(pages[start:start + 4])
    text = text.replace("￾", "-").replace("’", "'")
    part1, part2 = text.split("Part II", 1)
    lines = [l.strip() for l in part1.splitlines()[1:] if l.strip() and l.strip() != "Back to Page One"]

    states: dict[str, dict] = {}
    idx = 0
    current = None
    buf: list[str] = []
    for line in lines:
        nxt = STATES[idx] if idx < len(STATES) else None
        if nxt and line.startswith(nxt + " ") and "," in line:
            if current:
                states[current] = {"lgas_raw": " ".join(buf[:-1]), "capital": buf[-1]}
            current, buf, idx = nxt, [line[len(nxt) + 1:]], idx + 1
        else:
            buf.append(line)
    states[current] = {"lgas_raw": " ".join(buf[:-1]), "capital": buf[-1]}

    for s in states.values():
        raw = re.sub(r"\.\s*,", ",", s.pop("lgas_raw"))
        raw = re.sub(r"\.\s+(?=[A-Z])", ", ", raw)  # "Takum. Ussa" -> "Takum, Ussa"
        s["lgas"] = [re.sub(r"\s+", " ", p).strip(" .") for p in raw.split(",") if p.strip(" .")]

    councils = re.findall(r"^(Abaji|Abuja Municipal|Bwari|Gwagwalada|Kuje|Kwali)\s+(\S+)\s*$", part2, re.M)
    out = {"states": states, "fct_area_councils": [{"name": n, "headquarters": h} for n, h in councils]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    total = sum(len(s["lgas"]) for s in states.values())
    for name, s in states.items():
        print(f"{name:12} {len(s['lgas']):3} LGAs  capital: {s['capital']}")
    print(f"States: {len(states)}  LGAs parsed: {total} (Constitution s.3(6) says 768)  FCT councils: {len(councils)}")


if __name__ == "__main__":
    main()
