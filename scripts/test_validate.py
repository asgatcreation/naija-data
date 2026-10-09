import validate


def test_repository_data_is_valid():
    assert validate.validate() == []


def test_duplicate_source_id_is_rejected():
    s = {"id": "x", "name": "n", "publisher": "p", "url": "https://a", "retrieved": "2026-01-01", "licence": "CC0-1.0"}
    assert any("duplicate id" in e for e in validate.check_sources([s, dict(s)]))


def test_whitespace_is_rejected():
    s = {"id": "x", "name": "n ", "publisher": "p", "url": "https://a", "retrieved": "2026-01-01", "licence": "CC0-1.0"}
    assert any("whitespace" in e for e in validate.check_sources([s]))


def test_future_date_is_rejected():
    s = {"id": "x", "name": "n", "publisher": "p", "url": "https://a", "retrieved": "2999-01-01", "licence": "CC0-1.0"}
    assert any("future" in e for e in validate.check_sources([s]))


def test_unknown_licence_fails_schema():
    s = {"id": "x", "name": "n", "publisher": "p", "url": "https://a", "retrieved": "2026-01-01", "licence": "whatever"}
    assert validate.check_schema("t", [s], "sources.schema.json")
