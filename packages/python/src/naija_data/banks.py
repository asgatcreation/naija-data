"""Banks and other CBN-licensed institutions, and NUBAN account-number validation."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import List, Optional, Tuple, Union

from ._load import load
from ._text import norm, score
from .models import Bank

BankLike = Union[str, Bank]

BANK_TYPES = ("commercial", "merchant", "non_interest", "payment_service_bank", "mobile_money_operator",
              "microfinance", "mortgage", "development_finance")

# CBN Revised Standards on NUBAN: weights for the 6-digit institution code + 9-digit serial.
_WEIGHTS = (3, 7, 3, 3, 7, 3, 3, 7, 3, 3, 7, 3, 3, 7, 3)


@lru_cache(maxsize=None)
def _banks() -> Tuple[Bank, ...]:
    return tuple(Bank(**{**r, "aliases": tuple(r["aliases"]), "unverified_fields": tuple(r["unverified_fields"]),
                         "sources": tuple(r["sources"])}) for r in load("banks"))


def banks(type: Optional[str] = None, active_only: bool = True) -> List[Bank]:
    """Licensed institutions, optionally of one type (see BANK_TYPES). Inactive ones (merged,
    licence revoked) are included only with active_only=False."""
    if type is not None and type not in BANK_TYPES:
        raise ValueError(f"Unknown bank type: {type!r}. Use one of {', '.join(BANK_TYPES)}")
    return [b for b in _banks() if (type is None or b.type == type) and (b.active or not active_only)]


def get_bank(query: BankLike) -> Optional[Bank]:
    """Find an institution by id ("gtbank"), CBN code ("058", "50211"), NIP code ("000013"),
    name, short name or alias ("GTB", "Guaranty Trust Bank"). Active institutions win ties."""
    if isinstance(query, Bank):
        return query
    q = query.strip()
    if not q:
        return None
    if re.fullmatch(r"\d{3}|\d{5}", q):
        hits = [b for b in _banks() if b.cbn_code == q]
    elif re.fullmatch(r"\d{6}", q):
        hits = [b for b in _banks() if b.nip_code == q]
    else:
        key = norm(q)
        hits = [b for b in _banks() if b.id == q.lower()] or [
            b for b in _banks() if key in {norm(t) for t in (b.name, b.short_name or "", *b.aliases) if t}]
    hits.sort(key=lambda b: not b.active)
    return hits[0] if hits else None


def find_banks(query: str, limit: int = 10, active_only: bool = True, min_score: int = 600) -> List[Bank]:
    """Fuzzy search by name, short name or alias, best match first."""
    q = norm(query)
    if not q:
        return []
    scored = []
    for b in _banks():
        if active_only and not b.active:
            continue
        best = max(score(q, norm(t)) for t in (b.name, b.short_name or "", *b.aliases) if t)
        if best >= min_score:
            scored.append((best, b))
    scored.sort(key=lambda x: (-x[0], x[1].name, x[1].id))
    return [b for _, b in scored[:limit]]


# ---------------------------------------------------------------- NUBAN

def _institution_code(cbn_code: str) -> str:
    if re.fullmatch(r"\d{3}", cbn_code):
        return "000" + cbn_code  # deposit money banks
    if re.fullmatch(r"\d{5}", cbn_code):
        return "9" + cbn_code  # other financial institutions (microfinance, etc.)
    raise ValueError(f"A CBN bank code has 3 digits (banks) or 5 digits (other institutions): {cbn_code!r}")


def nuban_check_digit(bank_code: str, serial: str) -> int:
    """Check digit for a 9-digit account serial at the bank with this CBN code."""
    if not re.fullmatch(r"\d{9}", serial):
        raise ValueError(f"The NUBAN serial must be 9 digits: {serial!r}")
    digits = _institution_code(bank_code) + serial
    total = sum(int(d) * w for d, w in zip(digits, _WEIGHTS))
    return (10 - total % 10) % 10


def is_valid_nuban(account: str, bank: BankLike) -> bool:
    """True if the 10-digit account number has a correct check digit for this bank.

    `bank` is a CBN code ("058"), a Bank, or anything get_bank() understands. This only checks the
    arithmetic: it does not prove the account exists.
    """
    account = re.sub(r"[\s-]", "", account)
    if not re.fullmatch(r"\d{10}", account):
        return False
    code = bank if isinstance(bank, str) and re.fullmatch(r"\d{3}|\d{5}", bank.strip()) else None
    if code is None:
        found = get_bank(bank)
        if found is None or not found.cbn_code:
            raise ValueError(f"No CBN code known for bank {bank!r}")
        code = found.cbn_code
    return nuban_check_digit(code.strip(), account[:9]) == int(account[9])


def banks_for_nuban(account: str, active_only: bool = True) -> List[Bank]:
    """Institutions for which this 10-digit account number has a valid check digit.

    On average about 1 in 10 banks will match any number, so use this to narrow a bank picker,
    not to identify the bank for certain.
    """
    account = re.sub(r"[\s-]", "", account)
    if not re.fullmatch(r"\d{10}", account):
        return []
    check = int(account[9])
    return [b for b in _banks() if b.cbn_code and (b.active or not active_only)
            and nuban_check_digit(b.cbn_code, account[:9]) == check]
