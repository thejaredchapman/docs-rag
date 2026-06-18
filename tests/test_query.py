import pytest

import config
import query


def test_ask_returns_answer_and_sources(built_index, fake_chat):
    result = query.ask("What is this about?", use_cache=False)
    assert "fake answer" in result["answer"].lower()
    assert result["sources"] == ["sample.md"]
    assert result["cached"] is False


def test_ask_raises_when_index_missing(temp_index_dir, fake_embed):
    with pytest.raises(FileNotFoundError):
        query.ask("anything")


def test_list_sources(built_index):
    assert query.list_sources() == ["sample.md"]


def test_index_stats(built_index):
    stats = query.index_stats()
    assert stats["total_chunks"] > 0
    assert stats["total_sources"] == 1


def test_cache_hit_on_repeated_question(built_index, fake_chat):
    first = query.ask("What is this about?", use_cache=True)
    assert first["cached"] is False
    second = query.ask("What is this about?", use_cache=True)
    assert second["cached"] is True


def test_index_stats_reflects_params_model_override(built_index, monkeypatch):
    monkeypatch.setattr(config, "CHAT_PARAMS", {"model": "azure/my-deployment"})
    monkeypatch.setattr(config, "EMBED_PARAMS", {"model": "bedrock/titan-embed"})
    stats = query.index_stats()
    assert stats["chat_model"] == "azure/my-deployment"
    assert stats["embed_model"] == "bedrock/titan-embed"


def test_ask_raises_when_embed_params_model_changed_after_ingest(built_index, fake_chat, monkeypatch):
    # built_index ingested with the default effective_embed_model(); now
    # simulate switching providers via EMBED_PARAMS without re-ingesting.
    monkeypatch.setattr(config, "EMBED_PARAMS", {"model": "a-different-embed-model"})
    with pytest.raises(RuntimeError, match="Vectors from different models"):
        query.ask("What is this about?", use_cache=False)
