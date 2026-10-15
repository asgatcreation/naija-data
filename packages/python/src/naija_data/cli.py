"""Command line: `naija lga lagos`, `naija bank 058`, `naija nuban 0123456789`, ...

Run `naija --help` for all commands. Add --json to any command for machine-readable output.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from . import (banks, banks_for_nuban, find_banks, get_bank, get_lga, get_state, is_valid_nuban, lgas,
               lookup_phone, meta, search, states, wards, __version__)


def _out(args, data, lines: List[str]) -> int:
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("\n".join(lines) if lines else "No results.")
    return 0 if data not in (None, []) else 1


def main(argv: Optional[List[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="naija", description="Nigerian reference data from naija-data.")
    p.add_argument("--version", action="version", version=f"naija-data {__version__} (data {meta()['data_version']})")
    p.add_argument("--json", action="store_true", help="print JSON")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("states", help="list states and the FCT")
    sp = sub.add_parser("state", help="show one state");  sp.add_argument("query")
    sp = sub.add_parser("lga", help="list a state's LGAs, or show one LGA");  sp.add_argument("query")
    sp.add_argument("--state", help="state, when an LGA name exists in several states")
    sp = sub.add_parser("wards", help="list an LGA's wards");  sp.add_argument("lga")
    sp.add_argument("--state")
    sp = sub.add_parser("search", help="fuzzy search states and LGAs");  sp.add_argument("query")
    sp = sub.add_parser("bank", help="look up a bank by code or name");  sp.add_argument("query")
    sp = sub.add_parser("banks", help="list institutions");  sp.add_argument("--type")
    sp = sub.add_parser("nuban", help="validate a 10-digit account number");  sp.add_argument("account")
    sp.add_argument("bank", nargs="?", help="bank code or name; omit to list possible banks")
    sp = sub.add_parser("phone", help="normalise a mobile number and guess its network");  sp.add_argument("number")
    args = p.parse_args(argv)

    if args.cmd == "states":
        rows = states()
        return _out(args, [s.to_dict() for s in rows], [f"{s.code}  {s.name:26} capital: {s.capital:14} {s.zone}" for s in rows])
    if args.cmd == "state":
        s = get_state(args.query)
        return _out(args, s and s.to_dict(), [] if not s else [
            f"{s.name} ({s.iso_code})", f"  capital: {s.capital}", f"  zone: {s.zone}",
            f"  LGAs: {len(lgas(s))}", f"  INEC code: {s.inec_code}   P-code: {s.pcode}"])
    if args.cmd == "lga":
        st = get_state(args.query) if not args.state else None
        if st:
            rows = lgas(st)
            return _out(args, [l.to_dict() for l in rows], [f"{st.name}: {len(rows)} LGAs"] + [f"  {l.code}  {l.name}" for l in rows])
        l = get_lga(args.query, args.state)
        return _out(args, l and l.to_dict(), [] if not l else [
            f"{l.name} ({l.code}), {get_state(l.state_code).name}",
            f"  headquarters: {l.headquarters or 'unknown'}" + (" (unverified)" if "headquarters" in l.unverified_fields else ""),
            f"  senatorial district: {l.senatorial_district}", f"  wards: {len(wards(l))}"])
    if args.cmd == "wards":
        rows = wards(args.lga, args.state)
        return _out(args, [w.to_dict() for w in rows], [f"  {w.code}  {w.name}" for w in rows])
    if args.cmd == "search":
        rows = search(args.query)
        return _out(args, [r.to_dict() for r in rows], [f"  {r.score:4}  {r.kind:5} {r.code:9} {r.name}" + (
            f" ({r.state_code})" if r.kind != "state" else "") for r in rows])
    if args.cmd == "bank":
        b = get_bank(args.query)
        rows = [b] if b else find_banks(args.query, limit=5)
        return _out(args, [x.to_dict() for x in rows], [
            f"{x.name}  [{x.type}]  CBN code: {x.cbn_code or '-'}  NIP code: {x.nip_code or '-'}  USSD: {x.ussd or '-'}"
            + ("" if x.active else f"  ({x.status} {x.status_date})") for x in rows])
    if args.cmd == "banks":
        rows = banks(args.type)
        return _out(args, [b.to_dict() for b in rows], [f"  {b.cbn_code or '-':6} {b.name}" for b in rows])
    if args.cmd == "nuban":
        if args.bank:
            ok = is_valid_nuban(args.account, args.bank)
            print(json.dumps({"account": args.account, "bank": args.bank, "valid": ok}) if args.json else
                  f"{args.account}: {'valid' if ok else 'NOT valid'} for {args.bank}")
            return 0 if ok else 1
        rows = banks_for_nuban(args.account)
        return _out(args, [b.to_dict() for b in rows], [f"{args.account} has a valid check digit for {len(rows)} banks:"]
                    + [f"  {b.cbn_code:6} {b.name}" for b in rows])
    if args.cmd == "phone":
        info = lookup_phone(args.number)
        return _out(args, info and info.to_dict(), [] if not info else [
            f"{info.e164}  ({info.local})", f"  network: {info.network or 'unknown'} (prefix {info.prefix})", f"  note: {info.note}"])
    return 2


if __name__ == "__main__":
    sys.exit(main())
