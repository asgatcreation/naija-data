"""Build the electoral units from INEC's Result Viewing portal (IReV).

Writes:
  data/senatorial_districts.csv     109 senatorial districts (Senate)
  data/federal_constituencies.csv   360 federal constituencies (House of Representatives)
  data/state_constituencies.csv     990 state constituencies (State Houses of Assembly)
and fills, in data/wards.csv, each ward's senatorial district, federal constituency and state
constituency, and in data/lgas.csv each LGA's senatorial district (name).

Input: .cache/raw/inec-irev/*.json (python scripts/fetch/inec_irev.py)

Rules:
- Units, names and links are INEC's. Names come from the 2023 general elections (Senate and House
  of Representatives on 25 February 2023, Houses of Assembly on 18 March 2023), title-cased.
  Names used by INEC for other elections of the same unit (re-runs, by-elections) become aliases.
- Reviewed fixes: NAME_FIXES (misspelled state names inside unit names) and SC_CODE_FIXES
  (three state constituency codes INEC typed twice; the right number follows from the sequence).
- IReV gives the FCT one placeholder state constituency: the FCT has no House of Assembly, so FCT
  wards have no state constituency.
- A ward whose state constituency lies, for every other ward of that constituency, in a different
  federal constituency is very likely mislinked in IReV (a same-named ward of a neighbouring LGA).
  INEC's value is kept, but the field is listed in the ward's `unverified_fields`.

Run after import_admin.py:  python scripts/build/import_electoral.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from names import key, slugify, tidy, title  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / ".cache" / "raw" / "inec-irev"
DATA = ROOT / "data"
SOURCE = "inec-irev"

KINDS = {  # IReV election code -> (our code prefix, file, 2023 general election date)
    "SEN": ("SD", "senatorial_districts", "2023-02-25"),
    "REPS": ("FC", "federal_constituencies", "2023-02-25"),
    "ASSEMBLY": ("SC", "state_constituencies", "2023-03-18"),
}
WARD_KEYS = {"SD": "senatorial_district_id", "FC": "federal_constituency_id", "SC": "state_constituency_id"}
WARD_COLUMNS = {"SD": "senatorial_district", "FC": "federal_constituency", "SC": "state_constituency"}

# Misspelled state names inside INEC's unit names: (wrong word, right word).
NAME_FIXES = [("Ademawa", "Adamawa"), ("Deltal", "Delta"), ("Nassarawa", "Nasarawa")]
UNIT_NAMES = {("SD", "FCT"): "FCT"}  # IReV writes "fct"

# Reviewed fixes to single unit names: code -> (name, reason). INEC's spelling stays an alias.
UNIT_NAME_FIXES = {
    "SC018": ("Ugwunagbo", "INEC writes 'Ugwuna Agbo L.G.A'; the constituency is Ugwunagbo LGA"),
    "SC732": ("Ijebu North II (Ago-Iwoye/Oru/Awa)", "closing bracket missing in INEC's name"),
    "SC736": ("Odogbolu (Alekkun-Ifesowapo/Laporu)", "closing bracket missing in INEC's name"),
}

# State constituency codes INEC typed twice: (state, IReV name) -> right code.
SC_CODE_FIXES = {
    ("DELTA", "IKA SOUTH"): "SC/251/DT",  # typed SC/252/DT, same as Isoko North
    ("GOMBE", "BILLIRI WEST"): "SC/376/GM",  # typed SC/076GM, same number as Aguata I (Anambra)
    ("OGUN", "REMO NORTH (IDARAPO)"): "SC/741/OG",  # typed SC/941/OG, same number as Lau (Taraba)
}

UNIT_FIELDS = ["code", "state_code", "inec_code", "name", "slug", "aliases", "sources"]
WARD_FIELDS = ["code", "lga_code", "state_code", "name", "slug", "senatorial_district", "federal_constituency",
               "state_constituency", "aliases", "unverified_fields", "sources"]


def load(name: str):
    return json.loads((RAW / f"{name}.json").read_text(encoding="utf-8"))["data"]


def read_csv(name: str) -> list[dict]:
    with (DATA / f"{name}.csv").open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(name: str, fields: list[str], rows: list[dict]) -> None:
    with (DATA / f"{name}.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def display(prefix: str, raw: str) -> str:
    name = title(tidy(raw))
    for wrong, right in NAME_FIXES:
        name = re.sub(rf"\b{wrong}\b", right, name)
    return UNIT_NAMES.get((prefix, name.upper()), name)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    report: list[str] = []
    elections, irev_wards = load("elections"), load("wards")
    states = read_csv("states")
    state_by_inec = {s["inec_code"]: s["code"] for s in states}

    # ---- units: one per IReV domain, named from the 2023 general election
    units: dict[str, dict[int, dict]] = {}
    for kind, (prefix, fname, general) in KINDS.items():
        by_domain: dict[int, list[dict]] = defaultdict(list)
        for lst in elections[kind].values():
            for e in lst:
                by_domain[e["domain_id"]].append(e)
        out: dict[int, dict] = {}
        for did, es in by_domain.items():
            es.sort(key=lambda e: (not e["election_date"].startswith(general), e["election_date"]), reverse=False)
            main_e = es[0]
            dom, st = main_e["domain"], main_e["state"]
            fix = SC_CODE_FIXES.get((st["name"], dom["name"])) if prefix == "SC" else None
            if fix:
                report.append(f"{prefix} code fix: {st['name']}/{dom['name']}: {dom['code']} -> {fix}")
            # INEC's codes are "SC/001/AB"; a few lack a slash or carry a stray space.
            m = re.fullmatch(r"([A-Z]{2})/?(\d+)/?([A-Z]{2,3})", re.sub(r"\s", "", (fix or dom["code"]).upper()))
            if not m or m[1] != prefix:
                raise SystemExit(f"Unexpected INEC code {dom['code']!r} for {dom['name']}")
            inec_code, num = f"{m[1]}/{m[2]}/{m[3]}", int(m[2])
            name = display(prefix, dom["name"])
            others = {display(prefix, e["domain"]["name"]) for e in es[1:]}
            code = f"{prefix}{num:03d}"
            if code in UNIT_NAME_FIXES:
                report.append(f"{code} name fix: {name!r} -> {UNIT_NAME_FIXES[code][0]!r} ({UNIT_NAME_FIXES[code][1]})")
                if key(name) != key(UNIT_NAME_FIXES[code][0]):
                    others.add(name)
                name = UNIT_NAME_FIXES[code][0]
            out[did] = {
                "code": code, "state_code": state_by_inec[st["code"].zfill(2)],
                "inec_code": inec_code, "name": name, "slug": slugify(name),
                "aliases": "|".join(sorted(n for n in others if key(n) != key(name))), "sources": SOURCE,
                "_general": main_e["election_date"].startswith(general),
            }
        units[prefix] = out

    # ---- ward links
    wards = read_csv("wards")
    by_lga: dict[str, list[dict]] = defaultdict(list)
    for w in wards:
        by_lga[w["code"][:5]].append(w)
    lgas = read_csv("lgas")
    lga_by_inec = {l["inec_code"]: l for l in lgas}
    links: dict[str, dict[str, int]] = {}
    for lst in irev_wards.values():
        for lg in lst:
            lcode = f"{lg['state']['code'].zfill(2)}-{lg['lga']['code'].zfill(2)}"
            ours = by_lga[lcode]
            by_name, by_alias = defaultdict(list), defaultdict(list)
            for w in ours:
                by_name[key(w["name"])].append(w)
                for n in filter(None, w["aliases"].split("|")):
                    by_alias[key(n)].append(w)
            for iw in lg["wards"]:  # current name, then an older spelling, then the ward code
                hits = by_name.get(key(iw["name"])) or by_alias.get(key(iw["name"])) or []
                if len(hits) == 1:
                    w = hits[0]
                else:
                    w = next(x for x in ours if x["code"] == f"{lcode}-{iw['code'].zfill(2)}")
                if w["code"] in links:
                    raise SystemExit(f"Two IReV wards matched {w['code']}")
                if w["code"][-2:] != iw["code"].zfill(2):
                    report.append(f"Ward matched by name, not code: IReV {lcode}-{iw['code']} {iw['name']} -> {w['code']} {w['name']}")
                links[w["code"]] = {p: iw[k] for p, k in WARD_KEYS.items()}
    missing = [w["code"] for w in wards if w["code"] not in links]
    if missing:
        raise SystemExit(f"{len(missing)} wards not in IReV: {missing[:10]}")

    # FCT placeholder state constituency: linked only to FCT wards and never named in an election.
    ward_state = {w["code"]: w["state_code"] for w in wards}
    placeholder = {l["SC"] for c, l in links.items() if ward_state[c] == "FC"}
    for did in placeholder:
        if did in units["SC"]:
            raise SystemExit(f"FCT state constituency {did} is a real election domain")
    for c, l in links.items():
        if l["SC"] in placeholder:
            l["SC"] = None
    report.append(f"FCT: IReV placeholder state constituency {sorted(placeholder)} dropped (the FCT has no House of Assembly)")

    # Suspected mislinks: the ward's federal constituency differs from that of every other ward
    # in its state constituency.
    sc_fcs: dict[int, Counter] = defaultdict(Counter)
    for l in links.values():
        if l["SC"]:
            sc_fcs[l["SC"]][l["FC"]] += 1
    ward_by_code = {w["code"]: w for w in wards}
    for c, l in sorted(links.items()):
        unverified = []
        if l["SC"] and sc_fcs[l["SC"]][l["FC"]] == 1 and sum(sc_fcs[l["SC"]].values()) > 1:
            unverified.append("state_constituency")
            report.append(f"Suspected IReV mislink (kept, unverified): ward {c} {ward_by_code[c]['name']} -> "
                          f"{units['SC'][l['SC']]['name']} ({units['SC'][l['SC']]['code']})")
        w = ward_by_code[c]
        for p, col in WARD_COLUMNS.items():
            w[col] = units[p][l[p]]["code"] if l[p] else ""
        w["unverified_fields"] = "|".join(unverified)
        if SOURCE not in w["sources"].split("|"):
            w["sources"] += "|" + SOURCE

    # ---- LGA senatorial districts (an LGA is never split between districts)
    lga_sd: dict[str, set] = defaultdict(set)
    for c, l in links.items():
        lga_sd[ward_by_code[c]["lga_code"]].add(l["SD"])
    for l in lgas:
        sds = lga_sd[l["code"]]
        if len(sds) != 1:
            raise SystemExit(f"LGA {l['name']} is in {len(sds)} senatorial districts")
        new = units["SD"][next(iter(sds))]["name"]
        if l["senatorial_district"] and key(new) != key(l["senatorial_district"]):
            report.append(f"LGA senatorial district: {l['state_code']}/{l['name']}: OCHA COD-AB {l['senatorial_district']!r} -> INEC {new!r}")
        l["senatorial_district"] = new
        if SOURCE not in l["sources"].split("|"):
            l["sources"] += "|" + SOURCE

    # Units never linked to a ward cannot be placed; units with no 2023 election are reported.
    used = {p: {l[p] for l in links.values() if l[p]} for p in WARD_KEYS}
    for p, us in units.items():
        for did, u in list(us.items()):
            if did not in used[p]:
                raise SystemExit(f"{p} {u['name']} has no wards")
            if not u.pop("_general"):
                report.append(f"{p} {u['code']} {u['name']}: not in the 2023 general election list; named from a later election")

    for prefix, (fname, rows) in {p: (KINDS[k][1], list(units[p].values())) for k, (p, *_ ) in KINDS.items()}.items():
        codes = Counter(r["code"] for r in rows)
        if any(v > 1 for v in codes.values()):
            raise SystemExit(f"{prefix}: duplicate codes {[c for c, v in codes.items() if v > 1]}")
        rows.sort(key=lambda r: r["code"])
        write_csv(fname, UNIT_FIELDS, rows)
        print(f"{fname}: {len(rows)}")
    write_csv("wards", WARD_FIELDS, wards)
    write_csv("lgas", list(lgas[0].keys()), lgas)
    print(f"wards linked: {len(links)}")
    for line in report:
        print("  " + line)


if __name__ == "__main__":
    main()
