import litellm
import pytest

import config
import llm


@pytest.fixture
def capture_completion(monkeypatch):
    calls = []

    def fake_completion(**kwargs):
        calls.append(kwargs)
        return {"choices": [{"message": {"content": "ok"}}]}

    monkeypatch.setattr(litellm, "completion", fake_completion)
    return calls


@pytest.fixture
def capture_embedding(monkeypatch):
    calls = []

    def fake_embedding(**kwargs):
        calls.append(kwargs)
        return {"data": [{"embedding": [0.1, 0.2]} for _ in kwargs["input"]]}

    monkeypatch.setattr(litellm, "embedding", fake_embedding)
    return calls


def test_chat_uses_configured_model_by_default(capture_completion, monkeypatch):
    monkeypatch.setattr(config, "CHAT_PARAMS", {})
    llm.chat([{"role": "user", "content": "hi"}])
    assert capture_completion[0]["model"] == config.CHAT_MODEL


def test_chat_merges_chat_params(capture_completion, monkeypatch):
    monkeypatch.setattr(config, "CHAT_PARAMS", {"temperature": 0.2, "extra_headers": {"X": "1"}})
    llm.chat([{"role": "user", "content": "hi"}])
    assert capture_completion[0]["temperature"] == 0.2
    assert capture_completion[0]["extra_headers"] == {"X": "1"}


def test_chat_params_model_overrides_chat_model(capture_completion, monkeypatch):
    monkeypatch.setattr(config, "CHAT_PARAMS", {"model": "bedrock/anthropic.claude-3"})
    llm.chat([{"role": "user", "content": "hi"}])
    assert capture_completion[0]["model"] == "bedrock/anthropic.claude-3"


def test_chat_call_time_kwargs_override_chat_params(capture_completion, monkeypatch):
    monkeypatch.setattr(config, "CHAT_PARAMS", {"temperature": 0.2})
    llm.chat([{"role": "user", "content": "hi"}], temperature=0.9)
    assert capture_completion[0]["temperature"] == 0.9


def test_embed_merges_embed_params(capture_embedding, monkeypatch):
    monkeypatch.setattr(config, "EMBED_PARAMS", {"dimensions": 256})
    llm.embed(["hello"])
    assert capture_embedding[0]["dimensions"] == 256
    assert capture_embedding[0]["model"] == config.EMBED_MODEL


def test_embed_params_model_overrides_embed_model(capture_embedding, monkeypatch):
    monkeypatch.setattr(config, "EMBED_PARAMS", {"model": "ollama/nomic-embed-text"})
    llm.embed(["hello"])
    assert capture_embedding[0]["model"] == "ollama/nomic-embed-text"
