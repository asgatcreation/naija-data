"""Django REST framework serializer fields and validators.

    from django_naija import rest_framework as ngdrf

    class PayoutSerializer(serializers.Serializer):
        phone = ngdrf.NigerianPhoneField(types=["mobile"])
        state = ngdrf.StateField()
        lga = ngdrf.LGAField()
        bank = ngdrf.BankField()
        account_number = ngdrf.NUBANField()

        class Meta:
            validators = [ngdrf.NUBANBankValidator(), ngdrf.LGAInStateValidator()]
"""

from __future__ import annotations

from typing import Optional, Sequence

import naija_data as ng
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from . import choices
from .validators import (NUBANValidator, PhoneValidator, PlateValidator, clean_nuban, validate_lga_in_state,
                         validate_nuban_for_bank)


def _run(validator, value):
    try:
        validator(value)
    except DjangoValidationError as e:
        raise serializers.ValidationError(e.messages, code=e.code)


class NigerianPhoneField(serializers.CharField):
    """Accepts any common format; returns E.164 ("+2348031234567")."""

    def __init__(self, *, types: Optional[Sequence[str]] = None, **kwargs):
        self.phone_validator = PhoneValidator(types)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        _run(self.phone_validator, value)
        return ng.normalize_phone(value)


class NUBANField(serializers.CharField):
    """Returns the 10 digits of an account number."""

    def __init__(self, *, bank: Optional[str] = None, **kwargs):
        self.nuban_validator = NUBANValidator(bank)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        _run(self.nuban_validator, value)
        return clean_nuban(value)


class PlateNumberField(serializers.CharField):
    """Returns the plate's display form ("KJA-123AB")."""

    def __init__(self, *, formats: Optional[Sequence[str]] = None, **kwargs):
        self.plate_validator = PlateValidator(formats)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        _run(self.plate_validator, value)
        return ng.parse_plate(value).display


class StateField(serializers.ChoiceField):
    """A state's ISO 3166-2 code ("LA"). Also accepts names and aliases ("Lagos", "Abuja")."""

    def __init__(self, **kwargs):
        super().__init__(choices=choices.state_choices(), **kwargs)

    def to_internal_value(self, data):
        found = ng.get_state(str(data)) if data not in ("", None) else None
        return super().to_internal_value(found.code if found else data)


class LGAField(serializers.ChoiceField):
    """An LGA's P-code ("NG025011"). Also accepts INEC codes ("24-11") and unambiguous names."""

    def __init__(self, **kwargs):
        super().__init__(choices=[c for _, group in choices.lga_choices() for c in group], **kwargs)

    def to_internal_value(self, data):
        found = ng.get_lga(str(data)) if data not in ("", None) else None
        return super().to_internal_value(found.code if found else data)


class BankField(serializers.ChoiceField):
    """A bank's naija-data id ("gtbank"). Also accepts CBN codes ("058") and names ("GTB")."""

    def __init__(self, *, types: Optional[Sequence[str]] = None, with_cbn_code_only: bool = True, **kwargs):
        super().__init__(choices=choices.bank_choices(types, with_cbn_code_only), **kwargs)

    def to_internal_value(self, data):
        found = ng.get_bank(str(data)) if data not in ("", None) else None
        return super().to_internal_value(found.id if found else data)


class NUBANBankValidator:
    """Serializer-level validator: the account number must be valid for the chosen bank."""

    requires_context = False

    def __init__(self, nuban_field: str = "account_number", bank_field: str = "bank"):
        self.nuban_field, self.bank_field = nuban_field, bank_field

    def __call__(self, attrs):
        account, bank = attrs.get(self.nuban_field), attrs.get(self.bank_field)
        if account and bank:
            try:
                validate_nuban_for_bank(account, bank)
            except DjangoValidationError as e:
                field = self.nuban_field if e.code == "check_digit" else self.bank_field
                raise serializers.ValidationError({field: e.messages}, code=e.code)


class LGAInStateValidator:
    """Serializer-level validator: the LGA must be in the chosen state."""

    requires_context = False

    def __init__(self, state_field: str = "state", lga_field: str = "lga"):
        self.state_field, self.lga_field = state_field, lga_field

    def __call__(self, attrs):
        state, lga = attrs.get(self.state_field), attrs.get(self.lga_field)
        if state and lga:
            try:
                validate_lga_in_state(lga, state)
            except DjangoValidationError as e:
                raise serializers.ValidationError({self.lga_field: e.messages}, code=e.code)
