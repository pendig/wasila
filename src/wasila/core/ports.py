from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from wasila.core.contracts import (
    CustomerContext,
    CustomerEvent,
    TicketUpdate,
    AgentRun,
    MemoryUpdate,
    OrchestrationResult,
    OwnerNotification,
    PrivateAgentJob,
    PrivateAgentResult,
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


class PrivateAgentAdapter(Protocol):
    def run(self, job: PrivateAgentJob) -> PrivateAgentResult:
        """Run a sanitized private assistant job."""
        ...


class Storage(Protocol):

    def initialize(self) -> None:
        """Create or migrate storage."""

    def find_message_by_event(self, gateway: str, event_id: str) -> dict[str, Any] | None:
        """Return stored message row for an incoming event if already processed."""

    def ensure_customer(
        self,
        *,
        customer_id_hint: str | None,
        external_customer_id: str,
        gateway: str,
        external_conversation_id: str | None = None,
        display_name: str | None = None,
    ) -> str:
        """Resolve an existing customer or create a new one."""

    def get_customer(self, customer_id: str) -> dict[str, Any] | None:
        """Load customer metadata."""

    def create_message(
        self,
        *,
        message_id: str,
        customer_id: str,
        ticket_id: str | None,
        gateway: str,
        direction: str,
        body: str,
        metadata_json: dict[str, Any],
        event_id: str | None = None,
    ) -> None:
        """Persist one message entry."""

    def update_message_metadata(self, message_id: str, metadata_json: dict[str, Any]) -> None:
        """Update message metadata for idempotent returns."""

    def list_open_tickets(self, customer_id: str) -> list[dict[str, Any]]:
        """List non-closed tickets for a customer."""

    def list_recent_messages(self, customer_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Load recent message history for context."""

    def get_open_tickets_for_context(self, customer_id: str) -> list[dict[str, Any]]:
        """Alias used by orchestration context for open tickets."""

    def apply_ticket_update(self, customer_id: str, update: TicketUpdate) -> str:
        """Apply a ticket update and return the effective ticket id."""

    def create_agent_run(self, run: AgentRun) -> str:
        """Persist a CrewAI agent run."""

    def create_skill_execution(self, result: SkillResult) -> str:
        """Persist one skill execution record."""

    def create_owner_summary(self, notification: OwnerNotification) -> str:
        """Persist one owner summary."""

    def list_owner_summaries(self, customer_id: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        """Load recent owner summaries."""

    def list_tickets(self, status: str | None = None) -> list[dict[str, Any]]:
        """List stored tickets with optional status filter."""


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

    def allow_owner_notification(self, notification: OwnerNotification) -> bool:
        """Return whether owner notification should be sent."""

    def allow_private_agent_delegation(self, result: OrchestrationResult) -> bool:
        """Return whether a private assistant should receive the sanitized job."""
        ...

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
