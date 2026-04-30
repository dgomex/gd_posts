"""Pydantic-based configuration loaded from environment variables / .env.

Two LLMs are configured independently using the nested env var convention
``WRITER__*`` and ``JUDGE__*`` (the double underscore is the
``env_nested_delimiter``).

Example .env::

    WRITER__PROVIDER=ollama_cloud
    WRITER__MODEL=gpt-oss:120b-cloud
    WRITER__API_KEY=ollama-...
    JUDGE__PROVIDER=google_genai
    JUDGE__MODEL=gemini-2.0-flash
    JUDGE__API_KEY=AIza...
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProvider = Literal["google_genai", "openai", "ollama", "ollama_cloud"]


class LLMConfig(BaseModel):
    """Provider-agnostic configuration for a single chat model."""

    provider: LLMProvider = "google_genai"
    model: str = "gemini-2.0-flash"
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.7

    @field_validator("base_url", "api_key", mode="before")
    @classmethod
    def _empty_to_none(cls, v: object) -> object:
        # pydantic-settings reads empty env vars as "" — treat them as unset.
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class Settings(BaseSettings):
    """Top-level app settings.

    Values are loaded from the process environment, falling back to a local
    ``.env`` file. Nested ``LLMConfig`` fields use ``WRITER__*`` /
    ``JUDGE__*`` env var prefixes thanks to ``env_nested_delimiter='__'``.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    writer: LLMConfig = Field(
        default_factory=lambda: LLMConfig(temperature=0.8),
        description="LLM that drafts and rewrites the post.",
    )
    judge: LLMConfig = Field(
        default_factory=lambda: LLMConfig(temperature=0.2),
        description="LLM that reviews drafts and emits structured feedback.",
    )

    max_iterations: int = Field(
        default=3, ge=1, le=10,
        description="Maximum number of writer/judge rounds before giving up.",
    )
    prompts_dir: Path = Field(default=Path("prompts"))


def get_settings() -> Settings:
    """Return a freshly loaded Settings instance."""
    return Settings()
