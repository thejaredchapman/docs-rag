"""Shared pytest fixtures. All embedding/chat calls are mocked here --
tests never touch the network or need an API key.
"""
import numpy as np
import pytest

import config
import query
from cache import SimilarityCache


@pytest.fixture(autouse=True)
def reset_query_state():
    """query.py caches the loaded index/metadata at module level; reset
    between tests so each test sees its own temp index."""
    query._index = None
    query._metadata = None
    query._cache = SimilarityCache()
    yield


@pytest.fixture
def fake_embed(monkeypatch):
    """Deterministic fake embeddings: hash the text into a small vector."""
    import llm

    def _embed(texts):
        vectors = []
        for text in texts:
            seed = abs(hash(text)) % (2**32)
            rng = np.random.default_rng(seed)
            vectors.append(rng.random(8).tolist())
        return vectors

    monkeypatch.setattr(llm, "embed", _embed)
    return _embed


@pytest.fixture
def fake_chat(monkeypatch):
    import llm

    def _chat(messages, **kwargs):
        return "This is a fake answer. [1]"

    monkeypatch.setattr(llm, "chat", _chat)
    return _chat


@pytest.fixture
def temp_index_dir(tmp_path, monkeypatch):
    index_dir = tmp_path / "index"
    docs_dir = tmp_path / "docs"
    index_dir.mkdir()
    docs_dir.mkdir()
    monkeypatch.setattr(config, "INDEX_DIR", index_dir)
    monkeypatch.setattr(config, "FAISS_INDEX_PATH", index_dir / "faiss.index")
    monkeypatch.setattr(config, "METADATA_PATH", index_dir / "metadata.json")
    monkeypatch.setattr(config, "INDEX_CONFIG_PATH", index_dir / "index_config.json")
    monkeypatch.setattr(config, "DOCS_DIR", docs_dir)
    return index_dir, docs_dir


@pytest.fixture
def built_index(temp_index_dir, fake_embed):
    index_dir, docs_dir = temp_index_dir
    (docs_dir / "sample.md").write_text("# Sample\n\nThis is a sample document about widgets.")

    import ingest

    ingest.build_index()
    return index_dir, docs_dir
