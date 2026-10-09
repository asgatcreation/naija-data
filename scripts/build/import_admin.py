"""Build data/states.csv, data/lgas.csv and data/wards.csv from the raw sources.

This is the *import* step. It is run to create the dataset and to audit it against
fresh downloads. After import, data/*.csv is the source of truth that contributors edit.

Inputs (see scripts/fetch/*):
  INEC CVR live lists         .cache/raw/inec-cvr/*.json        -> codes, ward lists, names
  INEC 2015 PU directories    .cache/extract/inec2015.json      -> cross-check, aliases
  OCHA COD-AB                 .cache/raw/codab/*.xlsx           -> P-codes, coordinates,
                                                                   senatorial districts, LGA HQs
  1999 Constitution           .cache/extract/constitution.json  -> capitals, FCT council HQs, aliases
  Unicode CLDR                .cache/raw/cldr/subdivisions-en.xml -> ISO 3166-2 codes
  EUAA Nigeria guidance       (zones, below)                    -> geopolitical zones
  BusinessDay (2025)          (dates, below)                    -> creation dates (unverified)

Name rule: an LGA's display name is INEC's current name, title-cased. The only exceptions
are the reviewed fixes in LGA_NAME_FIXES, where INEC's live entry is abbreviated, truncated
or misspelled compared with the legal name in the Constitution. Older spellings (INEC 2015,
COD-AB, Constitution) are not used to overrule INEC: they mostly copy the same 1990s lists.
Every variant seen in any source is kept as an alias, so searches still find them.

Run:  python scripts/build/import_admin.py
"""

from __future__ import annotations

import csv
import difflib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent))
from names import key, repair_roman, slugify, tidy, title  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / ".cache" / "raw"
EXTRACT = ROOT / ".cache" / "extract"
DATA = ROOT / "data"

# INEC's live list repeats one ward with a new internal id (8810): "09 - MBAIKYAAN" in
# Gwer East, Benue. INEC publishes 8,809 registration areas; this duplicate makes 8,810.
INEC_DUPLICATE_WARD_IDS = {"8810"}

# Geopolitical zones as listed by the EU Agency for Asylum, Country Guidance: Nigeria (2021).
ZONES = {
    "North-Central": ["Niger", "Kogi", "Benue", "Plateau", "Nasarawa", "Kwara", "Federal Capital Territory"],
    "North-East": ["Bauchi", "Borno", "Taraba", "Adamawa", "Gombe", "Yobe"],
    "North-West": ["Zamfara", "Sokoto", "Kaduna", "Kebbi", "Katsina", "Kano", "Jigawa"],
    "South-East": ["Enugu", "Imo", "Ebonyi", "Abia", "Anambra"],
    "South-South": ["Bayelsa", "Akwa Ibom", "Edo", "Rivers", "Cross River", "Delta"],
    "South-West": ["Oyo", "Ekiti", "Osun", "Ondo", "Lagos", "Ogun"],
}

# Creation dates as listed by BusinessDay (2025). Single secondary source, so the field is
# marked unverified. FCT: Federal Capital Territory Act 1976 (Decree No. 6 of 4 February 1976).
CREATED = {
    "Abia": "1991-08-27", "Adamawa": "1991-08-27", "Akwa Ibom": "1987-09-23", "Anambra": "1991-08-27",
    "Bauchi": "1976-02-03", "Bayelsa": "1996-10-01", "Benue": "1976-02-03", "Borno": "1976-02-03",
    "Cross River": "1967-05-27", "Delta": "1991-08-27", "Ebonyi": "1996-10-01", "Edo": "1991-08-27",
    "Ekiti": "1996-10-01", "Enugu": "1991-08-27", "Gombe": "1996-10-01", "Imo": "1976-02-03",
    "Jigawa": "1991-08-27", "Kaduna": "1967-05-27", "Kano": "1967-05-27", "Katsina": "1987-09-23",
    "Kebbi": "1991-08-27", "Kogi": "1991-08-27", "Kwara": "1967-05-27", "Lagos": "1967-05-27",
    "Nasarawa": "1996-10-01", "Niger": "1976-02-03", "Ogun": "1976-02-03", "Ondo": "1976-02-03",
    "Osun": "1991-08-27", "Oyo": "1976-02-03", "Plateau": "1976-02-03", "Rivers": "1967-05-27",
    "Sokoto": "1976-02-03", "Taraba": "1991-08-27", "Yobe": "1991-08-27", "Zamfara": "1996-10-01",
}

