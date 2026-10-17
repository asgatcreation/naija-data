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
                                 "+234 (0) 803 123 4567", "8031234567", "+234-803-123-4567", "00234 803 123 4567"])
def test_normalize_mobile(raw):
    assert ng.normalize_phone(raw) == "+2348031234567"
    assert ng.to_local(raw) == "08031234567"


@pytest.mark.parametrize("raw, error", [
    ("", "empty"), ("0803123456", "bad_length"), ("+1 803 123 4567", "not_nigerian"),
    ("hello", "invalid_characters"), ("0803 123 4567 ext 2", "invalid_characters"),
    ("0900 123 4567", "reserved"),  # NCC: reserved for vanity numbers
    ("0819 012 3456", "unallocated"),  # NCC: withdrawn block
    ("0910 123 4567", "unknown_prefix"),  # not in either NCC document
    ("044 123456", None), ("099 123456", None), ("040 123456", "unknown_area_code"), ("098 123456", None),
])
def test_phone_errors(raw, error):
    assert ng.phone_error(raw) == error
    assert ng.is_valid_phone(raw) is (error is None)


def test_phone_types_and_networks():
    m = ng.parse_phone("08031234567")
    assert (m.type, m.network, m.prefix) == ("mobile", "MTN", "0803")
    assert "ported" in m.note
    assert ng.parse_phone("08021234567").network == "Airtel"
    assert ng.parse_phone("08051234567").network == "Glo"
    assert ng.parse_phone("08091234567").network == "9mobile"
    lagos = ng.parse_phone("01 269 1531")  # example number from the NCC Numbering Regulations 2008
    assert (lagos.type, lagos.area, lagos.e164) == ("fixed", "Lagos", "+23412691531")
    kano = ng.parse_phone("064 310000")
    assert (kano.area, kano.network, kano.allocated) == ("Kano", "Intercellular Nig. Limited", True)
    assert ng.parse_phone("0800 123 4567").type == "toll_free"
    assert ng.parse_phone("0700 123 4567").type == "non_toll_free"
    assert ng.parse_phone("07026000000").network == "MTN"  # only the 2022 numbering plan lists this block
    assert ng.is_valid_phone("01 269 1531", types=["mobile"]) is False
    assert len(ng.area_codes()) == 56


@pytest.mark.parametrize("raw, display, fmt, state", [
    ("kja 123 ab", "KJA-123AB", "standard", None),
    ("KJA-123AB", "KJA-123AB", "standard", None),
    ("DKN 135 3", "DKN 135 3", "dealer", "KN"),  # sample from the Regulations, Schedule 5 figure 10
    ("dla5481", "DLA 548 1", "dealer", "LA"),
])
def test_plates(raw, display, fmt, state):
    p = ng.parse_plate(raw)
    assert (p.display, p.format, p.state_code) == (display, fmt, state)
    assert ng.is_valid_plate(raw)


@pytest.mark.parametrize("raw, error", [("", "empty"), ("AB-123-CD", "unknown_format"), ("DZZ 135 3", "unknown_state"),
                                        ("KJ@-123AB", "invalid_characters")])
def test_plate_errors(raw, error):
    assert ng.plate_error(raw) == error
    assert ng.parse_plate(raw) is None


def test_plate_categories_from_regulations():
    cats = {(c.category, c.vehicle): c for c in ng.plate_categories()}
    assert cats[("commercial", "vehicle")].lettering_colour == "red"
    assert cats[("government", "vehicle")].lettering_colour == "green"
    assert cats[("private", "motorcycle")].lettering_colour == "blue"


def test_cli(capsys):
    from naija_data.cli import main
    assert main(["lga", "lagos"]) == 0
    assert "Ikeja" in capsys.readouterr().out
    assert main(["nuban", "0000014579", "011"]) == 0
    assert main(["phone", "08031234567"]) == 0
    assert "MTN" in capsys.readouterr().out
    assert main(["phone", "0900 123 4567"]) == 1
    assert main(["plate", "DKN", "135", "3"]) == 0
    assert "Kano" in capsys.readouterr().out
    assert main(["constituencies", "Surulere", "--state", "Lagos"]) == 0
    assert "Surulere II" in capsys.readouterr().out


def test_constituency_totals():
    assert len(ng.senatorial_districts()) == 109
    assert len(ng.federal_constituencies()) == 360
    assert len(ng.state_constituencies()) == 990
    assert len(ng.federal_constituencies("Lagos")) == 24
    assert len(ng.state_constituencies("Lagos")) == 40
    assert ng.state_constituencies("FCT") == []  # the FCT has no House of Assembly
    assert [u.name for u in ng.senatorial_districts("FCT")] == ["FCT"]


def test_constituency_lookups():
    fc = ng.get_constituency("FC/001/AB")
    assert fc is ng.get_constituency("fc001")
    assert (fc.kind, fc.name) == ("federal_constituency", "Aba North/Aba South")
    assert [l.name for l in ng.constituency_lgas(fc)] == ["Aba North", "Aba South"]
    assert ng.get_constituency("FC999") is None
    with pytest.raises(ValueError):
        ng.constituency_wards("nope")
    with pytest.raises(ValueError):
        ng.constituencies("ward")


def test_lga_constituencies():
    # Surulere (Lagos) is split between two federal and two state constituencies.
    units = ng.lga_constituencies("Surulere", "Lagos")
    assert [(u.kind, u.name) for u in units] == [
        ("senatorial_district", "Lagos Central"), ("federal_constituency", "Surulere I"),
        ("federal_constituency", "Surulere II"), ("state_constituency", "Surulere I"),
        ("state_constituency", "Surulere II")]
    # INEC places Offa in Kwara South (OCHA COD-AB had Kwara Central).
    assert ng.get_lga("Offa").senatorial_district == "Kwara South"
    assert ng.lga_constituencies("Offa")[0].name == "Kwara South"


def test_ward_constituencies():
    w = ng.get_ward("01-01-01")
    assert (w.senatorial_district, w.federal_constituency, w.state_constituency) == ("SD003", "FC001", "SC001")
    assert all(x.state_constituency is None for x in ng.wards("Abaji", "FCT"))
    sc = ng.get_constituency(w.state_constituency)
    assert w in ng.constituency_wards(sc)
    assert sum(len(ng.constituency_wards(u)) for u in ng.senatorial_districts()) == 8809
