"""Record types. Field names match the dataset (and the REST API) in every language."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional, Tuple


class _Record:
    def to_dict(self) -> dict:
        d = asdict(self)  # type: ignore[call-overload]
        return {k: list(v) if isinstance(v, tuple) else v for k, v in d.items()}


@dataclass(frozen=True)
class State(_Record):
    code: str
    iso_code: str
    name: str
    slug: str
    inec_code: str
    pcode: str
    capital: str
    zone: str
    created: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    aliases: Tuple[str, ...]
    unverified_fields: Tuple[str, ...]
    sources: Tuple[str, ...]


@dataclass(frozen=True)
class LGA(_Record):
    code: str
    state_code: str
    inec_code: str
    name: str
    slug: str
    headquarters: Optional[str]
    senatorial_district: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    aliases: Tuple[str, ...]
    unverified_fields: Tuple[str, ...]
    sources: Tuple[str, ...]


@dataclass(frozen=True)
class Ward(_Record):
    code: str
    lga_code: str
    state_code: str
    name: str
    slug: str
    aliases: Tuple[str, ...]


@dataclass(frozen=True)
class Bank(_Record):
    id: str
    name: str
    short_name: Optional[str]
    type: str
    cbn_code: Optional[str]
    nip_code: Optional[str]
    ussd: Optional[str]
    status: str
    status_date: Optional[str]
    merged_into: Optional[str]
    aliases: Tuple[str, ...]
    unverified_fields: Tuple[str, ...]
    sources: Tuple[str, ...]

    @property
    def active(self) -> bool:
        return self.status == "active"


@dataclass(frozen=True)
class SearchResult(_Record):
    kind: str  # "state", "lga" or "ward"
    code: str
    name: str
    state_code: str
    score: int  # 0..1000
    matched: str  # the name or alias that matched


@dataclass(frozen=True)
class PhoneInfo(_Record):
    e164: str  # +2348031234567
    local: str  # 08031234567
    prefix: str  # 0803
    network: Optional[str]  # network the number block was allocated to (see note)
    status: Optional[str]  # NCC block status, None if the prefix is not in the NCC table
    note: str = (
        "Numbers can be ported between networks, so the prefix shows the network the number "
        "was first allocated to, not necessarily its network today."
    )
