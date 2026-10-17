"""Electoral units from INEC: senatorial districts, federal constituencies and state constituencies."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Dict, List, Optional, Tuple, Union

from ._load import load
from ._text import norm
from .admin import LGALike, StateLike, _lgas, _require_lga, _require_state, _wards
from .models import LGA, Constituency, Ward

ConstituencyLike = Union[str, Constituency]

CONSTITUENCY_KINDS = ("senatorial_district", "federal_constituency", "state_constituency")
_KIND_ORDER = {k: i for i, k in enumerate(CONSTITUENCY_KINDS)}


@lru_cache(maxsize=None)
def _units() -> Tuple[Constituency, ...]:
    return tuple(Constituency(**{**r, "aliases": tuple(r["aliases"]), "lga_codes": tuple(r["lga_codes"]),
                                 "sources": tuple(r["sources"])}) for r in load("constituencies"))


@lru_cache(maxsize=None)
def _by_code() -> Dict[str, Constituency]:
    out: Dict[str, Constituency] = {}
    for u in _units():
        out[u.code] = u
        out[u.inec_code] = u
    return out


def _check_kind(kind: Optional[str]) -> None:
    if kind is not None and kind not in _KIND_ORDER:
        raise ValueError(f"Unknown constituency kind: {kind!r} (use one of {', '.join(CONSTITUENCY_KINDS)})")


def constituencies(kind: Optional[str] = None, state: Optional[StateLike] = None) -> List[Constituency]:
    """Electoral units of one kind (or all), optionally in one state, in INEC code order."""
    _check_kind(kind)
    code = _require_state(state).code if state is not None else None
    return [u for u in _units() if (kind is None or u.kind == kind) and (code is None or u.state_code == code)]


def senatorial_districts(state: Optional[StateLike] = None) -> List[Constituency]:
    """The 109 senatorial districts (3 per state, 1 for the FCT), or those of one state."""
    return constituencies("senatorial_district", state)


def federal_constituencies(state: Optional[StateLike] = None) -> List[Constituency]:
    """The 360 federal constituencies (House of Representatives seats), or those of one state."""
    return constituencies("federal_constituency", state)


def state_constituencies(state: Optional[StateLike] = None) -> List[Constituency]:
    """The 990 state constituencies (House of Assembly seats), or those of one state.
    The FCT has none: it has no House of Assembly."""
    return constituencies("state_constituency", state)


def get_constituency(code: ConstituencyLike) -> Optional[Constituency]:
    """Find a unit by code ("SD001", "FC001", "SC001") or INEC code ("FC/001/AB"). None if unknown."""
    if isinstance(code, Constituency):
        return code
    return _by_code().get(re.sub(r"\s", "", code).upper())


def find_constituencies(name: str, kind: Optional[str] = None, state: Optional[StateLike] = None) -> List[Constituency]:
    """Every unit whose name or alias matches exactly (ignoring case and punctuation), e.g. "Ikeja"
    (a federal and a state constituency) or "Lagos West"."""
    q = norm(name)
    return [u for u in constituencies(kind, state) if q in {norm(t) for t in (u.name, u.slug, *u.aliases)}]


def _require(code: ConstituencyLike) -> Constituency:
    u = get_constituency(code)
    if u is None:
        raise ValueError(f"Unknown constituency: {code!r}")
    return u


def constituency_lgas(code: ConstituencyLike) -> List[LGA]:
    """LGAs a unit covers in full or in part, sorted by name. A few LGAs are split between
    constituencies (e.g. Surulere I and II in Lagos): use constituency_wards for the exact area."""
    codes = set(_require(code).lga_codes)
    return sorted((l for l in _lgas() if l.code in codes), key=lambda l: (l.name, l.code))


def constituency_wards(code: ConstituencyLike) -> List[Ward]:
    """Wards (INEC registration areas) that make up a unit, in INEC code order."""
    u = _require(code)
    return [w for w in _wards() if getattr(w, u.kind) == u.code]  # ward attributes are named after the kinds


def lga_constituencies(lga: LGALike, state: Optional[StateLike] = None) -> List[Constituency]:
    """The senatorial district, federal constituencies and state constituencies an LGA lies in
    (more than one when the LGA is split), ordered by kind then code."""
    code = _require_lga(lga, state).code
    return sorted((u for u in _units() if code in u.lga_codes), key=lambda u: (_KIND_ORDER[u.kind], u.code))
