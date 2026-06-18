"""query.ask(question) -- embed the question, retrieve top-K chunks via
FAISS, build a prompt, call the chat model, return {answer, sources}.
"""
import json

import faiss
import numpy as np

import config
import llm
from cache import SimilarityCache

_cache = SimilarityCache()
_index = None
_metadata = None


def _load_index():
    global _index, _metadata
    if _index is None:
        if not config.FAISS_INDEX_PATH.exists():
            raise FileNotFoundError(
                f"No index found at {config.FAISS_INDEX_PATH}. Run `python ingest.py` first."
            )
        _index = faiss.read_index(str(config.FAISS_INDEX_PATH))
        _metadata = json.loads(config.METADATA_PATH.read_text())
    return _index, _metadata


def _check_embed_model():
    if config.INDEX_CONFIG_PATH.exists():
        index_config = json.loads(config.INDEX_CONFIG_PATH.read_text())
        built_with = index_config.get("embed_model")
        if built_with != config.EMBED_MODEL:
            raise RuntimeError(
                f"Index was built with embed model '{built_with}' but config.EMBED_MODEL "
                f"is now '{config.EMBED_MODEL}'. Vectors from different models aren't "
                "comparable -- rerun `python ingest.py`."
            )


def list_sources() -> list[str]:
    _, metadata = _load_index()
    return sorted({record["source_file"] for record in metadata})


def index_stats() -> dict:
    index, _ = _load_index()
    return {
        "total_chunks": index.ntotal,
        "total_sources": len(list_sources()),
        "embed_model": config.EMBED_MODEL,
        "chat_model": config.CHAT_MODEL,
    }


def cache_stats() -> dict:
    return _cache.stats()


def _build_prompt(question: str, chunks: list[dict]) -> list[dict]:
    context = "\n\n".join(
        f"[{i + 1}] (source: {c['source_file']})\n{c['text']}" for i, c in enumerate(chunks)
    )
    user_message = (
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the context above. Cite sources like [1], [2]."
    )
    return [
        {"role": "system", "content": config.SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]


def ask(question: str, top_k: int = None, use_cache: bool = True) -> dict:
    _check_embed_model()
    index, metadata = _load_index()
    top_k = top_k or config.TOP_K

    [raw_vector] = llm.embed([question])
    query_vector = np.array(raw_vector, dtype="float32").reshape(1, -1)
    faiss.normalize_L2(query_vector)
    query_vector = query_vector[0]

    if use_cache:
        cached = _cache.get(query_vector)
        if cached is not None:
            return {**cached, "cached": True}

    scores, indices = index.search(query_vector.reshape(1, -1), top_k)
    retrieved = [metadata[i] for i in indices[0] if i != -1 and i < len(metadata)]

    if not retrieved:
        result = {"answer": "I don't know -- no relevant documents were found.", "sources": []}
        return {**result, "cached": False}

    messages = _build_prompt(question, retrieved)
    answer = llm.chat(messages)
    sources = sorted({r["source_file"] for r in retrieved})
    result = {"answer": answer, "sources": sources}

    if use_cache:
        _cache.set(query_vector, result)

    return {**result, "cached": False}
