---
title: Django and DRF
description: Model, form and serializer fields for Nigerian data with django-naija.
---

`django-naija` builds on the Python package. Python 3.10+, Django 5.2+.

```bash
pip install django-naija            # fields, forms, validators
pip install "django-naija[rest]"    # plus Django REST framework fields
```

## Models

```python
from django.db import models
from django_naija.fields import LGAField, NigerianPhoneField, NUBANField, PlateNumberField, StateField

class Customer(models.Model):
    phone = NigerianPhoneField(types=["mobile"])   # stored as "+2348031234567"
    state = StateField()                           # stored as "LA"
    lga = LGAField()                               # stored as "NG025011"
    plate = PlateNumberField(blank=True)           # stored as "KJA123AB"
    account_number = NUBANField(blank=True)        # stored as "0123456789"
```

Values are normalised before validation and saving, so `"0803 123 4567"`, `"+234 (0) 803 123 4567"` and
`"08031234567"` all store the same value, and lookups such as `Customer.objects.filter(phone="08031234567")`
match. State and LGA choices load lazily, so migrations stay one line per field.

## Forms

```python
from django import forms
from django_naija import forms as ngforms

class PayoutForm(ngforms.StateLGAFormMixin, ngforms.NUBANFormMixin, forms.Form):
    phone = ngforms.NigerianPhoneField(types=["mobile"])
    state = ngforms.StateField()
    lga = ngforms.LGAField()               # choices limited to the chosen state; must belong to it
    bank = ngforms.BankField()             # banks with a CBN code
    account_number = ngforms.NUBANField()  # checked against the chosen bank
```

For a dependent `<select>`, serve `django_naija.choices.lga_choices(state_code)` as JSON.

## Django REST framework

```python
from rest_framework import serializers
from django_naija import rest_framework as ngdrf

class PayoutSerializer(serializers.Serializer):
    phone = ngdrf.NigerianPhoneField(types=["mobile"])
    state = ngdrf.StateField()             # accepts "LA", "Lagos", "Abuja", "FCT"
    lga = ngdrf.LGAField()                 # accepts P-codes, INEC codes, unambiguous names
    bank = ngdrf.BankField()               # accepts "gtbank", "058", "GTB"
    account_number = ngdrf.NUBANField()

    class Meta:
        validators = [ngdrf.LGAInStateValidator(), ngdrf.NUBANBankValidator()]
```

## Error messages

Every failure has a translatable message and a code, for example `reserved`: "This number range is reserved
and not in service." or `check_digit`: "This account number is not valid for the selected bank."

The repository includes an example project (`packages/django/example`) using every field, with tests.
