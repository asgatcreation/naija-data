import pytest

from names import key, repair_roman, slugify, title


@pytest.mark.parametrize("raw, expected", [
    ("ANIFOWOSHE/IKEJA", "Anifowoshe/Ikeja"),
    ("ABAK URBAN II", "Abak Urban II"),
    ("IFAKO - IJAYE", "Ifako-Ijaye"),
    ("YALMALTU/ DEBA", "Yalmaltu/Deba"),
    ('BOGORO "A"', 'Bogoro "A"'),
    ("JAMA'ARE \"B\"", "Jama'are \"B\""),
    ("WARD IV, N5A", "Ward IV, N5A"),
    ("AMUWO-ODOFIN HOUSING ESTATE, MILE 2", "Amuwo-Odofin Housing Estate, Mile 2"),
])
def test_title(raw, expected):
    assert title(raw) == expected


@pytest.mark.parametrize("raw, expected", [
    ("ABAK URBAN 11", "ABAK URBAN II"),
    ("EASTERN OBOLO V111", "EASTERN OBOLO VIII"),
    ("URBAN 1V", "URBAN IV"),
    ("1TAK", "ITAK"),
    ("Oluponna 1ii", "Oluponna III"),
])
def test_repair_roman_fixes_digit_one_typed_for_letter_i(raw, expected):
    assert repair_roman(raw) == expected


@pytest.mark.parametrize("raw", ["Mile 12", "C1", "Ward 10", "N2"])
def test_repair_roman_leaves_real_numbers_alone(raw):
    assert repair_roman(raw) == raw


def test_key_ignores_case_spacing_and_punctuation():
    assert key("Akwa-Ibom") == key("AKWA IBOM") == key("akwa ibom")


def test_slugify():
    assert slugify("Ajeromi/Ifelodun") == "ajeromi-ifelodun"
    assert slugify("Jama'are") == "jamaare"
