"""Nigerian mobile phone numbers: normalisation and network lookup (NCC allocation table)."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import List, Optional, Tuple

from ._load import load
from .models import PhoneInfo

_SEPARATORS = re.compile(r"[\s\-.()]")
_MOBILE = re.compile(r"[789][01]\d{8}")


@lru_cache(maxsize=None)
def _blocks() -> Tuple[dict, ...]:
    return tuple(load("phone"))


def _national(text: str) -> Optional[str]:
    """The 10-digit national number (without the leading 0), or None."""
    s = _SEPARATORS.sub("", text.strip())
    if s.startswith("+"):
        s = s[1:]
        if not s.startswith("234"):
            return None
    if s.startswith("2340"):  # "+234 (0) 803 ..." written with the trunk 0
        s = "234" + s[4:]
    if s.startswith("234") and len(s) == 13:
        s = s[3:]
    elif s.startswith("0") and len(s) == 11:
        s = s[1:]
    return s if _MOBILE.fullmatch(s) else None


def normalize_phone(text: str) -> Optional[str]:
    """Return the number in international (E.164) form, "+2348031234567", or None if it is not a
    well-formed Nigerian mobile number. Accepts "0803 123 4567", "+234 803-123-4567",
    "2348031234567", "+234 (0) 803 123 4567" and "8031234567"."""
    n = _national(text)
    return f"+234{n}" if n else None


def to_local(text: str) -> Optional[str]:
    """Return the number in local form, "08031234567", or None."""
    n = _national(text)
    return f"0{n}" if n else None


def lookup_phone(text: str) -> Optional[PhoneInfo]:
    """Normalise a mobile number and look up the network its number block was allocated to.

    Because of number portability the network is a guess, see PhoneInfo.note.
    """
    n = _national(text)
    if n is None:
        return None
    prefix, subscriber = "0" + n[:3], n[3:]
    block = next((b for b in _blocks() if b["prefix"] == prefix
                  and b["range_start"] <= subscriber <= b["range_end"]), None)
    return PhoneInfo(e164=f"+234{n}", local=f"0{n}", prefix=prefix,
                     network=block["operator"] if block else None, status=block["status"] if block else None)


def networks() -> List[str]:
    """Names of networks with allocated mobile prefixes."""
    return sorted({b["operator"] for b in _blocks() if b["operator"]})


def prefixes(network: Optional[str] = None) -> List[str]:
    """Mobile prefixes ("0803", ...) allocated to a network (case-insensitive), or all prefixes."""
    want = network.lower() if network else None
    return sorted({b["prefix"] for b in _blocks()
                   if want is None or (b["operator"] or "").lower() == want})
