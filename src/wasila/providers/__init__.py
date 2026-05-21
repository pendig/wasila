"""Provider adapters for Wasila."""

from wasila.config.models import ProviderSettings
from wasila.providers.crewai_llm import build_crewai_llm
from wasila.runner.crewai_runner import CrewAIRunner


def build_orchestrator(profile, provider: ProviderSettings):
    """Build the configured orchestration runner."""
    return CrewAIRunner(profile, provider)


__all__ = ["build_orchestrator", "build_crewai_llm", "CrewAIRunner"]
