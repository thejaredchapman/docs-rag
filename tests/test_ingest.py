import json

import pytest

import config


def test_build_index_writes_faiss_index_and_metadata(built_index):
    assert config.FAISS_INDEX_PATH.exists()
    assert config.METADATA_PATH.exists()
    assert config.INDEX_CONFIG_PATH.exists()

    metadata = json.loads(config.METADATA_PATH.read_text())
    assert len(metadata) > 0
    assert metadata[0]["source_file"] == "sample.md"


def test_build_index_records_effective_embed_model(temp_index_dir, fake_embed, monkeypatch):
    monkeypatch.setattr(config, "EMBED_PARAMS", {"model": "bedrock/titan-embed"})
    _, docs_dir = temp_index_dir
    (docs_dir / "sample.md").write_text("# Sample\n\nSome content.")

    import ingest

    ingest.build_index()

    index_config = json.loads(config.INDEX_CONFIG_PATH.read_text())
    assert index_config["embed_model"] == "bedrock/titan-embed"


def test_build_index_exits_when_no_docs(temp_index_dir, fake_embed):
    import ingest

    with pytest.raises(SystemExit):
        ingest.build_index()