# Capital spellings: the Constitution's spelling is kept as an alias where the modern
# official spelling differs.
CAPITAL_MODERN = {"Oshogbo": "Osogbo", "Port-Harcourt": "Port Harcourt"}

# Reviewed corrections to INEC's live LGA labels: (state, INEC label) -> (name, reason).
LGA_NAME_FIXES = {
    ("Borno", "MAIDUGURI M. C."): ("Maiduguri", "abbreviation; Constitution: Maiduguri"),
    ("Cross River", "CALABAR MUNICIPALITY"): ("Calabar Municipal", "Constitution: Calabar-Municipal"),
    ("Federal Capital Territory", "MUNICIPAL"): ("Abuja Municipal", "truncated; Constitution Part II: Abuja Municipal"),
    ("Kogi", "KOGI . K. K."): ("Kogi", "abbreviation of Kogi (Koton-Karfe); Constitution: Kogi"),
    ("Sokoto", "S/BIRNI"): ("Sabon Birni", "abbreviation; Constitution: Sabon birni"),
    ("Gombe", "YALMALTU/ DEBA"): ("Yamaltu/Deba", "typo; Constitution and INEC 2015: Yamaltu/Deba"),
    ("Katsina", "MALUFASHI"): ("Malumfashi", "typo; Constitution and INEC 2015: Malumfashi"),
    ("Yobe", "KARASAWA"): ("Karasuwa", "typo; Constitution and INEC 2015: Karasuwa"),
    ("Edo", "UHUNMWODE"): ("Uhunmwonde", "typo; Constitution and INEC 2015: Uhunmwonde"),
    ("Akwa Ibom", "ESIT EKET (UQUO)"): ("Esit Eket", "headquarters in brackets; Constitution: Esit Eket"),
    ("Abia", "OSISIOMA"): ("Osisioma Ngwa", "truncated; Constitution: Osisioma Ngwa"),
    ("Kogi", "MOPA MORO"): ("Mopa-Muro", "typo; Constitution and INEC 2015: Mopa-Muro"),
    ("Kogi", "OGORI MANGOGO"): ("Ogori/Magongo", "typo; INEC 2015 and COD-AB: Ogori/Magongo"),
    ("Kebbi", "AREWA"): ("Arewa Dandi", "truncated; Constitution: Arewa-Dandi"),
}

# Common names people search for that no source lists as a spelling of the LGA.
LGA_EXTRA_ALIASES = {
    ("Federal Capital Territory", "Abuja Municipal"): ["AMAC", "Abuja Municipal Area Council"],
    ("Borno", "Maiduguri"): ["Maiduguri Metropolitan Council", "MMC"],
    ("Kogi", "Kogi"): ["Koton Karfe", "Kogi/Koton-Karfe"],
    ("Ekiti", "Aiyekire"): ["Gbonyin"],
}

STATE_ALIASES = {
    "Federal Capital Territory": ["FCT", "Abuja", "FCT Abuja", "Abuja FCT"],
    "Nasarawa": ["Nassarawa"],
}

STATE_FIELDS = ["code", "iso_code", "name", "slug", "inec_code", "pcode", "capital", "zone", "created",
                "lat", "lon", "aliases", "unverified_fields", "sources"]
LGA_FIELDS = ["code", "state_code", "inec_code", "name", "slug", "headquarters", "senatorial_district",
              "lat", "lon", "aliases", "unverified_fields", "sources"]
WARD_FIELDS = ["code", "lga_code", "state_code", "name", "slug", "aliases", "sources"]


def split_label(label: str) -> tuple[str, str]:
    code, name = label.split(" - ", 1)
    return code.strip(), name.strip()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sheet(wb, name):
    rows = list(wb[name].iter_rows(values_only=True))
    head = rows[0]
    return [dict(zip(head, r)) for r in rows[1:]]


def join(values) -> str:
    seen, out = set(), []
    for v in values:
        if v and key(v) not in seen:
            seen.add(key(v))
            out.append(v)
    return "|".join(out)


def aliases_for(name: str, variants) -> str:
    """Variants that differ from the display name (ignoring case and spacing)."""
    return join(v for v in variants if v and key(v) != key(name))


