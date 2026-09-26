"""Document loading + chunking: walk a docs folder, strip YAML frontmatter
or extract PDF text, then split into overlapping chunks.
"""
from pathlib import Path


def strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4 :].lstrip("\n")
    return text


def extract_pdf_text(path: Path) -> str:
    import pdfplumber

    with pdfplumber.open(path) as pdf:
        return "\n\n".join(page.extract_text() or "" for page in pdf.pages)


def load_documents(docs_dir: Path):
    """Yield (relative_path_str, text) for every .md/.markdown/.txt/.pdf file."""
    docs_dir = Path(docs_dir)
    if not docs_dir.exists():
        return
    for path in sorted(docs_dir.rglob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in (".md", ".markdown", ".txt"):
            text = strip_frontmatter(path.read_text(encoding="utf-8"))
        elif suffix == ".pdf":
            text = extract_pdf_text(path)
        else:
            continue
        if text.strip():
            yield str(path.relative_to(docs_dir)), text


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks of up to `chunk_size` chars."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    step = chunk_size - overlap
    while start < len(text):
        chunk = text[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        if start + chunk_size >= len(text):
            break
        start += step
    return chunks
