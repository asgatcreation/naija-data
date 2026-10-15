"""naija-data: accurate, sourced Nigerian reference data.

    >>> import naija_data as ng
    >>> ng.get_state("lagos").capital
    'Ikeja'
    >>> [l.name for l in ng.lgas("FCT")][:2]
    ['Abaji', 'Abuja Municipal']
    >>> ng.is_valid_nuban("0000014579", "011")
    True

Data: CC BY 4.0, Akanji Oluwaseun Gabriel, compiled from INEC, CBN, NCC, OCHA and other sources
(see meta()["sources"]). Code: MIT.
"""

from __future__ import annotations

from ._load import load as _load
from .admin import find_lgas, get_lga, get_state, get_ward, lgas, search, states, wards
from .banks import (BANK_TYPES, banks, banks_for_nuban, find_banks, get_bank, is_valid_nuban,
                    nuban_check_digit)
from .models import LGA, Bank, PhoneInfo, SearchResult, State, Ward
from .phone import lookup_phone, networks, normalize_phone, prefixes, to_local

__version__ = "0.1.0.dev0"

__all__ = [
    "BANK_TYPES", "LGA", "Bank", "PhoneInfo", "SearchResult", "State", "Ward",
    "banks", "banks_for_nuban", "find_banks", "find_lgas", "get_bank", "get_lga", "get_state", "get_ward",
    "is_valid_nuban", "lgas", "lookup_phone", "meta", "networks", "normalize_phone", "nuban_check_digit",
    "prefixes", "search", "states", "to_local", "wards",
]


def meta() -> dict:
    """Dataset version, row counts, licence, attribution and sources."""
    return _load("meta")
