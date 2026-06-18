"""Thin wrapper around litellm so every provider -- OpenAI, Anthropic,
Ollama, or a LiteLLM proxy sitting in front of any of them -- is called the
exact same way. Swapping providers means changing CHAT_MODEL / EMBED_MODEL
(or pointing LITELLM_API_BASE at a proxy) in .env. No code changes.

For providers that need more than a model-name string, CHAT_PARAMS /
EMBED_PARAMS (arbitrary JSON objects in .env, parsed in config.py) are
merged into every call -- any key litellm accepts works, including a
"model" override. Precedence, lowest to highest: CHAT_MODEL/EMBED_MODEL +
LITELLM_API_BASE/KEY  <  CHAT_PARAMS/EMBED_PARAMS  <  kwargs passed to
chat()/embed() directly.
"""
import litellm
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

import config

litellm.drop_params = True  # ignore params a given provider doesn't support
litellm.suppress_debug_info = True

# Only retry on transient/network-ish failures, not on bad requests.
TRANSIENT_ERRORS = (
    litellm.RateLimitError,
    litellm.APIConnectionError,
    litellm.Timeout,
    litellm.ServiceUnavailableError,
    litellm.InternalServerError,
)


def _merged_kwargs(model: str, params: dict, overrides: dict) -> dict:
    kwargs = {"model": model}
    if config.LITELLM_API_BASE:
        kwargs["api_base"] = config.LITELLM_API_BASE
    if config.LITELLM_API_KEY:
        kwargs["api_key"] = config.LITELLM_API_KEY
    kwargs.update(params)  # CHAT_PARAMS/EMBED_PARAMS -- any object, any keys, may override "model"
    kwargs.update(overrides)  # explicit call-time kwargs win over everything
    return kwargs


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(TRANSIENT_ERRORS),
)
def chat(messages: list[dict], **kwargs) -> str:
    response = litellm.completion(
        messages=messages,
        **_merged_kwargs(config.CHAT_MODEL, config.CHAT_PARAMS, kwargs),
    )
    return response["choices"][0]["message"]["content"]


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(TRANSIENT_ERRORS),
)
def embed(texts: list[str], **kwargs) -> list[list[float]]:
    response = litellm.embedding(
        input=texts,
        **_merged_kwargs(config.EMBED_MODEL, config.EMBED_PARAMS, kwargs),
    )
    return [item["embedding"] for item in response["data"]]
