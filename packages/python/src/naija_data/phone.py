"""Nigerian phone numbers: strict validation, number type, normalisation and network lookup.

Rules (identical in the JS and Go packages; see fixtures/README.md):
- Accepted input: local ("0803 123 4567", "01 269 1531"), international ("+234 803 123 4567",
  "00234...", "234..."), "+234 (0) ..." and a bare 10-digit mobile number ("8031234567").
- Mobile: 10-digit national number in a block that the NCC allocated to a network, in either the
  Mobile Number Allocation Table (Dec 2023) or the National Numbering Plan (Oct 2022).
- Fixed line: 8-digit national number starting with one of the NCC's 56 area codes.
- Toll-free: 0800 + 7 digits. Non-toll-free special numbers: 0700 + 7 digits.
- 0900 is reserved by the NCC for vanity numbers and is rejected.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

from ._load import load
from .models import AreaCode, PhoneNumber

PORTING_NOTE = (
    "Numbers can be ported between networks, so the prefix shows the network the number "
    "was first allocated to, not necessarily its network today."
)

PHONE_TYPES = ("mobile", "fixed", "toll_free", "non_toll_free")

# Why a number is invalid (returned by phone_error).
PHONE_ERRORS = ("empty", "invalid_characters", "not_nigerian", "bad_length", "unknown_prefix", "unallocated",
                "reserved", "unknown_area_code")

_SEPARATORS = re.compile(r"[\s\-.()/]")
_DIGITS = re.compile(r"[0-9]*")


@lru_cache(maxsize=None)
def _phone() -> dict:
    return load("phone")


@lru_cache(maxsize=None)
def _area_codes() -> Dict[str, dict]:
    return {a["area_code"]: a for a in _phone()["area_codes"]}


def _short_network(allottee: str) -> str:
    """Network name for a mobile block that only the 2022 numbering plan lists."""
    for key, name in (("MTN", "MTN"), ("Airtel", "Airtel"), ("Glo", "Glo"), ("9Mobile", "9mobile"),
                      ("Smile", "Smile"), ("Mafab", "MAFAB"), ("nTel", "nTel")):
        if key.lower() in allottee.lower():
            return name
    return allottee


def _in_plan(nsn: str, number_type: str) -> Optional[dict]:
    for b in _phone()["blocks"]:
        if b["number_type"] == number_type and len(b["range_start"]) == len(nsn) and b["range_start"] <= nsn <= b["range_end"]:
            return b
    return None


def _national(text: str) -> Tuple[Optional[str], Optional[str]]:
    """(national significant number, error)."""
    s = _SEPARATORS.sub("", text.strip())
    if not s:
        return None, "empty"
    if s.startswith("+"):
        s = s[1:]
        if not _DIGITS.fullmatch(s):
            return None, "invalid_characters"
        if not s.startswith("234"):
            return None, "not_nigerian"
    elif s.startswith("00"):
        if not _DIGITS.fullmatch(s):
            return None, "invalid_characters"
        if not s.startswith("00234"):
            return None, "not_nigerian"
        s = s[2:]
    if not _DIGITS.fullmatch(s):
        return None, "invalid_characters"
    if s.startswith("2340"):  # "+234 (0) 803 ..." written with the trunk 0
        s = "234" + s[4:]
    if s.startswith("234") and len(s) in (11, 13):
        return s[3:], None
    if s.startswith("0") and len(s) in (9, 11):
        return s[1:], None
    if len(s) == 10 and s[0] in "789":
        return s, None
    return None, "bad_length"


def _classify(nsn: str) -> Tuple[Optional[PhoneNumber], Optional[str]]:
    local, e164 = "0" + nsn, "+234" + nsn
    if len(nsn) == 10:
        lead = nsn[:3]
        if lead == "900":
            return None, "reserved"
        if lead in ("800", "700"):
            kind = "toll_free" if lead == "800" else "non_toll_free"
            block = _in_plan(nsn, kind)
            return PhoneNumber(e164, local, nsn, kind, "0" + lead, None, block["allottee"] if block else None,
                               block is not None, None), None
        prefix, subscriber = "0" + lead, nsn[3:]
        table = [b for b in _phone()["mobile"] if b["prefix"] == prefix]
        hit = next((b for b in table if b["range_start"] <= subscriber <= b["range_end"]), None)
        if hit and hit["status"] == "allocated":
            network = hit["operator"]
        else:
            plan = _in_plan(nsn, "mobile")
            if plan is None:
                return None, "unallocated" if table else "unknown_prefix"
            network = _short_network(plan["allottee"])
        return PhoneNumber(e164, local, nsn, "mobile", prefix, None, network, True, PORTING_NOTE), None
    if len(nsn) == 8:
        code = "0" + nsn[0] if nsn[0] in "129" else "0" + nsn[:2]
        area = _area_codes().get(code)
        if area is None:
            return None, "unknown_area_code"
        block = _in_plan(nsn, "fixed")
        return PhoneNumber(e164, local, nsn, "fixed", code, area["primary_centre"],
                           block["allottee"] if block else None, block is not None, None), None
    return None, "bad_length"


def phone_error(text: str) -> Optional[str]:
    """Why `text` is not a valid Nigerian phone number (one of PHONE_ERRORS), or None if it is valid."""
    nsn, err = _national(text)
    if err:
        return err
    return _classify(nsn)[1]


def parse_phone(text: str) -> Optional[PhoneNumber]:
    """Validate and describe a Nigerian phone number, or return None if it is not valid.

    >>> parse_phone("0803 123 4567").network
    'MTN'
    >>> parse_phone("01 269 1531").type, parse_phone("01 269 1531").area
    ('fixed', 'Lagos')
    """
    nsn, err = _national(text)
    if err:
        return None
    return _classify(nsn)[0]


def is_valid_phone(text: str, types: Optional[Sequence[str]] = None) -> bool:
    """True if `text` is a valid Nigerian number, optionally only of the given types
    (e.g. types=["mobile"] for numbers that can receive SMS)."""
    p = parse_phone(text)
    return p is not None and (types is None or p.type in types)


def normalize_phone(text: str) -> Optional[str]:
    """International (E.164) form, "+2348031234567", or None if the number is not valid."""
    p = parse_phone(text)
    return p.e164 if p else None


def to_local(text: str) -> Optional[str]:
    """Local form, "08031234567", or None if the number is not valid."""
    p = parse_phone(text)
    return p.local if p else None


def networks() -> List[str]:
    """Names of networks with allocated mobile prefixes."""
    return sorted({b["operator"] for b in _phone()["mobile"] if b["operator"]})


def prefixes(network: Optional[str] = None) -> List[str]:
    """Mobile prefixes ("0803", ...) allocated to a network (case-insensitive), or all prefixes."""
    want = network.lower() if network else None
    return sorted({b["prefix"] for b in _phone()["mobile"]
                   if want is None or (b["operator"] or "").lower() == want})


def area_codes() -> List[AreaCode]:
    """The NCC's 56 geographic (landline) area codes."""
    return [AreaCode(a["area_code"], a["primary_centre"], a["ncc_zone"], tuple(a["unverified_fields"]))
            for a in _phone()["area_codes"]]
