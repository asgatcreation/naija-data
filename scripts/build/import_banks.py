"""Build data/banks.csv from the CBN register plus code lists from payment providers.

Rules
- Which institutions exist, their official name, type and "active" status come ONLY from the
  CBN's lists of licensed financial institutions (cbn.gov.ng/supervision).
- Codes come from two independent public lists: Paystack (GET api.paystack.co/bank) and
  Monnify (GET api.monnify.com/api/v1/sdk/transactions/banks).
  * cbn_code: 3 digits for banks, 5 digits for other financial institutions (OFIs).
  * nip_code: the 6-digit NIBSS Instant Payment institution code.
  A code is "verified" only when both lists agree; otherwise it is listed in
  unverified_fields. Provider lists also contain defunct banks, wallets and products
  (e.g. "ALAT by WEMA"), so they never add institutions on their own.

Run:  python scripts/build/import_banks.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from names import slugify  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / ".cache" / "raw"
DATA = ROOT / "data"

CBN_TYPES = {
    "DMBs": "commercial", "MBs": "merchant", "NIBs": "non_interest", "PSBs": "payment_service_bank",
    "MMOs": "mobile_money_operator", "MFBs": "microfinance", "PMIs": "mortgage", "DFIs": "development_finance",
}

# Which NIP code prefixes belong to which types (NIBSS numbering convention seen in both lists).
NIP_PREFIX_TYPES = {
    "000": {"commercial", "merchant", "non_interest"}, "090": {"microfinance", "development_finance"},
    "50": {"microfinance"}, "51": {"microfinance"}, "120": {"payment_service_bank"},
    "100": {"mobile_money_operator", "microfinance"}, "070": {"mortgage"}, "999": {"mobile_money_operator", "microfinance"},
}

# Words that don't help tell institutions apart.
NOISE = {"LIMITED", "LTD", "PLC", "NIGERIA", "NIG", "THE", "MICROFINANCE", "MICRO", "FINANCE", "MFB", "BANK",
         "PSB", "PAYMENT", "SERVICE", "SERVICES", "MORTGAGE", "MORTAGE", "COMPANY", "OF", "AND", "NIGERIAN"}

# Short names people use, for the big banks. Also used as search aliases.
SHORT = {
    "Access Bank Plc": ("Access Bank", ["Access"]),
    "Citibank Nigeria Limited": ("Citibank", ["Citi"]),
    "Ecobank Nigeria Plc": ("Ecobank", []),
    "Fidelity Bank Plc": ("Fidelity Bank", ["Fidelity"]),
    "First Bank Nigeria Limited": ("First Bank", ["FBN", "FirstBank", "First Bank of Nigeria"]),
    "First City Monument Bank Plc": ("FCMB", ["First City Monument Bank"]),
    "Guaranty Trust Bank Plc": ("GTBank", ["GTB", "GTCO", "Guaranty Trust Bank"]),
    "Stanbic IBTC Bank Plc": ("Stanbic IBTC", ["Stanbic"]),
    "Standard Chartered Bank Nigeria Ltd.": ("Standard Chartered", ["StanChart"]),
    "Union Bank of Nigeria Plc": ("Union Bank", []),
    "United Bank For Africa Plc": ("UBA", ["United Bank for Africa"]),
    "Unity Bank Plc": ("Unity Bank", []),
    "Wema Bank Plc": ("Wema Bank", ["Wema", "ALAT"]),
    "Zenith Bank Plc": ("Zenith Bank", ["Zenith"]),
    "Sterling Bank Plc": ("Sterling Bank", ["Sterling"]),
    "Polaris Bank Plc": ("Polaris Bank", ["Polaris"]),
    "Keystone Bank Limited": ("Keystone Bank", ["Keystone"]),
    "OPAY MFB LIMITED": ("OPay", ["OPay Digital Services", "Paycom"]),
    "Moniepoint MFB": ("Moniepoint", ["Moniepoint MFB", "TeamApt"]),
    "KUDA MFB": ("Kuda", ["Kuda Bank"]),
    "PALMPAY LIMITED": ("PalmPay", []),
    "MOMO PAYMENT SERVICE BANK": ("MoMo PSB", ["MTN MoMo", "MTN Momo PSB"]),
    "SMARTCASH PSB LIMITED": ("SmartCash PSB", ["Airtel SmartCash", "Airtel Smartcash PSB"]),
    "9 PSB Ltd": ("9PSB", ["9mobile 9Payment Service Bank", "9Payment Service Bank"]),
    "Hope PSB Ltd": ("HopePSB", ["Hope PSB"]),
    "Moneymaster PSB Ltd": ("Moneymaster PSB", []),
    "Titan Trust Bank Ltd": ("Titan Trust Bank", ["Titan Bank", "Titan"]),
    "Nova Commercial Bank Limited": ("Nova Bank", ["Nova"]),
    "Diamond Bank Plc": ("Diamond Bank", ["Diamond"]),
    "Heritage Bank Plc": ("Heritage Bank", ["Heritage"]),
    "PAGATECH LIMITED": ("Paga", ["Pagatech"]),
}

# Institutions no longer licensed. Provider lists still carry their codes (old account numbers
# keep working after a merger), so they are kept with their history.
HISTORICAL = [
    {"name": "Diamond Bank Plc", "type": "commercial", "status": "merged", "status_date": "2019-04-01",
     "merged_into": "access-bank", "sources": ["nairametrics-access-diamond-2019", "thecable-access-diamond-2019"]},
    {"name": "Heritage Bank Plc", "type": "commercial", "status": "licence_revoked", "status_date": "2024-06-03",
     "merged_into": "", "sources": ["cbn-heritage-revocation-2024"]},
]

# Provider entries that refer to a historical institution under its successor's name.
PROVIDER_RENAMES = {"Access Bank (Diamond)": "Diamond Bank"}

FIELDS = ["id", "name", "short_name", "type", "cbn_code", "nip_code", "ussd", "status", "status_date",
          "merged_into", "aliases", "unverified_fields", "sources"]


def bank_key(name: str) -> str:
    name = re.sub(r"\(.*?\)", " ", name.upper())
    words = [w for w in re.findall(r"[A-Z0-9]+", name) if w not in NOISE]
    return "".join(words)


def clean_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r"\bLIMITEd\b", "LIMITED", name)
    return name


def code_shape(code: str) -> tuple[str | None, str | None]:
    """Return (cbn_code, nip_code) implied by a provider's code string."""
    if re.fullmatch(r"\d{3}", code):
        return code, None
    if re.fullmatch(r"00\d{3}", code):
        return code[2:], None  # newer banks: CBN code 103 written as 00103 (Monnify and Paystack)
    if re.fullmatch(r"\d{5}", code):
        return code, None
    if re.fullmatch(r"\d{6}", code):
        return None, code
    return None, None  # e.g. "MFB50094", "035A", "09": not usable


