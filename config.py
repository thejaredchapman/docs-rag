"""Single source of truth for paths, models, and tunables."""
import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

# Search upward from the current working directory for a .env file. This
# matters once this package is pip-installed: the module's own location
# (site-packages) is never where a user's docs/.env live, so paths must
# resolve relative to wherever the user runs the command/MCP client from --
# not relative to this file. MCP clients that support a "cwd" setting
# should point it at the user's project directory.
load_dotenv(find_dotenv(usecwd=True))
DOCS_DIR = Path(os.getenv("DOCS_DIR", Path.cwd() / "docs"))
INDEX_DIR = Path(os.getenv("INDEX_DIR", Path.cwd() / "index"))
FAISS_INDEX_PATH = INDEX_DIR / "faiss.index"
METADATA_PATH = INDEX_DIR / "metadata.json"
INDEX_CONFIG_PATH = INDEX_DIR / "index_config.json"

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 800))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 150))
TOP_K = int(os.getenv("TOP_K", 10))
EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", 100))

# Model selection. litellm resolves the right backend from the model name
# prefix (e.g. "gpt-4o", "claude-sonnet-4-6", "ollama/llama3.1") and reads
# the matching API key from the environment. Swap providers by changing
# these two values -- no code changes.
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

# If set, every litellm call is routed through a running LiteLLM proxy
# (see litellm_proxy_config.example.yaml) instead of calling providers
# directly. That lets you swap or add backend models server-side without
# redeploying this app.
LITELLM_API_BASE = os.getenv("LITELLM_API_BASE") or None
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY") or None

CACHE_SIMILARITY_THRESHOLD = float(os.getenv("CACHE_SIMILARITY_THRESHOLD", 0.95))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", 86400))

FLASK_PORT = int(os.getenv("FLASK_PORT", 5050))

SYSTEM_PROMPT = (
    "You are a documentation assistant. Answer the question using ONLY the "
    "provided context chunks. If the answer isn't in the context, say you "
    "don't know. Always cite which source file(s) you used, like [1]."
)
