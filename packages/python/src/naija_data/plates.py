"""Vehicle number plates: format validation and parsing.

Sources: National Road Traffic Regulations 2012 (Official Gazette No. 101, S.I. 61), regulations
37-39 and Schedule 5. The Local Government code comes first on private, commercial and local
government plates (reg. 39(4)(f)); dealer plates are "D" + the state code + digits (figure 10).

FRSC sets the LGA plate codes (reg. 39(5)) but does not publish them, so this module checks the
format only and does not map a plate to its LGA. Government, armed forces, paramilitary and
diplomatic formats are not validated because the Regulations' sample images are not available.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import List, Optional, Sequence

from ._load import load
from .admin import _states
from .models import Plate, PlateCategory

PLATE_FORMATS = ("standard", "dealer")
PLATE_ERRORS = ("empty", "invalid_characters", "unknown_format", "unknown_state")

LGA_CODE_NOTE = ("The first three letters are the Local Government code. FRSC does not publish the list of "
                 "codes, so naija-data does not map them to LGAs yet.")

_STANDARD = re.compile(r"([A-Z]{3})(\d{3})([A-Z]{2})")
_DEALER = re.compile(r"D([A-Z]{2})(\d{3})([A-Z0-9])")


def _parse(text: str):
    s = re.sub(r"[\s\-.]", "", text.strip())
    if not s:
        return None, "empty"
    # Check for plain ASCII before upper-casing: languages upper-case some letters differently ("ß").
    if not re.fullmatch(r"[A-Za-z0-9]+", s):
        return None, "invalid_characters"
    s = s.upper()
    m = _STANDARD.fullmatch(s)
    if m:
        return Plate(s, f"{m[1]}-{m[2]}{m[3]}", "standard", m[1], m[2], m[3], None, LGA_CODE_NOTE), None
    m = _DEALER.fullmatch(s)
    if m:
        if m[1] not in {st.code for st in _states()}:
            return None, "unknown_state"
        return Plate(s, f"D{m[1]} {m[2]} {m[3]}", "dealer", "D" + m[1], m[2], m[3], m[1], None), None
    return None, "unknown_format"


def plate_error(text: str) -> Optional[str]:
    """Why `text` is not a valid plate number (one of PLATE_ERRORS), or None if it is valid."""
    return _parse(text)[1]


def parse_plate(text: str) -> Optional[Plate]:
    """Validate and split a plate number, or return None.

    >>> parse_plate("kja 123 ab").display
    'KJA-123AB'
    >>> parse_plate("DKN 135 3").state_code
    'KN'
    """
    return _parse(text)[0]


def is_valid_plate(text: str, formats: Optional[Sequence[str]] = None) -> bool:
    """True if `text` is a valid plate number, optionally only of the given formats."""
    p = parse_plate(text)
    return p is not None and (formats is None or p.format in formats)


@lru_cache(maxsize=None)
def _categories():
    return tuple(PlateCategory(**c) for c in load("plates")["categories"])


def plate_categories() -> List[PlateCategory]:
    """Plate colours by category, as set by the National Road Traffic Regulations 2012."""
    return list(_categories())
