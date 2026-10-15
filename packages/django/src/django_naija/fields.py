"""Model fields.

    from django_naija.fields import LGAField, NigerianPhoneField, NUBANField, PlateNumberField, StateField

    class Customer(models.Model):
        phone = NigerianPhoneField(types=["mobile"])   # stored as "+2348031234567"
        state = StateField()                           # stored as "LA"
        lga = LGAField()                               # stored as "NG025011"
        plate = PlateNumberField(blank=True)           # stored as "KJA123AB"
        account_number = NUBANField(blank=True)        # stored as "0123456789"
"""

from __future__ import annotations

from typing import Optional, Sequence

import naija_data as ng
from django.db import models

from . import choices, forms
from .validators import NUBANValidator, PhoneValidator, PlateValidator, clean_nuban, validate_lga, validate_state


class NigerianPhoneField(models.CharField):
    """Stores numbers in E.164 form ("+2348031234567"); accepts any common input format."""

    description = "Nigerian phone number"

    def __init__(self, *args, types: Optional[Sequence[str]] = None, **kwargs):
        self.types = tuple(types) if types else None
        kwargs.setdefault("max_length", 16)
        super().__init__(*args, **kwargs)
        self.validators.append(PhoneValidator(self.types))

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.types:
            kwargs["types"] = list(self.types)
        if kwargs.get("max_length") == 16:
            del kwargs["max_length"]
        return name, path, args, kwargs

    def to_python(self, value):
        value = super().to_python(value)
        return (ng.normalize_phone(value) or value) if value else value

    def get_prep_value(self, value):
        return self.to_python(super().get_prep_value(value))

    def formfield(self, **kwargs):
        # Input like "+234 (0) 803 123 4567" is longer than the stored form, so don't reuse max_length.
        return super().formfield(**{"form_class": forms.NigerianPhoneField, "types": self.types, "max_length": 32, **kwargs})


class NUBANField(models.CharField):
    """Stores a 10-digit account number without spaces."""

    description = "NUBAN account number"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 10)
        super().__init__(*args, **kwargs)
        self.validators.append(NUBANValidator())

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if kwargs.get("max_length") == 10:
            del kwargs["max_length"]
        return name, path, args, kwargs

    def to_python(self, value):
        value = super().to_python(value)
        return clean_nuban(value) if value else value

    def get_prep_value(self, value):
        return self.to_python(super().get_prep_value(value))

    def formfield(self, **kwargs):
        return super().formfield(**{"form_class": forms.NUBANField, "max_length": 13, **kwargs})


class PlateNumberField(models.CharField):
    """Stores plate numbers in compact form ("KJA123AB"); use parse_plate(value).display to show them."""

    description = "Vehicle plate number"

    def __init__(self, *args, formats: Optional[Sequence[str]] = None, **kwargs):
        self.formats = tuple(formats) if formats else None
        kwargs.setdefault("max_length", 10)
        super().__init__(*args, **kwargs)
        self.validators.append(PlateValidator(self.formats))

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.formats:
            kwargs["formats"] = list(self.formats)
        if kwargs.get("max_length") == 10:
            del kwargs["max_length"]
        return name, path, args, kwargs

    def to_python(self, value):
        value = super().to_python(value)
        parsed = ng.parse_plate(value) if value else None
        return parsed.compact if parsed else value

    def get_prep_value(self, value):
        return self.to_python(super().get_prep_value(value))

    def formfield(self, **kwargs):
        return super().formfield(**{"form_class": forms.PlateNumberField, "formats": self.formats, "max_length": 16,
                                    **kwargs})


class StateField(models.CharField):
    """Stores a state's ISO 3166-2 code ("LA"), with the 37 states as choices."""

    description = "Nigerian state"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 2)
        kwargs.setdefault("choices", choices.state_choices)
        super().__init__(*args, **kwargs)
        self.validators.append(validate_state)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs.pop("choices", None)
        if kwargs.get("max_length") == 2:
            del kwargs["max_length"]
        return name, path, args, kwargs


class LGAField(models.CharField):
    """Stores an LGA's P-code ("NG025011"), with all 774 LGAs (grouped by state) as choices."""

    description = "Nigerian local government area"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 8)
        kwargs.setdefault("choices", choices.lga_choices)
        super().__init__(*args, **kwargs)
        self.validators.append(validate_lga)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs.pop("choices", None)
        if kwargs.get("max_length") == 8:
            del kwargs["max_length"]
        return name, path, args, kwargs
