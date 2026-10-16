# django-naija

Django and Django REST framework fields for Nigerian data, built on
[naija-data](https://github.com/asgatcreation/naija-data): phone numbers (strict NCC validation),
NUBAN account numbers (CBN check digit), vehicle plate numbers, states and LGAs.

Website and playground: https://naija-data.asgatcreation.workers.dev · REST API: https://naija-data-api.asgatcreation.workers.dev/v1

```bash
pip install django-naija            # Django fields, forms and validators
pip install "django-naija[rest]"    # plus Django REST framework fields
```

Requires Python 3.10+ and Django 5.2+.

## Models

```python
from django.db import models
from django_naija.fields import LGAField, NigerianPhoneField, NUBANField, PlateNumberField, StateField

class Customer(models.Model):
    phone = NigerianPhoneField(types=["mobile"])   # stored as "+2348031234567"
    state = StateField()                           # stored as "LA", 37 choices
    lga = LGAField()                               # stored as "NG025011", 774 choices grouped by state
    plate = PlateNumberField(blank=True)           # stored as "KJA123AB"
    account_number = NUBANField(blank=True)        # stored as "0123456789"
```

Choices are loaded lazily (Django's callable choices), so migrations stay small.

## Forms

```python
from django import forms
from django_naija import forms as ngforms

class PayoutForm(ngforms.StateLGAFormMixin, ngforms.NUBANFormMixin, forms.Form):
    phone = ngforms.NigerianPhoneField(types=["mobile"])
    state = ngforms.StateField()
    lga = ngforms.LGAField()            # limited to the chosen state; must belong to it
    bank = ngforms.BankField()          # banks with a CBN code
    account_number = ngforms.NUBANField()  # checked against the chosen bank
```

For a dependent state → LGA menu, `django_naija.choices.lga_choices("LA")` returns the LGAs of one
state; the example project serves it as JSON at `/lgas/?state=Lagos`.

## Django REST framework

```python
from rest_framework import serializers
from django_naija import rest_framework as ngdrf

class PayoutSerializer(serializers.Serializer):
    phone = ngdrf.NigerianPhoneField(types=["mobile"])
    state = ngdrf.StateField()          # also accepts "Lagos", "Abuja", "FCT"
    lga = ngdrf.LGAField()              # also accepts INEC codes and unambiguous names
    bank = ngdrf.BankField()            # also accepts "058" or "GTB"
    account_number = ngdrf.NUBANField()

    class Meta:
        validators = [ngdrf.LGAInStateValidator(), ngdrf.NUBANBankValidator()]
```

## Error messages

Every failure has a clear, translatable message and a machine-readable code, e.g.
`reserved` → "This number range is reserved and not in service.",
`check_digit` → "This account number is not valid for the selected bank.".
See `django_naija/messages.py`.

## Example project

`example/` is a small Django project using every field (model, form, DRF API, dependent LGA
endpoint). The tests in `tests/` run against it:

```bash
pip install -e "packages/python" -e "packages/django[test]"
cd packages/django && python -m pytest
```

Plate numbers: only the format is checked. FRSC does not publish its list of LGA plate codes, so
plates are not mapped to LGAs yet.

Licence: MIT. Data from naija-data: CC BY 4.0, Akanji Oluwaseun Gabriel.
