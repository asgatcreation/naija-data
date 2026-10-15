from django import forms

from django_naija import forms as ngforms

from .models import Customer


class CustomerForm(ngforms.StateLGAFormMixin, ngforms.NUBANFormMixin, forms.ModelForm):
    bank = ngforms.BankField(required=False)

    class Meta:
        model = Customer
        fields = ["name", "phone", "state", "lga", "plate", "bank", "account_number"]
