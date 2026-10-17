import copy

import pytest

import validate


@pytest.fixture(scope="module")
def tables():
    return {name: validate.load_csv(name) for name in validate.CSV_FILES}


@pytest.fixture(scope="module")
def source_ids():
    return {s["id"] for s in validate.load_json(validate.DATA / "sources.json")}


def test_repository_data_is_valid():
    assert validate.validate() == []


def test_expected_totals(tables):
    assert len(tables["states"]) == 37
    assert len(tables["lgas"]) == 774
    assert len(tables["wards"]) == 8809
    assert len(tables["senatorial_districts"]) == 109
    assert len(tables["federal_constituencies"]) == 360
    assert len(tables["state_constituencies"]) == 990


# --- sources.json

def source(**over):
    s = {"id": "x", "name": "n", "publisher": "p", "url": "https://a", "retrieved": "2026-01-01", "licence": "CC0-1.0"}
    s.update(over)
    return s


def test_duplicate_source_id_is_rejected():
    assert any("duplicate id" in e for e in validate.check_sources([source(), source()]))


def test_whitespace_in_source_is_rejected():
    assert any("whitespace" in e for e in validate.check_sources([source(name="n ")]))


def test_future_retrieval_date_is_rejected():
    assert any("future" in e for e in validate.check_sources([source(retrieved="2999-01-01")]))


def test_unknown_licence_fails_schema():
    assert validate.check_schema("t", [source(licence="whatever")], "sources.schema.json")


# --- states, LGAs, wards

def test_ward_with_unknown_lga_is_rejected(tables):
    wards = copy.deepcopy(tables["wards"])
    wards[0]["lga_code"] = "NG099999"
    errors = validate.check_admin(tables["states"], tables["lgas"], wards)
    assert any("unknown LGA" in e for e in errors)


def test_lga_with_unknown_state_is_rejected(tables):
    lgas = copy.deepcopy(tables["lgas"])
    lgas[0]["state_code"] = "ZZ"
    errors = validate.check_admin(tables["states"], lgas, tables["wards"])
    assert any("unknown state" in e for e in errors)


def test_missing_lga_breaks_the_count(tables):
    errors = validate.check_admin(tables["states"], tables["lgas"][1:], tables["wards"])
    assert any("expected 774" in e for e in errors)


def test_duplicate_ward_code_is_rejected(tables):
    wards = copy.deepcopy(tables["wards"])
    wards[1]["code"] = wards[0]["code"]
    errors = validate.check_admin(tables["states"], tables["lgas"], wards)
    assert any("duplicate code" in e for e in errors)


def test_ward_in_wrong_state_is_rejected(tables):
    wards = copy.deepcopy(tables["wards"])
    wards[0]["state_code"] = "LA" if wards[0]["state_code"] != "LA" else "AB"
    errors = validate.check_admin(tables["states"], tables["lgas"], wards)
    assert any("differs from its LGA" in e for e in errors)


def test_stray_whitespace_is_rejected(tables, source_ids):
    rows = copy.deepcopy(tables["lgas"][:1])
    rows[0]["name"] = " Ikeja"
    assert any("stray whitespace" in e for e in validate.check_common("lgas", rows, source_ids))


def test_duplicate_alias_is_rejected(tables, source_ids):
    rows = copy.deepcopy(tables["lgas"][:1])
    rows[0]["aliases"] = "Foo|foo"
    assert any("duplicate aliases" in e for e in validate.check_common("lgas", rows, source_ids))


def test_alias_equal_to_name_is_rejected(tables, source_ids):
    rows = copy.deepcopy(tables["lgas"][:1])
    rows[0]["aliases"] = rows[0]["name"].upper()
    assert any("repeats the name" in e for e in validate.check_common("lgas", rows, source_ids))


def test_unknown_source_id_is_rejected(tables, source_ids):
    rows = copy.deepcopy(tables["states"][:1])
    rows[0]["sources"] = "made-up-source"
    assert any("unknown source id" in e for e in validate.check_common("states", rows, source_ids))


def test_bad_row_shape_fails_schema(tables):
    rows = copy.deepcopy(tables["lgas"][:1])
    rows[0]["code"] = "NG25"
    assert validate.check_rows("lgas", rows)


