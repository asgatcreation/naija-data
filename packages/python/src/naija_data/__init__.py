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
from .admin import find_lgas, get_lga, get_state, get_ward, lgas, search, search_wards, states, wards
from .constituencies import (CONSTITUENCY_KINDS, constituencies, constituency_lgas, constituency_wards,
                             federal_constituencies, find_constituencies, get_constituency, lga_constituencies,
                             senatorial_districts, state_constituencies)
from .banks import (BANK_TYPES, banks, banks_for_nuban, find_banks, get_bank, is_valid_nuban,
                    nuban_check_digit)
from .models import LGA, AreaCode, Bank, Constituency, PhoneNumber, Plate, PlateCategory, SearchResult, State, Ward
from .phone import (PHONE_ERRORS, PHONE_TYPES, area_codes, is_valid_phone, networks, normalize_phone, parse_phone,
                    phone_error, prefixes, to_local)
from .plates import PLATE_ERRORS, PLATE_FORMATS, is_valid_plate, parse_plate, plate_categories, plate_error

__version__ = "1.0.0"

__all__ = [
    "BANK_TYPES", "CONSTITUENCY_KINDS", "PHONE_ERRORS", "PHONE_TYPES", "PLATE_ERRORS", "PLATE_FORMATS",
    "LGA", "AreaCode", "Bank", "Constituency", "PhoneNumber", "Plate", "PlateCategory", "SearchResult", "State", "Ward",
    "area_codes", "banks", "banks_for_nuban", "constituencies", "constituency_lgas", "constituency_wards",
    "federal_constituencies", "find_banks", "find_constituencies", "find_lgas", "get_bank", "get_constituency",
    "get_lga", "get_state", "get_ward", "is_valid_nuban", "is_valid_phone", "is_valid_plate", "lga_constituencies",
    "lgas", "meta", "networks", "normalize_phone", "nuban_check_digit", "parse_phone", "parse_plate", "phone_error",
    "plate_categories", "plate_error", "prefixes", "search", "search_wards", "senatorial_districts",
    "state_constituencies", "states", "to_local", "wards",
]


def meta() -> dict:
    """Dataset version, row counts, licence, attribution and sources."""
    return _load("meta")
