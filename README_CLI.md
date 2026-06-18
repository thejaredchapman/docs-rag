# CLI -- `main.py`

A thin command-line wrapper around `query.ask()`. Ask a question, get an
answer with source citations, no server required. This is the fastest way
to sanity-check that ingestion and retrieval are working before you touch
the web UI or the MCP server.

## Prerequisites

- Python 3.10+ (the project was verified against 3.12)
- Dependencies installed: `pip install -r requirements.txt`
- A `.env` file with your provider's API key (see `.env.example`)
- An index already built: `python ingest.py` (see root [README.md](README.md))

If any of these are missing, the CLI fails fast with a clear message
rather than a stack trace (see [Troubleshooting](#troubleshooting) below).

## Running it

```bash
source venv/bin/activate
python main.py "How do I configure the chunk size?"
```

Output:

```
You can configure the chunk size via the CHUNK_SIZE constant in
config.py [1]. The default is 800 characters with a 150-character
overlap between chunks.

Sources:
  - sample.md
```

The answer text comes straight from your configured `CHAT_MODEL`. The
`Sources:` block lists every distinct file that contributed a retrieved
chunk, deduplicated and sorted.

## Flags

| Flag | Default | What it does |
|---|---|---|
| `question` (positional, required) | -- | The natural-language question to ask |
| `--top-k N` | `config.TOP_K` (10) | Override how many chunks are retrieved for this one query, without editing `.env` |
| `--no-cache` | off | Skip the embedding-similarity cache for this query (always calls the chat model fresh) |

Examples:

```bash
# Retrieve more context for a broad question
python main.py "Summarize everything in the docs" --top-k 25

# Force a fresh answer, bypassing the cache (useful when testing prompt changes)
python main.py "How do I configure the chunk size?" --no-cache

# Quote questions with special characters/spaces
python main.py "What's the difference between CHUNK_SIZE and TOP_K?"
```

## Scripting

`main.py` writes the answer and a `Sources:` block to stdout, plain text,
no flags for JSON output today. If you want to pipe results into another
tool, capture stdout and parse it, or call `query.ask()` directly from
Python instead of going through the CLI:

```python
import query

result = query.ask("How do I configure the chunk size?")
print(result["answer"])    # str
print(result["sources"])   # list[str]
print(result["cached"])    # bool
```

This is the same dict shape the Flask API returns (see
[README_WEB.md](README_WEB.md)) and the same shape the MCP `ask_docs` tool
returns (see [README_MCP.md](README_MCP.md)) -- all three interfaces are
thin wrappers around this one function.

## Exit codes

| Exit code | Meaning |
|---|---|
| `0` | Success -- answer printed to stdout |
| `1` | Index not found (`FileNotFoundError`) -- message printed to stderr |
| Uncaught traceback | Provider error (bad/missing API key, network failure, embed-model mismatch) -- see below |

## Troubleshooting

**`Error: No index found at .../index/faiss.index. Run python ingest.py first.`**
You haven't built an index yet, or `config.INDEX_DIR` points somewhere
empty. Run `python ingest.py` from the project root.

**`litellm.llms.openai.common_utils.OpenAIError: Missing credentials...`**
Your `.env` doesn't have the API key that matches `CHAT_MODEL` /
`EMBED_MODEL`. Check `.env.example` for which key each provider needs, and
confirm `.env` is in the project root (the CLI loads it via `config.py`,
which reads `./.env` relative to the project root, not your shell's cwd).

**`RuntimeError: Index was built with embed model 'X' but config.EMBED_MODEL is now 'Y'...`**
You changed `EMBED_MODEL` after building the index. Vectors from different
embedding models aren't comparable -- rerun `python ingest.py` to rebuild.

**Answer looks wrong / ignores obvious context**
Try `--top-k` with a higher number, or `--no-cache` to rule out a stale
cached answer from an earlier prompt/model change. If you changed
`CHAT_MODEL` recently, the cache (in-memory, per-process) is irrelevant
across separate `python main.py` invocations anyway -- each CLI run starts
a fresh process with an empty cache, so cache hits only happen within a
single long-running process (Flask, MCP server), not across CLI calls.

**Slow first call**
The first call in any process loads the FAISS index and metadata.json from
disk (`query._load_index()`), then embeds your question. Subsequent calls
in the same process reuse the loaded index. Since the CLI is a one-shot
process, every invocation pays this load cost -- this is expected and by
design (no daemon to keep running).