# --- banks

def test_merged_into_must_exist(tables):
    banks = copy.deepcopy(tables["banks"])
    diamond = next(b for b in banks if b["id"] == "diamond-bank")
    diamond["merged_into"] = "no-such-bank"
    assert any("does not exist" in e for e in validate.check_banks(banks))


def test_active_code_clash_is_rejected(tables):
    banks = copy.deepcopy(tables["banks"])
    gtb = next(b for b in banks if b["id"] == "gtbank")
    zenith = next(b for b in banks if b["id"] == "zenith-bank")
    zenith["cbn_code"] = gtb["cbn_code"]
    assert any("several active institutions" in e for e in validate.check_banks(banks))


def test_bank_code_length_must_fit_type(tables):
    banks = copy.deepcopy(tables["banks"])
    next(b for b in banks if b["id"] == "gtbank")["cbn_code"] = "12345"
    assert any("must have 3 digits" in e for e in validate.check_banks(banks))


def test_known_bank_codes(tables):
    banks = {b["id"]: b for b in tables["banks"]}
    assert banks["access-bank"]["cbn_code"] == "044"
    assert banks["gtbank"]["cbn_code"] == "058"
    assert banks["diamond-bank"]["status"] == "merged"
    assert banks["diamond-bank"]["merged_into"] == "access-bank"
    assert banks["heritage-bank"]["status"] == "licence_revoked"


# --- phone prefixes

def test_overlapping_phone_blocks_are_rejected(tables):
    rows = copy.deepcopy(tables["phone_prefixes"])
    block = next(r for r in rows if r["prefix"] == "0803")
    rows.append(dict(block, range_start="5000000"))
    assert any("overlap" in e for e in validate.check_phone(rows))


def test_operator_only_when_allocated(tables):
    rows = copy.deepcopy(tables["phone_prefixes"])
    next(r for r in rows if r["status"] == "withdrawn")["operator"] = "MTN"
    assert any("operator must be set" in e for e in validate.check_phone(rows))


def test_garbled_text_is_rejected(tables, source_ids):
    rows = copy.deepcopy(tables["lgas"][:1])
    rows[0]["headquarters"] = "Jamao?" + chr(0xC7) + "oare"  # real example from OCHA COD-AB
    assert any("garbled" in e for e in validate.check_common("lgas", rows, source_ids))
    rows[0]["headquarters"] = "Jama'are"
    assert not validate.check_common("lgas", rows, source_ids)


# --- electoral units

def electoral(tables, wards=None, lgas=None, **units):
    return validate.check_electoral(tables["states"], lgas or tables["lgas"], wards or tables["wards"],
                                    {n: units.get(n, tables[n]) for n in validate.ELECTORAL})


def test_ward_linked_to_another_states_constituency_is_rejected(tables):
    wards = copy.deepcopy(tables["wards"])
    other = next(u["code"] for u in tables["federal_constituencies"] if u["state_code"] != wards[0]["state_code"])
    wards[0]["federal_constituency"] = other
    assert any("is in another state" in e for e in electoral(tables, wards=wards))


def test_fct_ward_with_state_constituency_is_rejected(tables):
    wards = copy.deepcopy(tables["wards"])
    w = next(w for w in wards if w["state_code"] == "FC")
    w["state_constituency"] = "SC001"
    assert any("no House of Assembly" in e for e in electoral(tables, wards=wards))


def test_missing_constituency_link_is_rejected(tables):
    wards = copy.deepcopy(tables["wards"])
    wards[0]["state_constituency"] = ""
    assert any("state_constituency is empty" in e for e in electoral(tables, wards=wards))


def test_lga_senatorial_district_must_match_its_wards(tables):
    lgas = copy.deepcopy(tables["lgas"])
    lgas[0]["senatorial_district"] = "Somewhere Else"
    assert any("differs from its wards" in e for e in electoral(tables, lgas=lgas))


def test_unit_code_must_match_inec_number(tables):
    units = copy.deepcopy(tables["federal_constituencies"])
    units[0]["inec_code"] = "FC/002/AB"
    errors = electoral(tables, federal_constituencies=units)
    assert any("differs from INEC code" in e for e in errors)
