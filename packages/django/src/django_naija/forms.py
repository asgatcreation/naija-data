"""Form fields and mixins.

    from django_naija import forms as ngforms

    class SignupForm(ngforms.StateLGAFormMixin, ngforms.NUBANFormMixin, forms.Form):
        phone = ngforms.NigerianPhoneField(types=["mobile"])
        state = ngforms.StateField()
        lga = ngforms.LGAField()
        bank = ngforms.BankField()
        account_number = ngforms.NUBANField()
"""

from __future__ import annotations

from typing import Optional, Sequence

import naija_data as ng
from django import forms
from django.core.exceptions import ValidationError

from . import choices
from .validators import (NUBANValidator, PhoneValidator, PlateValidator, clean_nuban, validate_lga_in_state,
                         validate_nuban_for_bank)


class NigerianPhoneField(forms.CharField):
    """Cleans to E.164, e.g. "+2348031234567". `types` restricts accepted number types."""

    def __init__(self, *, types: Optional[Sequence[str]] = None, **kwargs):
        kwargs.setdefault("max_length", 32)
        super().__init__(**kwargs)
        self.validators.append(PhoneValidator(types))
        self.widget.attrs.setdefault("inputmode", "tel")
        self.widget.attrs.setdefault("autocomplete", "tel")

    def clean(self, value):
        value = super().clean(value)
        return ng.normalize_phone(value) if value else value


class NUBANField(forms.CharField):
    """A 10-digit account number; cleans to the digits only."""

    def __init__(self, *, bank: Optional[str] = None, **kwargs):
        kwargs.setdefault("max_length", 13)
        super().__init__(**kwargs)
        self.validators.append(NUBANValidator(bank))
        self.widget.attrs.setdefault("inputmode", "numeric")

    def clean(self, value):
        value = super().clean(value)
        return clean_nuban(value) if value else value


class PlateNumberField(forms.CharField):
    """A vehicle plate number; cleans to the display form, e.g. "KJA-123AB"."""

    def __init__(self, *, formats: Optional[Sequence[str]] = None, **kwargs):
        kwargs.setdefault("max_length", 16)
        super().__init__(**kwargs)
        self.validators.append(PlateValidator(formats))

    def clean(self, value):
        value = super().clean(value)
        return ng.parse_plate(value).display if value else value


class StateField(forms.ChoiceField):
    """Choose a state; the value is its ISO 3166-2 code ("LA")."""

    def __init__(self, **kwargs):
        kwargs.setdefault("choices", choices.state_choices)
        super().__init__(**kwargs)


class LGAField(forms.ChoiceField):
    """Choose an LGA; the value is its P-code ("NG025011"). Use with StateLGAFormMixin to limit the
    choices to the selected state."""

    def __init__(self, *, state: Optional[str] = None, **kwargs):
        kwargs.setdefault("choices", (lambda: choices.lga_choices(state)) if state else choices.lga_choices)
        super().__init__(**kwargs)


class BankField(forms.ChoiceField):
    """Choose a bank; the value is its naija-data id ("gtbank")."""

    def __init__(self, *, types: Optional[Sequence[str]] = None, with_cbn_code_only: bool = True, **kwargs):
        kwargs.setdefault("choices", lambda: choices.bank_choices(types, with_cbn_code_only))
        super().__init__(**kwargs)


class StateLGAFormMixin:
    """Limits the LGA field's choices to the submitted (or initial) state and checks that the LGA
    belongs to it. Set `state_field` / `lga_field` if your fields have other names."""

    state_field = "state"
    lga_field = "lga"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        state = None
        if self.is_bound:
            state = self.data.get(self.add_prefix(self.state_field))
        state = state or self.initial.get(self.state_field) or self.fields[self.state_field].initial
        if state and ng.get_state(str(state)):
            self.fields[self.lga_field].choices = choices.lga_choices(state)

    def clean(self):
        data = super().clean()
        state, lga = data.get(self.state_field), data.get(self.lga_field)
        if state and lga:
            try:
                validate_lga_in_state(lga, state)
            except ValidationError as e:
                self.add_error(self.lga_field, e)
        return data


class NUBANFormMixin:
    """Checks that the account number is valid for the selected bank (CBN check digit).
    Set `nuban_field` / `bank_field` if your fields have other names."""

    nuban_field = "account_number"
    bank_field = "bank"

    def clean(self):
        data = super().clean()
        account, bank = data.get(self.nuban_field), data.get(self.bank_field)
        if account and bank:
            try:
                validate_nuban_for_bank(account, bank)
            except ValidationError as e:
                self.add_error(self.nuban_field if e.code == "check_digit" else self.bank_field, e)
        return data
