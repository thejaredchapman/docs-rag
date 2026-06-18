# Docs RAG

<!-- mcp-name: io.github.thejaredchapman/docs-rag -->

Documentation-search RAG app: drop markdown/PDF files in `./docs/`, build a
local FAISS index, then ask natural-language questions with source
citations via three interfaces.

Provider-agnostic by design: chat and embeddings go through
[litellm](https://docs.litellm.ai/), so switching models is a one-line env
var change, not a code change. You can also point the app at a running
LiteLLM proxy to swap backend models server-side without redeploying.

## The three interfaces

| Interface | Entry point | Guide |
|---|---|---|
| **Web UI** (has a frontend) | `app.py` | [README_WEB.md](README_WEB.md) |
| **CLI** | `main.py` | [README_CLI.md](README_CLI.md) |
| **MCP server** | `mcp_server.py` | [README_MCP.md](README_MCP.md) |

All three sit on top of the same `query.ask()` function in `query.py` --
same index, same retrieval, same prompt, same answer. They're just
different front doors. Each linked guide is a self-contained, extensive
walkthrough: setup, every flag/endpoint/tool, example output, and
troubleshooting specific to that interface.

## Shared setup (do this once, before any interface)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: set CHAT_MODEL / EMBED_MODEL and the matching provider API key

# put some .md / .pdf files in ./docs/ (a sample.md is already there)
python ingest.py          # build the index -- required before any interface works
pytest tests/ -v          # optional: confirm everything works offline, no API key needed
```

Once `./index/` exists, jump to whichever interface guide you want.

## Installing via pip (CLI + MCP server only)

The CLI and MCP server are also published to PyPI as `docs-rag-mcp` and
listed on the [MCP registry](https://registry.modelcontextprotocol.io) as
`io.github.thejaredchapman/docs-rag`:

```bash
pip install docs-rag-mcp
# or, to run without installing:
uvx docs-rag-mcp

cd /path/to/your/project   # wherever your ./docs/ and .env live
docs-rag-ingest             # build the index (same as python ingest.py)
docs-rag "your question"    # CLI (same as python main.py)
docs-rag-mcp                # MCP server, stdio transport (same as python mcp_server.py)
```

Paths (`DOCS_DIR`, `INDEX_DIR`) and `.env` resolve relative to your current
working directory, not to where pip installed the package -- run these
commands from your project folder, or set `DOCS_DIR`/`INDEX_DIR` to
absolute paths. The **web UI is not part of this package** (it needs the
`templates/`/`static/` assets, which aren't published) -- clone this repo
for `app.py`. See [README_MCP.md](README_MCP.md) for connecting MCP clients
to the installed `docs-rag-mcp` command instead of a cloned checkout.

## Switching providers ("oscillating")

litellm resolves the backend from the model name prefix and reads the
matching key from the environment. Just edit `.env`:

| Provider | `CHAT_MODEL` | `EMBED_MODEL` | Key(s) needed |
|---|---|---|---|
| OpenAI | `gpt-4o` | `text-embedding-3-small` | `OPENAI_API_KEY` |
| Anthropic + OpenAI embeddings | `claude-sonnet-4-6` | `text-embedding-3-small` | `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` |
| Local / free (Ollama) | `ollama/llama3.1` | `ollama/nomic-embed-text` | none |

**Gotcha:** if you change `EMBED_MODEL`, rerun `python ingest.py`. Vectors
from different embedding models aren't comparable -- `query.py` checks the
embed model recorded at ingest time and refuses to query a stale index.

## Using the LiteLLM proxy

Instead of calling providers directly, you can run a
[LiteLLM proxy](https://docs.litellm.ai/docs/simple_proxy) that exposes one
stable OpenAI-compatible endpoint in front of any number of backend models:

```bash
pip install 'litellm[proxy]'
litellm --config litellm_proxy_config.example.yaml
```

Then in `.env`:

```
LITELLM_API_BASE=http://localhost:4000
LITELLM_API_KEY=sk-litellm-proxy-key
CHAT_MODEL=gpt-4o                  # must match a model_name in the proxy config
EMBED_MODEL=text-embedding-3-small
```

Now you can add, remove, or repoint backend models by editing the proxy's
`model_list` -- this app's code never changes. This applies identically to
all three interfaces, since they all go through `llm.py`.

## Architecture

```
INGESTION (offline, run when docs change)
  ./docs/*.md, *.pdf -> ingest.py -> ./index/faiss.index + metadata.json

QUERY (per question, shared by all three interfaces)
  question -> query.ask() -> embed -> FAISS top-K -> prompt -> chat model
                                                              -> {answer, sources}

app.py        Flask web UI + JSON API  -- see README_WEB.md
main.py       CLI wrapper              -- see README_CLI.md
mcp_server.py FastMCP server           -- see README_MCP.md
config.py     All tunables in one place
llm.py        litellm wrapper (chat + embed) with retry/backoff
cache.py      Embedding-similarity answer cache
```

## Key parameters (`config.py`)

| Parameter | Default | What it does |
|---|---|---|
| `CHUNK_SIZE` | 800 chars | Size of each text chunk |
| `CHUNK_OVERLAP` | 150 chars | Overlap between chunks |
| `TOP_K` | 10 | Chunks retrieved per question |
| `EMBED_BATCH_SIZE` | 100 | Chunks embedded per API call |
| `CACHE_SIMILARITY_THRESHOLD` | 0.95 | Cosine similarity to count as a cache hit |
| `CACHE_TTL_SECONDS` | 86400 | How long cached answers live |

## Security

- The provider API key lives only in `.env` (gitignored) and server memory.
  It's never sent to the browser, and error messages are scrubbed of
  anything that looks like a key before being returned to clients.
- Flask runs with `debug=False`. Every response gets `X-Frame-Options: DENY`
  and `X-Content-Type-Options: nosniff`.
- Markdown answers are rendered client-side with `marked.js` and sanitized
  with `DOMPurify` before being inserted into the DOM.

## Tests

`pytest tests/ -v` -- every embedding and chat call is mocked
(`tests/conftest.py`), so the suite runs fully offline with no API key.
