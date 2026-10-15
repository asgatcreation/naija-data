from rest_framework import serializers

from django_naija import rest_framework as ngdrf

from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    phone = ngdrf.NigerianPhoneField(types=["mobile"])
    state = ngdrf.StateField()
    lga = ngdrf.LGAField()
    plate = ngdrf.PlateNumberField(required=False, allow_blank=True)
    bank = ngdrf.BankField(required=False, allow_blank=True)
    account_number = ngdrf.NUBANField(required=False, allow_blank=True)

    class Meta:
        model = Customer
        fields = ["id", "name", "phone", "state", "lga", "plate", "bank", "account_number"]
        validators = [ngdrf.LGAInStateValidator(), ngdrf.NUBANBankValidator()]
