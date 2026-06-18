from chunking import chunk_text, strip_frontmatter


def test_chunk_text_short_text_returns_single_chunk():
    text = "short text"
    assert chunk_text(text, chunk_size=800, overlap=150) == [text]


def test_chunk_text_splits_with_overlap():
    text = "a" * 1000
    chunks = chunk_text(text, chunk_size=400, overlap=100)
    assert len(chunks) > 1
    assert all(len(c) <= 400 for c in chunks)


def test_chunk_text_empty_returns_empty_list():
    assert chunk_text("   ", chunk_size=800, overlap=150) == []


def test_strip_frontmatter_removes_yaml_block():
    text = "---\ntitle: Test\n---\n\nBody content"
    assert strip_frontmatter(text).strip() == "Body content"


def test_strip_frontmatter_leaves_text_without_frontmatter():
    text = "Just body content"
    assert strip_frontmatter(text) == text
