---
title: Sample Document
---

# Welcome

This is a sample document for the Docs RAG pipeline. Drop your own
markdown or PDF files into this folder and run `python ingest.py` to
index them.

## Configuring the pipeline

All tunables -- chunk size, overlap, top-K, model names -- live in
`config.py`. Set `CHAT_MODEL` and `EMBED_MODEL` in `.env` to switch
providers; litellm picks the right backend from the model name prefix
(`gpt-4o`, `claude-sonnet-4-6`, `ollama/llama3.1`, ...).

## Rebuilding the index

If you change `EMBED_MODEL`, you must rerun `python ingest.py`. Vectors
from different embedding models are not comparable, and the app will
refuse to query a stale index.
