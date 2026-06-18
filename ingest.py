"""Build (or rebuild) the FAISS index from everything in ./docs/.

Run: python ingest.py
"""
import json
import sys

import faiss
import numpy as np

import config
import llm
from chunking import chunk_text, load_documents


def build_index():
    config.INDEX_DIR.mkdir(parents=True, exist_ok=True)

    records = []
    chunks = []
    for source_file, text in load_documents(config.DOCS_DIR):
        for i, chunk in enumerate(chunk_text(text, config.CHUNK_SIZE, config.CHUNK_OVERLAP)):
            records.append({"text": chunk, "source_file": source_file, "chunk_index": i})
            chunks.append(chunk)

    if not chunks:
        print(f"No documents found in {config.DOCS_DIR}. Add .md/.pdf files and re-run.")
        sys.exit(1)

    num_sources = len({r["source_file"] for r in records})
    print(f"Embedding {len(chunks)} chunks from {num_sources} file(s) using {config.EMBED_MODEL}...")

    vectors = []
    for i in range(0, len(chunks), config.EMBED_BATCH_SIZE):
        batch = chunks[i : i + config.EMBED_BATCH_SIZE]
        vectors.extend(llm.embed(batch))
        print(f"  embedded {min(i + config.EMBED_BATCH_SIZE, len(chunks))}/{len(chunks)}")

    matrix = np.array(vectors, dtype="float32")
    faiss.normalize_L2(matrix)

    dim = matrix.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(matrix)

    faiss.write_index(index, str(config.FAISS_INDEX_PATH))
    config.METADATA_PATH.write_text(json.dumps(records, indent=2))
    config.INDEX_CONFIG_PATH.write_text(
        json.dumps(
            {
                "embed_model": config.EMBED_MODEL,
                "dim": dim,
                "chunk_size": config.CHUNK_SIZE,
                "chunk_overlap": config.CHUNK_OVERLAP,
            },
            indent=2,
        )
    )

    print(f"Wrote {index.ntotal} vectors (dim={dim}) to {config.FAISS_INDEX_PATH}")
    print(f"Wrote metadata to {config.METADATA_PATH}")


if __name__ == "__main__":
    build_index()
