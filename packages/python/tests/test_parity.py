"""Run the shared parity cases (fixtures/parity.json) against the Python package."""

import json
from pathlib import Path

import pytest

import naija_data as ng

FIXTURE = Path(__file__).resolve().parents[3] / "fixtures" / "parity.json"
pytestmark = pytest.mark.skipif(not FIXTURE.exists(), reason="parity fixtures only exist in the repository")


def run(fn, args):
    try:
        if fn == "states":
            return [s.code for s in ng.states()]
        if fn in ("get_state", "get_lga", "get_bank"):
            r = getattr(ng, fn)(*args)
            return None if r is None else (r.id if fn == "get_bank" else r.code)
        if fn == "state_record":
            return ng.get_state(*args).to_dict()
        if fn == "lga_record":
            return ng.get_lga(*args).to_dict()
        if fn == "bank_record":
            return ng.get_bank(*args).to_dict()
        if fn in ("lgas", "find_lgas", "wards"):
            return [x.code for x in getattr(ng, fn)(*args)]
        if fn in ("banks", "find_banks", "banks_for_nuban"):
            return [b.id for b in getattr(ng, fn)(*args)]
        if fn == "get_ward":
            w = ng.get_ward(*args)
            return w.to_dict() if w else None
        if fn == "search":
            q, kinds, limit = args
            return [[r.kind, r.code, r.score, r.matched] for r in ng.search(q, kinds=kinds, limit=limit)]
        if fn == "lookup_phone":
            info = ng.lookup_phone(*args)
            return None if info is None else {k: v for k, v in info.to_dict().items() if k != "note"}
        return getattr(ng, fn)(*args)
    except ValueError:
        return {"error": True}


def load_cases():
    if not FIXTURE.exists():
        return []
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]


def test_fixture_matches_packaged_data():
    assert json.loads(FIXTURE.read_text(encoding="utf-8"))["data_version"] == ng.meta()["data_version"]


def test_all_parity_cases():
    failures = []
    for case in load_cases():
        got = run(case["fn"], case["args"])
        if got != case["expect"]:
            failures.append(f"{case['fn']}{tuple(case['args'])}: expected {case['expect']!r}, got {got!r}")
    assert not failures, f"{len(failures)} parity failures:\n" + "\n".join(failures[:20])
