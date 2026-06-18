# MCP Server -- `mcp_server.py`

A [FastMCP](https://github.com/jlowin/fastmcp) server that exposes the
same `query.ask()` pipeline as MCP tools, so AI coding agents -- Claude
Code, Claude Desktop, Cursor, GitHub Copilot, OpenAI Codex, or anything
else that speaks MCP over stdio -- can query your docs directly as part
of a conversation.

This server is also published so you don't need a local checkout at all:
PyPI package [`docs-rag-mcp`](https://pypi.org/project/docs-rag-mcp/) and
MCP registry entry `io.github.thejaredchapman/docs-rag`. Both ways of
running it (cloned repo vs. installed package) are covered below.

## Prerequisites

- Python 3.10+, dependencies installed, `.env` configured
- An index already built: `python ingest.py` (cloned repo) or
  `docs-rag-ingest` (installed package)
- An MCP-capable client (Claude Code, Claude Desktop, Cursor, GitHub
  Copilot, OpenAI Codex, or anything else that speaks MCP over stdio)

## Running it standalone (for testing)

From a cloned repo:
```bash
source venv/bin/activate
python mcp_server.py
```

From the published package, with no checkout at all:
```bash
uvx docs-rag-mcp
# or: pip install docs-rag-mcp && docs-rag-mcp
```

This starts the server on **stdio transport** and blocks, waiting for an
MCP client to speak the protocol over stdin/stdout. There's no terminal
output to "watch" -- it's not meant to be run interactively by a human.
To verify it starts without errors, Ctrl+C after a second; a clean start
with no traceback means it's working. For actual testing, connect a real
MCP client (below) or use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector):

```bash
npx @modelcontextprotocol/inspector python mcp_server.py
```

## Connecting a client

Two ways to wire this up: point at a cloned checkout, or use the
published `docs-rag-mcp` package via `uvx` (no checkout needed). Either
way, set `cwd` to the project folder containing your `docs/`, `index/`,
and `.env` -- `config.py` resolves all paths relative to the working
directory the process runs in (see below).

### Claude Code

Add to your project's `.mcp.json` (or run `claude mcp add`):

```json
{
  "mcpServers": {
    "docs-rag": {
      "command": "/absolute/path/to/venv/bin/python",
      "args": ["/absolute/path/to/mcp_server.py"],
      "cwd": "/absolute/path/to/your/project"
    }
  }
}
```

Or, using the published package instead of a checkout:

```json
{
  "mcpServers": {
    "docs-rag": {
      "command": "uvx",
      "args": ["docs-rag-mcp"],
      "cwd": "/absolute/path/to/your/project"
    }
  }
}
```

Use absolute paths for `command`/`args` -- they aren't resolved relative
to anything.

### Claude Desktop

Edit `claude_desktop_config.json` (Settings -> Developer -> Edit Config),
same shape as above. Restart Claude Desktop after editing; the tool
should appear in the hammer/tools menu as `docs-rag`.

### Cursor

Settings -> MCP -> Add new MCP server, same `command`/`args`/`cwd` shape
as above (Cursor's config file is typically `~/.cursor/mcp.json` or per
project `.cursor/mcp.json`).

### GitHub Copilot (VS Code / Copilot Chat)

VS Code uses a different top-level key (`servers`, not `mcpServers`) and
**does not support a `cwd` field** -- set `DOCS_DIR`/`INDEX_DIR` to
absolute paths in `env` instead. Add to workspace `.vscode/mcp.json`
(shareable via source control) or via the `MCP: Open User Configuration`
command for a user-level config:

```json
{
  "servers": {
    "docs-rag": {
      "type": "stdio",
      "command": "uvx",
      "args": ["docs-rag-mcp"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "DOCS_DIR": "/absolute/path/to/your/docs",
        "INDEX_DIR": "/absolute/path/to/your/index"
      }
    }
  }
}
```

VS Code disables newly added tools by default -- after saving, run
`MCP: List Servers` and enable `docs-rag`'s tools.

### GitHub Copilot CLI

The standalone terminal tool (distinct from VS Code) uses its own config
at `~/.copilot/mcp-config.json`, with `"type": "local"` instead of
`"stdio"`:

```json
{
  "mcpServers": {
    "docs-rag": {
      "type": "local",
      "command": "uvx",
      "args": ["docs-rag-mcp"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "DOCS_DIR": "/absolute/path/to/your/docs",
        "INDEX_DIR": "/absolute/path/to/your/index"
      },
      "tools": ["*"]
    }
  }
}
```

Or via the CLI helper: `copilot mcp add docs-rag -- uvx docs-rag-mcp`,
then set the env vars when prompted.

### OpenAI Codex (CLI / IDE extension)

Codex stores MCP config as TOML in `~/.codex/config.toml` (or
`.codex/config.toml` scoped to a trusted project), and -- unlike VS
Code/Copilot -- **does** support `cwd` directly:

```toml
[mcp_servers.docs-rag]
command = "uvx"
args = ["docs-rag-mcp"]
cwd = "/absolute/path/to/your/project"

[mcp_servers.docs-rag.env]
OPENAI_API_KEY = "sk-..."
```

Or via the CLI helper, from your project directory:
```bash
codex mcp add docs-rag --env OPENAI_API_KEY=sk-... -- uvx docs-rag-mcp
```
The CLI and the Codex IDE extension share this same config, so you only
need to set it up once.

### Why `cwd` matters here specifically

MCP clients spawn the server as a subprocess with their own default
working directory -- usually *not* your project's. `config.py` resolves
`DOCS_DIR`, `INDEX_DIR`, and `.env` relative to **the process's current
working directory** (`Path.cwd()` / `find_dotenv(usecwd=True)`), not to
where `mcp_server.py` (or the installed package) physically lives. This
is intentional: it's what makes the same `docs-rag-mcp` package work for
any user's own docs folder. But it means you must either:

1. Set `cwd` in the client config to your project folder (shown above) --
   confirmed supported by Claude Code, Claude Desktop, Cursor, and Codex;
   or
2. Set `DOCS_DIR` / `INDEX_DIR` to absolute paths via the `env` block
   instead of relying on the relative `./docs` / `./index` defaults --
   **required** for VS Code / Copilot Chat (no `cwd` field exists), and
   the safer default for GitHub Copilot CLI too, since its docs don't
   document `cwd` support.

If you'd rather not rely on a `.env` file at all, every MCP client config
format also supports an `env` block to inject variables directly:

```json
{
  "mcpServers": {
    "docs-rag": {
      "command": "uvx",
      "args": ["docs-rag-mcp"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "CHAT_MODEL": "gpt-4o",
        "DOCS_DIR": "/absolute/path/to/your/docs",
        "INDEX_DIR": "/absolute/path/to/your/index"
      }
    }
  }
}
```

### Providers needing more than a model name

If your provider needs more than a model string (Azure's deployment name,
Bedrock's region, Vertex's project, custom headers, etc.), set
`CHAT_PARAMS` / `EMBED_PARAMS` in the `env` block to a JSON object --
every key is forwarded as-is to litellm, and a `"model"` key inside it
overrides `CHAT_MODEL`/`EMBED_MODEL` entirely:

```json
{
  "mcpServers": {
    "docs-rag": {
      "command": "uvx",
      "args": ["docs-rag-mcp"],
      "env": {
        "CHAT_PARAMS": "{\"model\": \"azure/my-gpt4o-deployment\", \"api_version\": \"2024-10-01\", \"api_base\": \"https://my-resource.openai.azure.com\"}"
      }
    }
  }
}
```

See the root [README.md](README.md#providers-that-need-more-than-a-model-name-bedrock-azure-vertex-)
for more examples -- this is the same mechanism the CLI and web UI use.

## Tool reference

### `ask_docs(question: str, top_k: int | None = None) -> dict`

The main tool. Same retrieval + generation as the CLI and web UI.

Input:
```json
{ "question": "How do I configure the chunk size?", "top_k": 5 }
```

Output:
```json
{
  "answer": "You can configure it via CHUNK_SIZE in config.py [1]...",
  "sources": ["sample.md"],
  "cached": false
}
```

Omit `top_k` to use the server's configured `TOP_K` default (10).

### `list_sources() -> list[str]`

No arguments. Returns every distinct source file currently indexed:
```json
["another-doc.md", "sample.md"]
```
Useful for an agent to check what's available before asking a question
scoped to a specific file.

### `index_stats() -> dict`

No arguments. Returns index size and cache performance:
```json
{
  "total_chunks": 42,
  "total_sources": 3,
  "embed_model": "text-embedding-3-small",
  "chat_model": "gpt-4o",
  "cache": { "hits": 5, "misses": 12, "size": 12 }
}
```
Useful for an agent (or you) to sanity-check which provider is actually
active without reading `.env`.

## How this differs from the CLI and Web UI

Same `query.ask()` underneath, same answer/sources shape, but:

- **Long-lived process.** Unlike the CLI (one-shot per invocation), the
  MCP server stays running for the life of the client session, so the
  FAISS index loads once and the similarity cache persists across
  multiple questions in the same conversation -- repeated/similar
  questions from the agent get faster, cached answers.
- **No HTTP, no browser.** Communication is stdio JSON-RPC, framed by
  FastMCP -- there's no port to curl and no security-header story, because
  there's no network surface to a browser at all. The same "API key never
  leaves the server process" property still holds: the key lives in the
  server's environment, never in a tool's input or output.

## Troubleshooting

**Client shows the server as "failed to start" / red status**
Almost always a path problem. Confirm: (1) `command` points at the venv's
Python binary, not `python3` on `PATH`; (2) `args` is an absolute path to
`mcp_server.py`; (3) running that exact command manually in a terminal
doesn't error.

**Tool call returns an index-not-found error**
The index has to exist in whatever directory `config.INDEX_DIR` resolves
to for this process -- by default `<cwd>/index/`. If you set `cwd` in the
client config, run `python ingest.py` (or `docs-rag-ingest`) from that same
directory first. If you didn't set `cwd`, set `DOCS_DIR`/`INDEX_DIR` to
absolute paths in the `env` block instead so it doesn't matter what the
client's default working directory is.

**Tool call fails with a credentials error**
The client's subprocess didn't get your API key. Either confirm `.env`
sits in the directory you set as `cwd` (it's found via
`find_dotenv(usecwd=True)`, which searches upward from the process's
working directory), or pass the key via the client's `env` block as shown
above -- the latter is more robust since it doesn't depend on `cwd` at all.

**Answers seem stale after you changed `CHAT_MODEL`/`EMBED_MODEL`**
Restart the MCP server process (most clients restart it when you reload
their config, but check). `config.py` reads `.env` once at import time, and
the in-memory similarity cache from before the restart could otherwise
keep surfacing old answers if you only changed `CHAT_MODEL` (the cache key
is the question's embedding, not the model name, so changing only the chat
model without restarting could return a cached answer generated by the old
model). If you changed `EMBED_MODEL`, you must also rerun `python
ingest.py` -- see the root [README.md](README.md) gotcha.

## Publishing (for maintainers)

This server is registered with the official
[MCP registry](https://registry.modelcontextprotocol.io) via `server.json`
at the project root, distributed through PyPI as `docs-rag-mcp` (see
`pyproject.toml`). To publish a new version:

```bash
# 1. Bump the version in pyproject.toml AND server.json (must match)

# 2. Build and upload to PyPI
python -m build
twine upload dist/*

# 3. Publish the updated server.json to the MCP registry
mcp-publisher login github   # device-flow auth, one-time per machine
mcp-publisher publish
```

PyPI ownership is verified via the `<!-- mcp-name: ... -->` comment in
this repo's root [README.md](README.md) (PyPI uses it as the package
description). Registry namespace ownership (`io.github.thejaredchapman/*`)
is verified via GitHub OAuth during `mcp-publisher login`.