def nip_type_ok(nip: str, typ: str) -> bool:
    for prefix, types in NIP_PREFIX_TYPES.items():
        if nip.startswith(prefix):
            return typ in types
    return False


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    cbn = []
    for file, typ in CBN_TYPES.items():
        for r in json.loads((RAW / "cbn" / f"{file}.json").read_text(encoding="utf-8")):
            cbn.append({"name": clean_name(r["name"]), "raw": r["name"], "type": typ, "status": "active",
                        "status_date": "", "merged_into": "", "extra_sources": []})
    for h in HISTORICAL:
        cbn.append({"name": h["name"], "raw": h["name"], "type": h["type"], "status": h["status"],
                    "status_date": h["status_date"], "merged_into": h["merged_into"], "extra_sources": h["sources"]})

    paystack = json.loads((RAW / "paystack" / "banks.json").read_text(encoding="utf-8"))["data"]
    monnify = json.loads((RAW / "monnify" / "banks.json").read_text(encoding="utf-8"))["responseBody"]

    by_key: dict[str, list[dict]] = defaultdict(list)
    for inst in cbn:
        by_key[bank_key(inst["name"])].append(inst)
        short = SHORT.get(inst["name"])
        if short:
            for alias in [short[0], *short[1]]:
                if inst not in by_key[bank_key(alias)]:
                    by_key[bank_key(alias)].append(inst)

    def find(name: str, cbn_code: str | None, nip: str | None) -> dict | None:
        cands = by_key.get(bank_key(name), [])
        if cbn_code and len(cbn_code) == 3:
            cands = [c for c in cands if c["type"] in ("commercial", "merchant", "non_interest")]
        elif cbn_code and len(cbn_code) == 5:
            cands = [c for c in cands if c["type"] not in ("commercial", "merchant", "non_interest")]
        if nip:
            cands = [c for c in cands if nip_type_ok(nip, c["type"])]
        return cands[0] if len(cands) == 1 else None

    evidence: dict[int, dict[str, dict[str, set]]] = defaultdict(lambda: {"cbn_code": defaultdict(set), "nip_code": defaultdict(set), "ussd": defaultdict(set)})
    unmatched = {"paystack": [], "monnify": []}

    for b in paystack:
        cc, nip = code_shape(b["code"])
        inst = find(PROVIDER_RENAMES.get(b["name"], b["name"]), cc, nip)
        if not inst:
            unmatched["paystack"].append(f"{b['code']} {b['name']}")
            continue
        ev = evidence[id(inst)]
        if cc:
            ev["cbn_code"][cc].add("paystack-banks")
        if nip:
            ev["nip_code"][nip].add("paystack-banks")

    for b in monnify:
        cc = code_shape(b["code"] or "")[0]
        nip = b["nipBankCode"] if b["nipBankCode"] and re.fullmatch(r"\d{6}", b["nipBankCode"]) else None
        if cc and len(cc) == 5 and nip == cc.zfill(6):
            cc = None  # some entries repeat the NIP code in the code field
        inst = find(b["name"], cc, nip)
        if not inst:
            unmatched["monnify"].append(f"{b['code']}/{b['nipBankCode']} {b['name']}")
            continue
        ev = evidence[id(inst)]
        if cc:
            ev["cbn_code"][cc].add("monnify-banks")
        if nip:
            ev["nip_code"][nip].add("monnify-banks")
        ussd = b.get("baseUssdCode") or ""
        if re.fullmatch(r"\*\d+(\*\d+)*#", ussd):
            ev["ussd"][ussd].add("monnify-banks")

    rows, conflicts = [], []
    used_ids = set()
    for inst in cbn:
        ev = evidence.get(id(inst), {"cbn_code": {}, "nip_code": {}, "ussd": {}})
        srcs = set(inst["extra_sources"]) or {"cbn-financial-institutions"}
        values, unverified = {}, []
        for field in ("cbn_code", "nip_code", "ussd"):
            opts = ev[field]
            if len(opts) > 1:
                conflicts.append(f"{inst['name']}: {field} sources disagree: {dict((k, sorted(v)) for k, v in opts.items())}")
                values[field] = ""
                continue
            if opts:
                (val, by), = opts.items()
                values[field] = val
                srcs |= by
                if len(by) < 2:
                    unverified.append(field)
            else:
                values[field] = ""
        short, aliases = SHORT.get(inst["name"], (None, []))
        same = {re.sub(r"[^a-z0-9]", "", x.lower()) for x in (inst["name"], short or "")}
        aliases = [a for a in aliases if re.sub(r"[^a-z0-9]", "", a.lower()) not in same]
        rid = slugify(short or re.sub(r"(?i)\b(limited|ltd|plc|nigeria)\b\.?", "", inst["name"]))
        if rid in used_ids:
            rid = f"{rid}-{inst['type'].replace('_', '-')}"
        used_ids.add(rid)
        rows.append({
            "id": rid, "name": inst["name"], "short_name": short or "", "type": inst["type"],
            "cbn_code": values["cbn_code"], "nip_code": values["nip_code"], "ussd": values["ussd"],
            "status": inst["status"], "status_date": inst["status_date"], "merged_into": inst["merged_into"], "aliases": "|".join(aliases), "unverified_fields": "|".join(unverified),
            "sources": "|".join(sorted(srcs)),
        })

    # A code claimed by two active institutions is wrong for at least one of them. If it rests
    # on a single source we cannot tell which, so we drop it from both rather than guess.
    for field in ("cbn_code", "nip_code"):
        owners = defaultdict(list)
        for r in rows:
            if r[field] and r["status"] == "active":
                owners[r[field]].append(r)
        for code, rs in owners.items():
            if len(rs) > 1 and all(field in r["unverified_fields"] for r in rs):
                for r in rs:
                    r[field] = ""
                    r["unverified_fields"] = "|".join(f for f in r["unverified_fields"].split("|") if f and f != field)
                conflicts.append(f"{field} {code} claimed by {[r['name'] for r in rs]} in one source only: dropped")

    rows.sort(key=lambda r: (r["type"], r["name"].lower()))
    with (DATA / "banks.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    def count(pred):
        return sum(1 for r in rows if pred(r))
    print(f"institutions: {len(rows)}")
    print(f"  with cbn_code: {count(lambda r: r['cbn_code'])} (verified {count(lambda r: r['cbn_code'] and 'cbn_code' not in r['unverified_fields'])})")
    print(f"  with nip_code: {count(lambda r: r['nip_code'])} (verified {count(lambda r: r['nip_code'] and 'nip_code' not in r['unverified_fields'])})")
    print(f"  with ussd:     {count(lambda r: r['ussd'])}")
    for c in conflicts:
        print("  CONFLICT", c)
    for src, items in unmatched.items():
        print(f"  {src}: {len(items)} entries not matched to a CBN-licensed institution")
    (ROOT / ".cache" / "extract").mkdir(parents=True, exist_ok=True)
    (ROOT / ".cache" / "extract" / "banks-unmatched.json").write_text(json.dumps(unmatched, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
