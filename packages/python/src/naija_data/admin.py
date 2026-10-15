"""States, LGAs, wards and fuzzy search."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

from ._load import load
from ._text import norm, score
from .models import LGA, SearchResult, State, Ward

StateLike = Union[str, State]
LGALike = Union[str, LGA]

KIND_ORDER = {"state": 0, "lga": 1, "ward": 2}


@lru_cache(maxsize=None)
def _states() -> Tuple[State, ...]:
    return tuple(State(**{**r, "aliases": tuple(r["aliases"]), "unverified_fields": tuple(r["unverified_fields"]),
                          "sources": tuple(r["sources"])}) for r in load("states"))


@lru_cache(maxsize=None)
def _lgas() -> Tuple[LGA, ...]:
    return tuple(LGA(**{**r, "aliases": tuple(r["aliases"]), "unverified_fields": tuple(r["unverified_fields"]),
                        "sources": tuple(r["sources"])}) for r in load("lgas"))


@lru_cache(maxsize=None)
def _wards() -> Tuple[Ward, ...]:
    raw = load("wards")
    fields = raw["fields"]
    out = []
    for row in raw["rows"]:
        d = dict(zip(fields, row))
        d["aliases"] = tuple(d["aliases"])
        out.append(Ward(**d))
    return tuple(out)


@lru_cache(maxsize=None)
def _state_index() -> Dict[str, State]:
    index: Dict[str, State] = {}
    for s in _states():
        for term in (s.name, s.slug, *s.aliases):
            index.setdefault(norm(term), s)
    return index


@lru_cache(maxsize=None)
def _lga_name_index() -> Dict[str, Tuple[LGA, ...]]:
    index: Dict[str, List[LGA]] = {}
    for l in _lgas():
        for key in {norm(t) for t in (l.name, l.slug, *l.aliases)}:
            index.setdefault(key, []).append(l)
    return {k: tuple(v) for k, v in index.items()}


@lru_cache(maxsize=None)
def _wards_by_lga() -> Dict[str, Tuple[Ward, ...]]:
    out: Dict[str, List[Ward]] = {}
    for w in _wards():
        out.setdefault(w.lga_code, []).append(w)
    return {k: tuple(v) for k, v in out.items()}


# ---------------------------------------------------------------- states

def states() -> List[State]:
    """All 36 states and the FCT, sorted by name."""
    return list(_states())


def get_state(query: StateLike) -> Optional[State]:
    """Find a state by ISO code ("LA", "NG-LA"), INEC code ("24"), P-code ("NG025"), slug,
    name or alias ("Lagos", "lagos state", "Abuja", "FCT", "Akwa-Ibom"). Returns None if unknown."""
    if isinstance(query, State):
        return query
    q = query.strip()
    up = q.upper()
    for s in _states():
        if up in (s.code, s.iso_code, s.pcode) or q == s.inec_code:
            return s
    return _state_index().get(norm(q))


def _require_state(state: StateLike) -> State:
    s = get_state(state)
    if s is None:
        raise ValueError(f"Unknown state: {state!r}")
    return s


# ---------------------------------------------------------------- LGAs

def lgas(state: Optional[StateLike] = None) -> List[LGA]:
    """All 774 LGAs, or the LGAs of one state, sorted by name. Raises ValueError for an unknown state."""
    if state is None:
        return sorted(_lgas(), key=lambda l: (l.name, l.code))
    code = _require_state(state).code
    return [l for l in _lgas() if l.state_code == code]


def find_lgas(name: str) -> List[LGA]:
    """Every LGA whose name or alias matches exactly (ignoring case and punctuation).
    Several states share LGA names, e.g. "Surulere" (Lagos and Oyo) or "Obi" (Benue and Nasarawa)."""
    return list(_lga_name_index().get(norm(name), ()))


def get_lga(query: LGALike, state: Optional[StateLike] = None) -> Optional[LGA]:
    """Find an LGA by P-code ("NG025011"), INEC code ("24-11"), or name/alias. A name shared by
    LGAs in several states returns None unless `state` is given."""
    if isinstance(query, LGA):
        return query
    q = query.strip()
    if re.fullmatch(r"(?i)ng\d{6}", q):
        return next((l for l in _lgas() if l.code == q.upper()), None)
    if re.fullmatch(r"\d{2}-\d{2}", q):
        return next((l for l in _lgas() if l.inec_code == q), None)
    matches = find_lgas(q)
    if state is not None:
        code = _require_state(state).code
        matches = [l for l in matches if l.state_code == code]
    return matches[0] if len(matches) == 1 else None


def _require_lga(lga: LGALike, state: Optional[StateLike] = None) -> LGA:
    l = get_lga(lga, state)
    if l is None:
        raise ValueError(f"Unknown or ambiguous LGA: {lga!r}" + ("" if state else " (pass state= to choose)"))
    return l


# ---------------------------------------------------------------- wards

def wards(lga: LGALike, state: Optional[StateLike] = None) -> List[Ward]:
    """Wards (INEC registration areas) of an LGA, in INEC code order."""
    return list(_wards_by_lga().get(_require_lga(lga, state).code, ()))


def get_ward(code: str) -> Optional[Ward]:
    """Find a ward by its INEC code, e.g. "24-11-01"."""
    code = code.strip()
    return next((w for w in _wards() if w.code == code), None)


# ---------------------------------------------------------------- search

def _candidates(kinds: Iterable[str]):
    if "state" in kinds:
        for s in _states():
            yield "state", s.code, s.name, s.code, (s.name, s.code, *s.aliases)
    if "lga" in kinds:
        for l in _lgas():
            yield "lga", l.code, l.name, l.state_code, (l.name, *l.aliases)
    if "ward" in kinds:
        for w in _wards():
            yield "ward", w.code, w.name, w.state_code, (w.name, *w.aliases)


def search(query: str, kinds: Sequence[str] = ("state", "lga"), limit: int = 10,
           min_score: int = 600) -> List[SearchResult]:
    """Fuzzy search across states and LGAs (add "ward" to `kinds` to include wards).

    Handles case, punctuation, aliases and typos: "lagso", "akwa-ibom", "abuja", "ikeja lga".
    Results are ordered by score (0..1000), then states before LGAs before wards, then name.
    """
    q = norm(query)
    if not q:
        return []
    results = []
    for kind, code, name, state_code, terms in _candidates(kinds):
        best, matched = 0, ""
        for term in terms:
            s = score(q, norm(term))
            if s > best:
                best, matched = s, term
        if best >= min_score:
            results.append(SearchResult(kind, code, name, state_code, best, matched))
    results.sort(key=lambda r: (-r.score, KIND_ORDER[r.kind], r.name, r.code))
    return results[:limit]


def search_wards(query: str, limit: int = 10, min_score: int = 600) -> List[SearchResult]:
    """Fuzzy search across all 8,809 wards (same as search(query, kinds=("ward",)))."""
    return search(query, kinds=("ward",), limit=limit, min_score=min_score)