def best_match(target: str, pool: dict[str, object], cutoff: float):
    if key(target) in pool:
        return pool[key(target)]
    scored = [(difflib.SequenceMatcher(None, key(target), k).ratio(), k) for k in pool]
    score, k = max(scored) if scored else (0, None)
    return pool[k] if score >= cutoff else None


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    report: list[str] = []

    inec_states = load_json(RAW / "inec-cvr" / "states.json")["data"]
    inec_lgas = load_json(RAW / "inec-cvr" / "lgas.json")["data"]
    inec_wards = load_json(RAW / "inec-cvr" / "wards.json")["data"]
    old = load_json(EXTRACT / "inec2015.json")
    const = load_json(EXTRACT / "constitution.json")
    wb = openpyxl.load_workbook(RAW / "codab" / "nga_admin_boundaries.xlsx", read_only=True)
    cod1, cod2, caps = sheet(wb, "nga_admin1"), sheet(wb, "nga_admin2"), sheet(wb, "nga_admincapitals")
    cldr = dict(re.findall(r'<subdivision type="ng([a-z]{2})">([^<]+)<', (RAW / "cldr" / "subdivisions-en.xml").read_text(encoding="utf-8")))

    cod1_by_name = {r["adm1_name"]: r for r in cod1}
    iso_by_name = {v: k.upper() for k, v in cldr.items()}
    zone_by_name = {s: z for z, states in ZONES.items() for s in states}

    states, lgas, wards = [], [], []
    for sid, slabel in inec_states.items():
        inec_scode, inec_sname = split_label(slabel)
        name = "Federal Capital Territory" if inec_sname == "FCT" else title(inec_sname)
        code = iso_by_name[name]
        c1 = cod1_by_name[name]
        old_state = old.get("FCT" if code == "FC" else name)

        if code == "FC":
            capital, cap_alias, cap_src = "Abuja", [], "constitution-1999"  # s.298
        else:
            raw_cap = const["states"][name]["capital"]
            capital = CAPITAL_MODERN.get(raw_cap, raw_cap)
            cap_alias = [raw_cap] if raw_cap != capital else []
            cap_src = "constitution-1999"

        unverified = ["created"] if code != "FC" else []
        states.append({
            "code": code, "iso_code": f"NG-{code}", "name": name, "slug": "fct" if code == "FC" else slugify(name),
            "inec_code": inec_scode, "pcode": c1["adm1_pcode"], "capital": capital,
            "zone": zone_by_name[name], "created": "1976-02-04" if code == "FC" else CREATED[name],
            "lat": round(c1["center_lat"], 5), "lon": round(c1["center_lon"], 5),
            "aliases": aliases_for(name, STATE_ALIASES.get(name, []) + [inec_sname.title(), cldr[code.lower()], c1["adm1_name"]]),
            "unverified_fields": "|".join(unverified),
            "sources": "|".join(["inec-cvr", "ocha-cod-ab-nga", "unicode-cldr", cap_src, "euaa-nigeria-2021"]
                                + ([] if code == "FC" else ["businessday-state-creation"])),
            "_capital_aliases": cap_alias,
        })

        # ---- LGAs of this state
        cod_pool = {key(r["adm2_name"]): r for r in cod2 if r["adm1_name"] == c1["adm1_name"]}
        const_lgas = const["states"].get(name, {}).get("lgas", []) if code != "FC" else [c["name"] for c in const["fct_area_councils"]]
        const_pool = {key(n): n for n in const_lgas}
        used_pcodes = set()
        for lid, llabel in inec_lgas[sid].items():
            lcode, live_raw = split_label(llabel)
            live = tidy(live_raw)
            o = (old_state or {}).get("lgas", {}).get(lcode)
            old_name = tidy(o["name"]) if o else None
            # Strip INEC 2015 parenthetical HQ hints, e.g. "ISU (UMUNDUGBA)" -> "ISU".
            old_core = re.sub(r"\s*\(.*\)$", "", old_name) if old_name else None

            cod = cod_pool.get(key(live)) or (cod_pool.get(key(old_core)) if old_core else None)
            if not cod:
                cod = best_match(live, cod_pool, 0.8) or (best_match(old_core, cod_pool, 0.8) if old_core else None)
            if not cod:  # last resort: highest similarity, reported for review
                cod = max(cod_pool.values(), key=lambda r: difflib.SequenceMatcher(None, key(live), key(r["adm2_name"])).ratio())
                report.append(f"LGA weak match: {name}/{live} -> {cod['adm2_name']} ({cod['adm2_pcode']})")
            if cod["adm2_pcode"] in used_pcodes:
                raise SystemExit(f"P-code used twice: {cod['adm2_pcode']} ({name}/{live})")
            used_pcodes.add(cod["adm2_pcode"])
            const_name = best_match(live, const_pool, 0.75) or (best_match(old_core, const_pool, 0.75) if old_core else None)

            display = title(live)
            fix = LGA_NAME_FIXES.get((name, live_raw))
            if fix:
                display = fix[0]
                report.append(f"LGA name fix: {name}/{live_raw} -> {display} ({fix[1]})")

            hq = None
            hq_src = None
            if code == "FC":
                hit = next((c for c in const["fct_area_councils"] if key(c["name"]) == key(const_name or "")), None)
                if hit:
                    hq, hq_src = hit["headquarters"], "constitution-1999"
            else:
                cands = [c for c in caps if c["adm_p_lvl"] == 2 and c["adm1_name"] == c1["adm1_name"] and c["adm2_name"] == cod["adm2_name"]]
                if len(cands) == 1:
                    hq, hq_src = cands[0]["name"], "ocha-cod-ab-nga"
                elif len(cands) > 1:
                    report.append(f"LGA HQ ambiguous in COD-AB: {name}/{display}: {[c['name'] for c in cands]}")

            lunverified = ["headquarters"] if hq_src == "ocha-cod-ab-nga" else []
            lgas.append({
                "code": cod["adm2_pcode"], "state_code": code, "inec_code": f"{inec_scode}-{lcode}",
                "name": display, "slug": slugify(display), "headquarters": hq or "",
                "senatorial_district": cod["sendist_en"] or "",
                "lat": round(cod["center_lat"], 5), "lon": round(cod["center_lon"], 5),
                # INEC's raw label is a useful alias for typos, not for abbreviations.
                "aliases": aliases_for(display, [None if fix and fix[1].startswith(("abbreviation", "headquarters")) else title(live),
                                                 title(old_core) if old_core else None, tidy(cod["adm2_name"]),
                                                 title(const_name) if const_name else None]
                                       + LGA_EXTRA_ALIASES.get((name, display), [])),
                "unverified_fields": "|".join(lunverified),
                "sources": join(["inec-cvr", "inec-pu-directory-2015" if o else None, "ocha-cod-ab-nga",
                                 "constitution-1999" if const_name else None]),
            })

            # ---- wards (registration areas) of this LGA
            old_ras = (old_state or {}).get("ras", {}).get(lcode, {})
            seen_codes = set()
            for wid, wlabel in inec_wards[lid].items():
                if wid in INEC_DUPLICATE_WARD_IDS:
                    continue
                wcode, wraw = split_label(wlabel)
                if wcode in seen_codes:
                    raise SystemExit(f"Duplicate ward code {name}/{display}/{wcode}")
                seen_codes.add(wcode)
                w2015 = old_ras.get(wcode, {}).get("name")
                live_w = tidy(wraw)
                repaired = repair_roman(live_w)
                if repaired != live_w and not (w2015 and key(repaired) == key(tidy(w2015))):
                    repaired = live_w  # only repair when the 2015 directory confirms the numeral
                wname = title(repaired)
                wards.append({
                    "code": f"{inec_scode}-{lcode}-{wcode}", "lga_code": cod["adm2_pcode"], "state_code": code,
                    "name": wname, "slug": slugify(wname),
                    "aliases": aliases_for(wname, [title(w2015) if w2015 else None]),
                    "sources": join(["inec-cvr", "inec-pu-directory-2015" if w2015 else None]),
                })

    # Capital aliases go into the state's aliases only if they are not state names themselves.
    for s in states:
        s.pop("_capital_aliases")

    states.sort(key=lambda r: r["name"])
    lgas.sort(key=lambda r: (r["state_code"], r["name"]))
    wards.sort(key=lambda r: r["code"])
    DATA.mkdir(exist_ok=True)
    write_csv(DATA / "states.csv", STATE_FIELDS, states)
    write_csv(DATA / "lgas.csv", LGA_FIELDS, lgas)
    write_csv(DATA / "wards.csv", WARD_FIELDS, wards)

    print(f"states {len(states)}  lgas {len(lgas)}  wards {len(wards)}")
    print(f"LGAs with headquarters: {sum(1 for l in lgas if l['headquarters'])}")
    for line in report:
        print("  " + line)


if __name__ == "__main__":
    main()
