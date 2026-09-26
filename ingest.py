"""Build the index: python ingest.py. Thin wrapper around docs_rag.ingest."""
from docs_rag.ingest import build_index

if __name__ == "__main__":
    build_index()
