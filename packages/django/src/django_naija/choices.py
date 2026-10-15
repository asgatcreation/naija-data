"""Choice lists for states, LGAs and banks. They are functions, so Django (5.0+) can use them as
callable choices and migrations stay small."""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

import naija_data as ng


def state_choices() -> List[Tuple[str, str]]:
    """[("AB", "Abia"), ..., ("FC", "Federal Capital Territory"), ...] stored as ISO 3166-2 codes."""
    return [(s.code, s.name) for s in ng.states()]


def lga_choices(state: Optional[str] = None):
    """LGAs as (P-code, name) pairs. With `state`, only that state's LGAs; without it, grouped by
    state for <optgroup> menus: [("Abia", [("NG001001", "Aba North"), ...]), ...]."""
    if state:
        return [(l.code, l.name) for l in ng.lgas(state)]
    return [(s.name, [(l.code, l.name) for l in ng.lgas(s)]) for s in ng.states()]


def ward_choices(lga: str, state: Optional[str] = None) -> List[Tuple[str, str]]:
    """Wards of an LGA as (INEC code, name) pairs."""
    return [(w.code, w.name) for w in ng.wards(lga, state)]


def bank_choices(types: Optional[Sequence[str]] = None, with_cbn_code_only: bool = False) -> List[Tuple[str, str]]:
    """Active banks as (id, name) pairs, short names first where available. Use
    with_cbn_code_only=True for account-number forms, so every choice can be NUBAN-checked."""
    rows = [b for b in ng.banks() if (types is None or b.type in types) and (b.cbn_code or not with_cbn_code_only)]
    return sorted(((b.id, b.short_name or b.name) for b in rows), key=lambda c: c[1].lower())
