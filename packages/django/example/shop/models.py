from django.db import models

from django_naija.fields import LGAField, NigerianPhoneField, NUBANField, PlateNumberField, StateField


class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = NigerianPhoneField(types=["mobile"])  # stored as "+2348031234567"
    state = StateField()  # stored as "LA"
    lga = LGAField()  # stored as "NG025011"
    plate = PlateNumberField(blank=True)  # stored as "KJA123AB"
    bank = models.CharField(max_length=60, blank=True)  # naija-data bank id, e.g. "gtbank"
    account_number = NUBANField(blank=True)  # stored as "0123456789"

    def __str__(self) -> str:
        return self.name
