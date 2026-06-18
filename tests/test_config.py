import pytest

from config import _parse_json_object


def test_parse_json_object_returns_empty_dict_when_unset(monkeypatch):
    monkeypatch.delenv("SOME_PARAMS", raising=False)
    assert _parse_json_object("SOME_PARAMS") == {}


def test_parse_json_object_parses_valid_object(monkeypatch):
    monkeypatch.setenv("SOME_PARAMS", '{"temperature": 0.2, "model": "bedrock/whatever"}')
    assert _parse_json_object("SOME_PARAMS") == {"temperature": 0.2, "model": "bedrock/whatever"}


def test_parse_json_object_rejects_invalid_json(monkeypatch):
    monkeypatch.setenv("SOME_PARAMS", "{not valid json")
    with pytest.raises(ValueError, match="must be valid JSON"):
        _parse_json_object("SOME_PARAMS")


def test_parse_json_object_rejects_non_object_json(monkeypatch):
    monkeypatch.setenv("SOME_PARAMS", '["a", "list", "not", "an", "object"]')
    with pytest.raises(ValueError, match="must be a JSON object"):
        _parse_json_object("SOME_PARAMS")


def test_parse_json_object_rejects_scalar_json(monkeypatch):
    monkeypatch.setenv("SOME_PARAMS", "42")
    with pytest.raises(ValueError, match="must be a JSON object"):
        _parse_json_object("SOME_PARAMS")
