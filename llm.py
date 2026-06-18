"""Thin wrapper around litellm so every provider -- OpenAI, Anthropic,
Ollama, or a LiteLLM proxy sitting in front of any of them -- is called the
exact same way. Swapping providers means changing CHAT_MODEL / EMBED_MODEL
(or pointing LITELLM_API_BASE at a proxy) in .env. No code changes.
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


def _common_kwargs() -> dict:
    kwargs = {}
    if config.LITELLM_API_BASE:
        kwargs["api_base"] = config.LITELLM_API_BASE
    if config.LITELLM_API_KEY:
        kwargs["api_key"] = config.LITELLM_API_KEY
    return kwargs


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(TRANSIENT_ERRORS),
)
def chat(messages: list[dict], **kwargs) -> str:
    response = litellm.completion(
        model=config.CHAT_MODEL,
        messages=messages,
        **_common_kwargs(),
        **kwargs,
    )
    return response["choices"][0]["message"]["content"]


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(TRANSIENT_ERRORS),
)
def embed(texts: list[str]) -> list[list[float]]:
    response = litellm.embedding(
        model=config.EMBED_MODEL,
        input=texts,
        **_common_kwargs(),
    )
    return [item["embedding"] for item in response["data"]]
