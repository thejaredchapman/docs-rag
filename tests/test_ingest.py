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


def test_build_index_exits_when_no_docs(temp_index_dir, fake_embed):
    import ingest

    with pytest.raises(SystemExit):
        ingest.build_index()
