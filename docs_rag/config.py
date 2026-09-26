"""Single source of truth for paths, models, and tunables."""
import json
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


def _parse_json_object(env_var: str) -> dict:
    """Parse an env var as an arbitrary JSON object. No schema is enforced
    beyond "must be a JSON object" -- this is the escape hatch for any
    provider-specific param litellm accepts (temperature, azure_deployment,
    aws_region_name, vertex_project, extra_headers, or even a full "model"
    override) without this project needing to know about it in advance.
    """
    raw = os.getenv(env_var)
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"{env_var} must be valid JSON: {e}") from e
    if not isinstance(parsed, dict):
        raise ValueError(f"{env_var} must be a JSON object (e.g. {{\"key\": \"value\"}}), got {type(parsed).__name__}")
    return parsed


# Arbitrary extra params forwarded as-is into litellm.completion() /
# litellm.embedding(). Any provider litellm supports works here, including
# ones that need more than a model-name string (Bedrock's aws_region_name,
# Azure's azure_deployment/api_version, Vertex's vertex_project, etc.) -- set
# them as a JSON object in .env, no code changes needed. A "model" key here
# overrides CHAT_MODEL/EMBED_MODEL entirely.
CHAT_PARAMS = _parse_json_object("CHAT_PARAMS")
EMBED_PARAMS = _parse_json_object("EMBED_PARAMS")


def effective_chat_model() -> str:
    """The model actually used for chat, accounting for a "model" key
    inside CHAT_PARAMS overriding CHAT_MODEL."""
    return CHAT_PARAMS.get("model", CHAT_MODEL)


def effective_embed_model() -> str:
    """The model actually used for embeddings, accounting for a "model"
    key inside EMBED_PARAMS overriding EMBED_MODEL."""
    return EMBED_PARAMS.get("model", EMBED_MODEL)

CACHE_SIMILARITY_THRESHOLD = float(os.getenv("CACHE_SIMILARITY_THRESHOLD", 0.95))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", 86400))

FLASK_PORT = int(os.getenv("FLASK_PORT", 5050))

SYSTEM_PROMPT = (
    "You are a documentation assistant. Answer the question using ONLY the "
    "provided context chunks. If the answer isn't in the context, say you "
    "don't know. Always cite which source file(s) you used, like [1]."
)
