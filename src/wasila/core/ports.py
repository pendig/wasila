from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from wasila.core.contracts import (
    CustomerContext,
    CustomerEvent,
    MemoryUpdate,
    OrchestrationResult,
    OwnerNotification,
    SkillCall,
    SkillResult,
)


@dataclass(frozen=True, slots=True)
class ProviderConfig:
    type: str
    base_url: str
    model: str
    api_key_env: str


class Orchestrator(Protocol):
    def run(self, event: CustomerEvent, context: CustomerContext) -> OrchestrationResult:
        """Run orchestration for a customer event."""


class Storage(Protocol):
    def initialize(self) -> None:
        """Create or migrate storage."""


class CustomerGateway(Protocol):
    name: str

    def normalize(self, payload: dict) -> CustomerEvent:
        """Convert an external payload into a CustomerEvent."""


class OwnerGateway(Protocol):
    name: str

    def deliver(self, notification: OwnerNotification) -> None:
        """Deliver an owner notification."""


class ProfileRegistry(Protocol):
    def load(self, profile_id: str) -> dict:
        """Load a profile definition."""


class SkillRegistry(Protocol):
    def execute(self, call: SkillCall) -> SkillResult:
        """Execute or defer a registered skill."""


class PolicyEngine(Protocol):
    def allow_memory_update(self, update: MemoryUpdate) -> bool:
        """Return whether a memory update is safe and durable enough."""

    def allow_skill_execution(self, call: SkillCall) -> bool:
        """Return whether a skill call can execute without approval."""


class KnowledgeLoader(Protocol):
    def load_markdown(self) -> str:
        """Load business knowledge as Markdown."""


class CustomerMemoryStore(Protocol):
    def memory_path(self, customer_id: str) -> Path:
        """Return the customer memory path."""

    def read(self, customer_id: str) -> str:
        """Read customer memory."""

    def ensure(self, customer_id: str, display_name: str | None = None) -> Path:
        """Create a customer memory file when missing."""

