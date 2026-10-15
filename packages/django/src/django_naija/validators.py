"""Validators for model fields, form fields and serializers. All are deconstructible, so they can be
used in migrations."""

from __future__ import annotations

import re
from typing import Optional, Sequence

import naija_data as ng
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

from .messages import ADMIN_MESSAGES, NUBAN_MESSAGES, PHONE_MESSAGES, PLATE_MESSAGES


@deconstructible
class PhoneValidator:
    """A valid Nigerian phone number, optionally only of some types (e.g. ("mobile",))."""

    def __init__(self, types: Optional[Sequence[str]] = None):
        self.types = tuple(types) if types else None

    def __call__(self, value) -> None:
        error = ng.phone_error(str(value))
        if error:
            raise ValidationError(PHONE_MESSAGES[error], code=error)
        if self.types and ng.parse_phone(str(value)).type not in self.types:
            raise ValidationError(PHONE_MESSAGES["wrong_type"], code="wrong_type")

    def __eq__(self, other) -> bool:
        return isinstance(other, PhoneValidator) and self.types == other.types


@deconstructible
class PlateValidator:
    """A valid vehicle plate number, optionally only of some formats (e.g. ("standard",))."""

    def __init__(self, formats: Optional[Sequence[str]] = None):
        self.formats = tuple(formats) if formats else None

    def __call__(self, value) -> None:
        error = ng.plate_error(str(value))
        if error:
            raise ValidationError(PLATE_MESSAGES[error], code=error)
        if self.formats and ng.parse_plate(str(value)).format not in self.formats:
            raise ValidationError(PLATE_MESSAGES["wrong_format"], code="wrong_format")

    def __eq__(self, other) -> bool:
        return isinstance(other, PlateValidator) and self.formats == other.formats


def clean_nuban(value) -> str:
    """The 10 digits of an account number, without spaces or dashes."""
    return re.sub(r"[\s-]", "", str(value))


@deconstructible
class NUBANValidator:
    """A 10-digit NUBAN account number. With `bank` (CBN code, id or name) the CBN check digit is
    checked too; to check against a bank chosen in the same form, use NUBANFormMixin."""

    def __init__(self, bank: Optional[str] = None):
        self.bank = bank

    def __call__(self, value) -> None:
        if not re.fullmatch(r"\d{10}", clean_nuban(value)):
            raise ValidationError(NUBAN_MESSAGES["format"], code="format")
        if self.bank and not ng.is_valid_nuban(clean_nuban(value), self.bank):
            raise ValidationError(NUBAN_MESSAGES["check_digit"], code="check_digit")

    def __eq__(self, other) -> bool:
        return isinstance(other, NUBANValidator) and self.bank == other.bank


def validate_nuban_for_bank(account, bank) -> None:
    """Raise ValidationError unless `account` has a valid check digit for `bank`."""
    found = ng.get_bank(str(bank)) if bank else None
    if found is None or not found.cbn_code:
        raise ValidationError(NUBAN_MESSAGES["unknown_bank"], code="unknown_bank")
    NUBANValidator()(account)
    if not ng.is_valid_nuban(clean_nuban(account), found.cbn_code):
        raise ValidationError(NUBAN_MESSAGES["check_digit"], code="check_digit")


def validate_state(value) -> None:
    if ng.get_state(str(value)) is None:
        raise ValidationError(ADMIN_MESSAGES["unknown_state"], code="unknown_state")


def validate_lga(value) -> None:
    if ng.get_lga(str(value)) is None:
        raise ValidationError(ADMIN_MESSAGES["unknown_lga"], code="unknown_lga")


def validate_lga_in_state(lga, state) -> None:
    """Raise ValidationError unless the LGA (code or name) is in the state."""
    st = ng.get_state(str(state)) if state else None
    if st is None:
        raise ValidationError(ADMIN_MESSAGES["unknown_state"], code="unknown_state")
    found = ng.get_lga(str(lga), st)
    if found is None:
        raise ValidationError(ADMIN_MESSAGES["unknown_lga"], code="unknown_lga")
    if found.state_code != st.code:
        raise ValidationError(ADMIN_MESSAGES["lga_not_in_state"], code="lga_not_in_state")
