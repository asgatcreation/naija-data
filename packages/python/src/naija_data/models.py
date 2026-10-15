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
class PhoneNumber(_Record):
    e164: str  # +2348031234567
    local: str  # 08031234567
    national: str  # 8031234567 (national significant number, without the trunk 0)
    type: str  # "mobile", "fixed", "toll_free" or "non_toll_free"
    prefix: str  # mobile/special prefix ("0803", "0800") or fixed-line area code ("01")
    area: Optional[str]  # fixed lines: the NCC primary centre, e.g. "Lagos"
    network: Optional[str]  # mobile: network the block was allocated to; others: the allottee
    allocated: bool  # the number falls in a block the NCC has allocated
    note: Optional[str]  # mobile: number portability caveat


@dataclass(frozen=True)
class AreaCode(_Record):
    area_code: str
    primary_centre: str
    ncc_zone: str
    unverified_fields: Tuple[str, ...]


@dataclass(frozen=True)
class Plate(_Record):
    compact: str  # KJA123AB
    display: str  # KJA-123AB
    format: str  # "standard" or "dealer"
    prefix: str  # standard: the Local Government code; dealer: "D" + state code
    number: str  # the three digits
    suffix: str  # standard: series letters; dealer: final character
    state_code: Optional[str]  # dealer plates only
    note: Optional[str]


@dataclass(frozen=True)
class PlateCategory(_Record):
    category: str
    vehicle: str  # "vehicle" or "motorcycle"
    lettering_colour: str
    background_colour: str
    provision: str  # where the National Road Traffic Regulations 2012 set it
