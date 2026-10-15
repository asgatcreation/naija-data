import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from rest_framework.test import APIClient

from django_naija import forms as ngforms
from django_naija.choices import bank_choices, lga_choices, state_choices
from django_naija.validators import NUBANValidator, PhoneValidator, PlateValidator, validate_nuban_for_bank
from shop.forms import CustomerForm
from shop.models import Customer

VALID = {"name": "Ada", "phone": "0803 123 4567", "state": "LA", "lga": "NG025011", "plate": "kja 123 ab",
         "bank": "first-bank", "account_number": "000 001 4579"}  # CBN example: bank 011, serial 000001457


# ---- validators

@pytest.mark.parametrize("value, code", [("0900 123 4567", "reserved"), ("0910 123 4567", "unknown_prefix"),
                                          ("+1 202 555 0100", "not_nigerian"), ("01 269 1531", "wrong_type")])
def test_phone_validator_codes(value, code):
    with pytest.raises(ValidationError) as e:
        PhoneValidator(["mobile"])(value)
    assert e.value.code == code


def test_validators_accept_valid_values():
    PhoneValidator()("01 269 1531")
    PlateValidator()("DKN 135 3")
    NUBANValidator(bank="011")("0000014579")
    validate_nuban_for_bank("0000014579", "First Bank")


def test_nuban_validators_reject():
    with pytest.raises(ValidationError) as e:
        NUBANValidator()("12345")
    assert e.value.code == "format"
    with pytest.raises(ValidationError) as e:
        validate_nuban_for_bank("0000014578", "011")
    assert e.value.code == "check_digit"
    with pytest.raises(ValidationError) as e:
        validate_nuban_for_bank("0000014579", "Atlantis Bank")
    assert e.value.code == "unknown_bank"


def test_validators_are_deconstructible():
    path, args, kwargs = PhoneValidator(["mobile"]).deconstruct()
    assert path == "django_naija.validators.PhoneValidator"
    assert (args, kwargs) == ((["mobile"],), {})
    assert PhoneValidator(["mobile"]) == PhoneValidator(("mobile",))


# ---- choices

def test_choices():
    assert len(state_choices()) == 37
    assert ("LA", "Lagos") in state_choices()
    assert len(lga_choices("LA")) == 20
    assert sum(len(group) for _, group in lga_choices()) == 774
    assert ("gtbank", "GTBank") in bank_choices(with_cbn_code_only=True)


# ---- forms

def test_form_cleans_and_normalises():
    form = CustomerForm(VALID)
    assert form.is_valid(), form.errors
    assert form.cleaned_data["phone"] == "+2348031234567"
    assert form.cleaned_data["plate"] == "KJA-123AB"
    assert form.cleaned_data["account_number"] == "0000014579"


def test_form_limits_lgas_to_state():
    form = CustomerForm({**VALID, "lga": "NG031033"})  # Surulere, Oyo: not in Lagos
    assert not form.is_valid()
    assert "lga" in form.errors
    assert len(form.fields["lga"].choices) == 20


def test_form_checks_account_against_bank():
    form = CustomerForm({**VALID, "account_number": "0000014578"})
    assert not form.is_valid()
    assert "not valid for the selected bank" in form.errors["account_number"][0]


def test_form_error_messages_are_clear():
    form = CustomerForm({**VALID, "phone": "0900 123 4567"})
    assert not form.is_valid()
    assert form.errors["phone"] == ["This number range is reserved and not in service."]


def test_standalone_form_fields():
    assert ngforms.NigerianPhoneField().clean("+234 (0) 803 123 4567") == "+2348031234567"
    assert ngforms.PlateNumberField(formats=["dealer"]).clean("dla5481") == "DLA 548 1"
    with pytest.raises(ValidationError):
        ngforms.PlateNumberField(formats=["dealer"]).clean("KJA-123AB")


# ---- models (database)

@pytest.mark.django_db
def test_model_stores_canonical_values():
    c = Customer(name="Ada", phone="0803 123 4567", state="LA", lga="NG025011", plate="kja 123 ab",
                 account_number="000 001 4579")
    c.full_clean()
    c.save()
    row = Customer.objects.values("phone", "plate", "account_number").get(pk=c.pk)
    assert row == {"phone": "+2348031234567", "plate": "KJA123AB", "account_number": "0000014579"}
    assert Customer.objects.filter(phone="08031234567").exists()  # lookups are normalised too


@pytest.mark.django_db
def test_model_full_clean_rejects_bad_values():
    c = Customer(name="Bad", phone="01 269 1531", state="ZZ", lga="NG999999")
    with pytest.raises(ValidationError) as e:
        c.full_clean()
    assert set(e.value.message_dict) >= {"phone", "state", "lga"}


@pytest.mark.django_db
def test_migrations_are_up_to_date():
    call_command("makemigrations", "shop", "--check", "--dry-run")


# ---- views and DRF

@pytest.mark.django_db
def test_dependent_lga_endpoint(client):
    data = client.get("/lgas/", {"state": "Lagos"}).json()
    assert data["state"] == "LA" and len(data["lgas"]) == 20
    assert client.get("/lgas/", {"state": "Atlantis"}).status_code == 404


@pytest.mark.django_db
def test_signup_view(client):
    assert client.post("/signup/", VALID).status_code == 201
    assert Customer.objects.get().phone == "+2348031234567"


@pytest.mark.django_db
def test_drf_accepts_names_and_normalises():
    api = APIClient()
    payload = {"name": "Ada", "phone": "+234 803 123 4567", "state": "Lagos", "lga": "24-11", "plate": "kja123ab",
               "bank": "First Bank", "account_number": "0000014579"}
    r = api.post("/api/customers/", payload, format="json")
    assert r.status_code == 201, r.json()
    body = r.json()
    assert (body["phone"], body["state"], body["lga"], body["bank"]) == ("+2348031234567", "LA", "NG025011", "first-bank")


@pytest.mark.django_db
def test_drf_errors_point_at_the_right_field():
    api = APIClient()
    bad_account = {"name": "Ada", "phone": "08031234567", "state": "LA", "lga": "NG025011", "bank": "011",
                   "account_number": "0000014578"}
    r = api.post("/api/customers/", bad_account, format="json")
    assert r.status_code == 400 and "account_number" in r.json()
    wrong_state = {**bad_account, "account_number": "0000014579", "lga": "NG031033"}
    r = api.post("/api/customers/", wrong_state, format="json")
    assert r.status_code == 400 and "lga" in r.json()
    r = api.post("/api/customers/", {**wrong_state, "lga": "NG025011", "phone": "0900 123 4567"}, format="json")
    assert r.json()["phone"] == ["This number range is reserved and not in service."]
