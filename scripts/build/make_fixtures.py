"""Generate fixtures/parity.json: shared test cases that the Python, JS and Go packages must agree on.

Expected values come from the Python package (the reference implementation). Its correctness is
covered separately by hand-written tests (packages/python/tests/test_api.py); this file makes sure
the other languages behave exactly the same, including fuzzy-search scores.

Run:  python scripts/build/make_fixtures.py          (write)
      python scripts/build/make_fixtures.py --check  (fail if out of date; used in CI)
See fixtures/README.md for how each function's result is projected to JSON.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "python" / "src"))

import naija_data as ng  # noqa: E402

OUT = ROOT / "fixtures" / "parity.json"


def project(fn: str, args: list):
    """Call the Python implementation and project the result as described in fixtures/README.md."""
    try:
        if fn == "states":
            return [s.code for s in ng.states()]
        if fn == "get_state":
            s = ng.get_state(*args)
            return s.code if s else None
        if fn == "state_record":
            return ng.get_state(*args).to_dict()
        if fn == "lgas":
            return [l.code for l in ng.lgas(*args)]
        if fn == "find_lgas":
            return [l.code for l in ng.find_lgas(*args)]
        if fn == "get_lga":
            l = ng.get_lga(*args)
            return l.code if l else None
        if fn == "lga_record":
            return ng.get_lga(*args).to_dict()
        if fn == "wards":
            return [w.code for w in ng.wards(*args)]
        if fn == "get_ward":
            w = ng.get_ward(*args)
            return w.to_dict() if w else None
        if fn == "search":
            q, kinds, limit = args
            return [[r.kind, r.code, r.score, r.matched] for r in ng.search(q, kinds=kinds, limit=limit)]
        if fn == "get_bank":
            b = ng.get_bank(*args)
            return b.id if b else None
        if fn == "bank_record":
            return ng.get_bank(*args).to_dict()
        if fn == "banks":
            return [b.id for b in ng.banks(*args)]
        if fn == "find_banks":
            return [b.id for b in ng.find_banks(*args)]
        if fn == "nuban_check_digit":
            return ng.nuban_check_digit(*args)
        if fn == "is_valid_nuban":
            return ng.is_valid_nuban(*args)
        if fn == "banks_for_nuban":
            return [b.id for b in ng.banks_for_nuban(*args)]
        if fn == "normalize_phone":
            return ng.normalize_phone(*args)
        if fn == "to_local":
            return ng.to_local(*args)
        if fn in ("parse_phone", "parse_plate"):
            r = getattr(ng, fn)(*args)
            return None if r is None else r.to_dict()
        if fn in ("phone_error", "plate_error", "is_valid_phone", "is_valid_plate"):
            return getattr(ng, fn)(*args)
        if fn in ("area_codes", "plate_categories"):
            return [x.to_dict() for x in getattr(ng, fn)()]
        if fn == "search_wards":
            return [[x.kind, x.code, x.score, x.matched] for x in ng.search_wards(args[0], limit=args[1])]
        if fn == "prefixes":
            return ng.prefixes(*args)
        if fn in ("constituencies", "find_constituencies", "lga_constituencies"):
            return [u.code for u in getattr(ng, fn)(*args)]
        if fn == "get_constituency":
            u = ng.get_constituency(*args)
            return u.code if u else None
        if fn == "constituency_record":
            return ng.get_constituency(*args).to_dict()
        if fn in ("constituency_lgas", "constituency_wards"):
            return [x.code for x in getattr(ng, fn)(*args)]
    except ValueError:
        return {"error": True}
    raise SystemExit(f"Unknown fn {fn}")


def typo(word: str) -> str:
    """Deterministic typo: swap the two middle letters (or drop the last letter of short words)."""
    if len(word) < 4:
        return word[:-1] or word
    i = len(word) // 2
    return word[: i - 1] + word[i] + word[i - 1] + word[i + 1:]


def accounts(n: int) -> list[str]:
    """Deterministic pseudo-random 10-digit numbers (linear congruential generator)."""
    x, out = 20261009, []
    for _ in range(n):
        x = (x * 1103515245 + 12345) % 2**31
        out.append(str(x % 10**10).zfill(10))
    return out


def cases() -> list[tuple[str, list]]:
    c: list[tuple[str, list]] = [("states", [])]
    for s in ng.states():
        for q in [s.code, s.code.lower(), s.iso_code, s.inec_code, s.pcode, s.slug, s.name, s.name.upper(),
                  f"{s.name} State", *s.aliases]:  # a list, not a set: the file must be reproducible
            c.append(("get_state", [q]))
        c.append(("state_record", [s.code]))
        c.append(("lgas", [s.code]))
        c.append(("search", [typo(s.name), ["state", "lga"], 5]))
    c += [("get_state", [q]) for q in ["", "  lagos  ", "Lagos-State", "Nassarawa", "Akwa-Ibom", "abuja", "xx", "99"]]
    c += [("lgas", [None]), ("lgas", ["Atlantis"])]
    for l in ng.lgas():
        c.append(("get_lga", [l.name, l.state_code]))
        c.append(("get_lga", [l.name, None]))
        c.append(("find_lgas", [l.name]))
        c.append(("search", [typo(l.name), ["state", "lga"], 5]))
    for l in ng.lgas()[::25]:
        c += [("lga_record", [l.code]), ("get_lga", [l.code.lower()]), ("get_lga", [l.inec_code]), ("wards", [l.code, None])]
    c += [("wards", ["Surulere", None]), ("wards", ["Surulere", "OY"]), ("wards", ["nowhere", None])]
    c += [("get_ward", [w]) for w in ["24-11-01", "07-07-09", "03-12-11", "30-06-02", "99-99-99", ""]]
    for q in ["lagso", "abuja", "ikeja lga", "yenegoa", "kano", "port harcourt", "amac", "surulere", "obi", "zz",
              "a", "ibadan", "gboyin", "koton karfe", "ilesha"]:
        c.append(("search", [q, ["state", "lga"], 10]))
    # Accented and compatibility input must fold the same way in every language (Go uses a
    # generated table instead of NFKD): Yoruba tones and dots, decomposed accents, full-width forms.
    accented = ["Ọ̀yọ́", "Ògùn", "Kàdúná", "Ẹ̀kìtì",
                "Ọ̀ṣun", "ÀKWÀ ÌBÓM", "Ｌａｇｏｓ", "Kanó State",
                "Ìeja", "Abújà", "Straße", "ﬁka"]
    for q in accented:
        c += [("get_state", [q]), ("search", [q, ["state", "lga"], 5])]
    for q in ["Ìbàdàn", "Ọyọ", "Ilé-Ifẹ̀"]:
        c.append(("search", [q, ["state", "lga"], 5]))
    for q in ["anifowoshe", "abak urban", "itak", "ward 10"]:
        c.append(("search", [q, ["ward"], 5]))
    for b in ng.banks(active_only=False):
        c.append(("get_bank", [b.id]))
        if b.short_name:
            c.append(("get_bank", [b.short_name]))
            c.append(("find_banks", [typo(b.short_name)]))
    for code in ["044", "058", "063", "030", "50211", "000013", "999992", "120001", "123", "GTB", "uba", "Kuda Bank", ""]:
        c.append(("get_bank", [code]))
    c += [("bank_record", [i]) for i in ["gtbank", "diamond-bank", "heritage-bank", "kuda", "opay"]]
    c += [("banks", [t, True]) for t in ng.BANK_TYPES] + [("banks", [None, False]), ("banks", ["shop", True])]
    c += [("nuban_check_digit", ["011", "000001457"]), ("nuban_check_digit", ["50547", "000021457"]),
          ("nuban_check_digit", ["1234", "000001457"]), ("nuban_check_digit", ["011", "12345"])]
    for a in accounts(300):
        c.append(("banks_for_nuban", [a]))
    for a in accounts(40):
        c += [("is_valid_nuban", [a, "058"]), ("is_valid_nuban", [a, "gtbank"]), ("is_valid_nuban", [a, "50211"])]
    c += [("is_valid_nuban", ["0000014579", "011"]), ("is_valid_nuban", ["0000214579", "50547"]),
          ("is_valid_nuban", ["000001457", "011"]), ("is_valid_nuban", ["00000145790", "011"]),
          ("is_valid_nuban", ["0000014579", "no-such-bank"]), ("is_valid_nuban", ["000-001-4579", "011"])]
    c += [("banks_for_nuban", [x]) for x in ["0000014579", "123", "abcdefghij"]]
    formats = ["0{n}", "+234{n}", "234{n}", "{n}", "+234 (0) {n}", "0{a} {b} {c}", "+234-{a}-{b}-{c}", "(0{a}) {b}.{c}"]
    for p in ng.prefixes():
        n = p[1:] + "1234567"
        for f in formats:
            q = f.format(n=n, a=n[:3], b=n[3:6], c=n[6:])
            c += [("normalize_phone", [q]), ("parse_phone", [q])]
        c.append(("to_local", ["+234" + n]))
    for p, sub in [("0702", "0000001"), ("0702", "1500000"), ("0702", "5999999"), ("0702", "8000000"), ("0819", "2500000")]:
        c.append(("parse_phone", [p + sub]))
    c += [("normalize_phone", [q]) for q in ["", "0803123456", "080312345678", "+1 803 123 4567", "+2348031234567",
                                             "06031234567", "0703-123-4567", "234 803 123 4567", "0803 123 4567 ext 2"]]
    # Strict validation: every area code, special ranges, every error reason.
    for a in ng.area_codes():
        sub = "1234567"[: 8 - len(a.area_code) + 1]
        for q in [a.area_code + sub, "+234" + a.area_code[1:] + sub, a.area_code + sub[:-1]]:
            c += [("parse_phone", [q]), ("phone_error", [q])]
    for q in ["08001234567", "0800 000 0001", "07001234567", "0700 810 0001", "09001234567", "098 123456",
              "0819 012 3456", "0819 250 0000", "0910 123 4567", "0702 400 0000", "0702 600 0000", "0704 700 0001",
              "00234 803 123 4567", "00 1 202 555 0100", "+", "00", "+234", "234", "+234 1", "0803\u00a0123\u00a04567",
              "\uff10\uff18\uff10\uff13", "\u0660\u0668\u0660\u0663"]:
        c += [("parse_phone", [q]), ("phone_error", [q]), ("is_valid_phone", [q, None]),
              ("is_valid_phone", [q, ["mobile"]]), ("is_valid_phone", [q, ["fixed", "toll_free"]])]
    c += [("area_codes", []), ("plate_categories", [])]
    for q in ["kja 123 ab", "KJA-123AB", "kja123ab", "EKY 456 DE", "DKN 135 3", "dla5481", "DOS-283-2", "DZZ 135 3",
              "DKN 135 X", "AB-123-CD", "ABCD-123-EF", "KJA-12AB", "", "  ", "KJ@-123AB", "kja.123.ab", "\u00c0BC-123DE",
              "kjß-123ab", "DFC 001 0"]:
        c += [("parse_plate", [q]), ("plate_error", [q]), ("is_valid_plate", [q, None]), ("is_valid_plate", [q, ["dealer"]])]
    c += [("search_wards", [q, 5]) for q in ["anifowoshe", "urban ii", "isale"]]
    # Electoral units
    for kind in [None, *ng.CONSTITUENCY_KINDS]:
        c.append(("constituencies", [kind, None]))
        c += [("constituencies", [kind, st.code]) for st in ng.states()]
    c += [("constituencies", ["ward", None]), ("constituencies", [None, "Atlantis"])]
    for i, u in enumerate(ng.constituencies()):
        c += [("get_constituency", [u.code]), ("get_constituency", [u.inec_code.lower()]),
              ("constituency_lgas", [u.code]), ("find_constituencies", [u.name, None, None])]
        if i % 20 == 0:
            c.append(("constituency_record", [u.code]))
        if i % 10 == 0:
            c.append(("constituency_wards", [u.code]))
    c += [("get_constituency", [q]) for q in ["sd001", " FC 001 ", "SC/990/ZF", "FC/001/AB", "SC000", "XX001", ""]]
    c += [("find_constituencies", q) for q in [["Ikeja", None, None], ["ikeja", "state_constituency", None],
                                                ["Lagos West", "senatorial_district", "LA"], ["Surulere I", None, "OY"],
                                                ["nowhere", None, None], ["Ikeja", "nope", None]]]
    c += [("lga_constituencies", [l.code, None]) for l in ng.lgas()]
    c += [("lga_constituencies", q) for q in [["Surulere", "LA"], ["Surulere", None], ["nowhere", None]]]
    c += [("constituency_lgas", ["nope"]), ("constituency_wards", ["nope"]), ("constituency_wards", ["SC001"])]
    c += [("prefixes", [None]), ("prefixes", ["MTN"]), ("prefixes", ["glo"]), ("prefixes", ["9mobile"]), ("prefixes", ["nope"])]
    return c


def main() -> None:
    out, seen = [], set()
    for fn, args in cases():
        k = json.dumps([fn, args])
        if k in seen:
            continue
        seen.add(k)
        out.append({"fn": fn, "args": args, "expect": project(fn, args)})
    content = (json.dumps({"data_version": ng.meta()["data_version"], "cases": out}, ensure_ascii=False, indent=0)
               + "\n").encode("utf-8")
    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_bytes() != content:
            raise SystemExit("fixtures/parity.json is out of date. Run: python scripts/build/make_fixtures.py")
        print(f"Parity fixtures are up to date ({len(out)} cases).")
        return
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_bytes(content)
    print(f"{len(out)} parity cases -> {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
