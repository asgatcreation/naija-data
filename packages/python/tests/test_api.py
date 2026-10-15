"""Hand-written expectations: each value here was checked against the source documents."""

import pytest

import naija_data as ng


def test_counts():
    assert len(ng.states()) == 37
    assert len(ng.lgas()) == 774
    assert sum(len(ng.lgas(s)) for s in ng.states()) == 774
    assert ng.meta()["counts"]["wards"] == 8809


@pytest.mark.parametrize("query", ["LA", "la", "NG-LA", "24", "NG025", "lagos", "Lagos State", "LAGOS"])
def test_get_state_lagos(query):
    assert ng.get_state(query).name == "Lagos"


@pytest.mark.parametrize("query", ["FCT", "Abuja", "fct abuja", "Federal Capital Territory", "37", "FC"])
def test_get_state_fct(query):
    assert ng.get_state(query).code == "FC"


def test_spelling_variants():
    assert ng.get_state("Akwa-Ibom").code == "AK"
    assert ng.get_state("Nassarawa").code == "NA"
    assert ng.get_state("Atlantis") is None


def test_capitals_from_constitution():
    assert ng.get_state("Lagos").capital == "Ikeja"
    assert ng.get_state("Anambra").capital == "Awka"  # not COD-AB's "Akwa"
    assert ng.get_state("Osun").capital == "Osogbo"


def test_lgas_per_state():
    assert len(ng.lgas("Lagos")) == 20
    assert len(ng.lgas("Kano")) == 44
    assert [l.name for l in ng.lgas("FCT")] == ["Abaji", "Abuja Municipal", "Bwari", "Gwagwalada", "Kuje", "Kwali"]
    with pytest.raises(ValueError):
        ng.lgas("Atlantis")


def test_ambiguous_lga_names():
    assert ng.get_lga("Surulere") is None
    assert {l.state_code for l in ng.find_lgas("Surulere")} == {"LA", "OY"}
    assert ng.get_lga("Surulere", "Oyo").state_code == "OY"
    assert ng.get_lga("NG025011").name == "Ikeja"
    assert ng.get_lga("24-11").name == "Ikeja"


def test_lga_aliases():
    assert ng.get_lga("Yenegoa").name == "Yenagoa"
    assert ng.get_lga("AMAC").name == "Abuja Municipal"
    assert ng.get_lga("Abuja Municipal").headquarters == "Garki"


def test_wards():
    ikeja = ng.wards("Ikeja", "Lagos")
    assert len(ikeja) == 10
    assert ikeja[0].name == "Anifowoshe/Ikeja"
    assert len(ng.wards("Gwer East")) == 14  # INEC's duplicate removed
    assert ng.get_ward("03-12-11").name == "Itak"  # INEC live "1TAK" repaired


def test_search():
    assert ng.search("lagso")[0].name == "Lagos"
    top = ng.search("abuja")
    assert (top[0].kind, top[0].code) == ("state", "FC")
    assert ng.search("ikeja lga")[0].code == "NG025011"
    assert ng.search("") == []


def test_nuban_examples_from_cbn_standard():
    assert ng.nuban_check_digit("011", "000001457") == 9
    assert ng.is_valid_nuban("0000014579", "011")
    assert ng.nuban_check_digit("50547", "000021457") == 9
    assert ng.is_valid_nuban("0000214579", "50547")
    assert not ng.is_valid_nuban("0000014578", "011")
    assert not ng.is_valid_nuban("123", "011")


def test_nuban_bank_resolution():
    assert ng.is_valid_nuban("0000014579", "First Bank")  # First Bank's CBN code is 011
    assert any(b.id == "first-bank" for b in ng.banks_for_nuban("0000014579"))
    with pytest.raises(ValueError):
        ng.nuban_check_digit("1234", "000001457")


def test_banks():
    assert ng.get_bank("058").id == "gtbank"
    assert ng.get_bank("GTB").cbn_code == "058"
    assert ng.get_bank("044").name == "Access Bank Plc"
    diamond = ng.get_bank("063")
    assert diamond.status == "merged" and diamond.merged_into == "access-bank"
    assert ng.get_bank("heritage-bank").status == "licence_revoked"
    assert len(ng.banks("commercial")) == 28
    assert len(ng.banks("commercial", active_only=False)) == 30
    assert ng.get_bank("OPay").type == "microfinance"
    assert ng.get_bank("PalmPay").type == "mobile_money_operator"


@pytest.mark.parametrize("raw", ["08031234567", "0803 123 4567", "+2348031234567", "2348031234567",
                                 "+234 (0) 803 123 4567", "8031234567", "+234-803-123-4567"])
def test_normalize_phone(raw):
    assert ng.normalize_phone(raw) == "+2348031234567"
    assert ng.to_local(raw) == "08031234567"


@pytest.mark.parametrize("raw", ["", "0803123456", "+1 803 123 4567", "06031234567", "hello"])
def test_invalid_phone(raw):
    assert ng.normalize_phone(raw) is None


def test_phone_network():
    assert ng.lookup_phone("08031234567").network == "MTN"
    assert ng.lookup_phone("08021234567").network == "Airtel"
    assert ng.lookup_phone("08051234567").network == "Glo"
    assert ng.lookup_phone("08091234567").network == "9mobile"
    assert ng.lookup_phone("07021500000").status == "returned"
    assert "ported" in ng.lookup_phone("08031234567").note


def test_cli(capsys):
    from naija_data.cli import main
    assert main(["lga", "lagos"]) == 0
    assert "Ikeja" in capsys.readouterr().out
    assert main(["nuban", "0000014579", "011"]) == 0
    assert main(["phone", "08031234567"]) == 0
    assert "MTN" in capsys.readouterr().out
