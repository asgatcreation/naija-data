"""Name helpers shared by the import scripts: comparison keys, title case, slugs."""

from __future__ import annotations

import re
import unicodedata

ROMAN = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV"}
_SPLIT = re.compile(r"([\s/\-()]+)")


def key(name: str) -> str:
    """Comparison key: letters and digits only, upper case, accents removed."""
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def tidy(name: str) -> str:
    """Normalise spacing, slashes and dashes without changing letters."""
    name = name.replace("’", "'").replace("‐", "-").replace("–", "-")
    name = re.sub(r"\s*/\s*", "/", name)
    name = re.sub(r"\s*-\s*", "-", name)
    return re.sub(r"\s+", " ", name).strip(" ,")


def _word(part: str, first: bool) -> str:
    core = part.strip("\"'.,:;")
    if not core:
        return part
    if not first and core.upper() in ROMAN:  # "Urban II", "Ward IV,"
        return part.upper()
    if any(c.isdigit() for c in core):  # INEC sub-codes such as N5a, SW3a, 2b
        return part.upper()
    if len(core) == 1 and not first:  # designators: Bogoro "A", B O I
        return part.upper()
    if re.fullmatch(r"(?:[A-Za-z]\.)+[A-Za-z]?", core):  # initials such as M.C.
        return part.upper()
    i = next(i for i, c in enumerate(part) if c.isalpha())
    return part[:i] + part[i].upper() + part[i + 1:].lower()


def title(name: str) -> str:
    """'ANIFOWOSHE/IKEJA' -> 'Anifowoshe/Ikeja'; 'ABAK URBAN II' -> 'Abak Urban II'."""
    out: list[str] = []
    for part in _SPLIT.split(tidy(name)):
        if not part or _SPLIT.fullmatch(part):
            out.append(part)
        else:
            out.append(_word(part, first=not any(p.strip() and not _SPLIT.fullmatch(p) for p in out)))
    return "".join(out)


def slugify(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    text = text.replace("'", "").replace('"', "")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


_NUMERAL_LIKE = re.compile(r"(?<![A-Za-z0-9])([1IiVvXx]*1[1IiVvXx]*)(?![A-Za-z0-9])")
_LEADING_ONE = re.compile(r"(?<![A-Za-z0-9])1(?=[A-Za-z]{2,})")


def repair_roman(name: str) -> str:
    """INEC's live list sometimes types the letter I as the digit 1.

    'URBAN 11' -> 'URBAN II', 'Oluponna 1ii' -> 'Oluponna III', '1tak' -> 'Itak'.
    Real numbers are untouched: 'Mile 12', 'C1', 'Ward 10'. Callers should only accept the
    result when another source (INEC 2015) confirms it.
    """
    name = _NUMERAL_LIKE.sub(lambda m: m.group(1).replace("1", "I").upper(), name)
    return _LEADING_ONE.sub("I", name)
