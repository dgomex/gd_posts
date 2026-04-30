"""LLM factory: build a LangChain chat model from an LLMConfig.

Adding a new provider is as simple as appending a branch here. Provider
imports are lazy so users only need to install the SDKs they actually use.
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from .config import LLMConfig


def make_llm(config: LLMConfig) -> BaseChatModel:
    """Instantiate a chat model for the given provider configuration.

    Supported providers:
        * ``google_genai``  — Google Gemini via ``langchain-google-genai``.
        * ``openai``        — OpenAI or any OpenAI-compatible API
                              (set ``base_url`` to point elsewhere).
        * ``ollama``        — Ollama server, defaults to localhost.
        * ``ollama_cloud``  — Ollama Cloud at ``https://ollama.com``;
                              ``api_key`` is sent as a Bearer token.
    """
    provider = config.provider

    if provider == "google_genai":
        from langchain_google_genai import ChatGoogleGenerativeAI

        kwargs: dict = {"model": config.model, "temperature": config.temperature}
        if config.api_key:
            kwargs["google_api_key"] = config.api_key
        return ChatGoogleGenerativeAI(**kwargs)

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        kwargs = {"model": config.model, "temperature": config.temperature}
        if config.api_key:
            kwargs["api_key"] = config.api_key
        if config.base_url:
            kwargs["base_url"] = config.base_url
        return ChatOpenAI(**kwargs)

    if provider in ("ollama", "ollama_cloud"):
        from langchain_ollama import ChatOllama

        if config.base_url:
            base_url = config.base_url
        elif provider == "ollama_cloud":
            base_url = "https://ollama.com"
        else:
            base_url = "http://localhost:11434"

        # Ollama Cloud authenticates with a Bearer token; for self-hosted
        # Ollama the api_key is usually unset and headers stay empty.
        client_kwargs: dict = {}
        if config.api_key:
            client_kwargs["headers"] = {
                "Authorization": f"Bearer {config.api_key}",
            }

        return ChatOllama(
            model=config.model,
            temperature=config.temperature,
            base_url=base_url,
            client_kwargs=client_kwargs or None,
        )

    raise ValueError(f"Unsupported LLM provider: {provider!r}")
