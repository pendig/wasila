from __future__ import annotations

import os
from typing import Any

from wasila.config.models import ProviderSettings


def crewai_llm_kwargs(settings: ProviderSettings) -> dict[str, Any]:
    """Translate Wasila provider settings into CrewAI LLM keyword arguments."""

    kwargs: dict[str, Any] = {"model": settings.model}
    if settings.base_url:
        kwargs["base_url"] = settings.base_url

    api_key = os.getenv(settings.api_key_env)
    if api_key:
        kwargs["api_key"] = api_key

    return kwargs


def build_crewai_llm(settings: ProviderSettings):
    """Build a CrewAI LLM instance from Wasila provider settings."""

    try:
        from crewai import LLM
    except ImportError as exc:
        raise RuntimeError(
            'CrewAI is not installed. Install the adapter dependency with: pip install -e ".[crewai]"'
        ) from exc

    return LLM(**crewai_llm_kwargs(settings))
