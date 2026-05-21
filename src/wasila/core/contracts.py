from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

JSONDict = dict[str, Any]


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(slots=True)
class CustomerEvent:
    gateway: str
    gateway_role: Literal["customer"] = "customer"
    external_conversation_id: str = ""
    external_customer_id: str = ""
    message_text: str = ""
    message_timestamp: str = field(default_factory=utc_now_iso)
    id: str | None = None
    customer_id: str | None = None
    metadata_json: JSONDict = field(default_factory=dict)


@dataclass(slots=True)
class CustomerContext:
    customer: JSONDict = field(default_factory=dict)
    customer_memory_markdown: str = ""
    business_knowledge_markdown: str = ""
    open_tickets: list[JSONDict] = field(default_factory=list)
    recent_messages: list[JSONDict] = field(default_factory=list)
    profile: str = "startup_saas"


@dataclass(slots=True)
class TicketUpdate:
    action: Literal["create", "update", "comment", "close"]
    title: str = ""
    status: str = "open"
    priority: str = "medium"
    summary: str = ""
    ticket_id: str | None = None
    metadata_json: JSONDict = field(default_factory=dict)


@dataclass(slots=True)
class MemoryUpdate:
    customer_id: str
    section: str
    body: str
    reason: str = ""


@dataclass(slots=True)
class OwnerNotification:
    profile: str
    customer_id: str
    summary: str
    risk_level: Literal["low", "medium", "high", "urgent"] = "low"
    recommended_action: str = ""
    ticket_id: str | None = None
    id: str | None = None
    metadata_json: JSONDict = field(default_factory=dict)


@dataclass(slots=True)
class SkillCall:
    agent_name: str
    skill_name: str
    execution_level: Literal["read", "write", "external", "approval_required"]
    approval_required: bool
    input_json: JSONDict = field(default_factory=dict)
    id: str | None = None


@dataclass(slots=True)
class SkillResult:
    skill_name: str
    status: Literal["success", "failed", "pending_approval", "skipped"]
    approval_status: Literal["not_required", "pending", "approved", "rejected"]
    output_json: JSONDict = field(default_factory=dict)
    skill_call_id: str | None = None
    id: str | None = None
    error: str | None = None


@dataclass(slots=True)
class AgentRun:
    profile: str
    agent_name: str
    task_name: str
    status: str
    input_json: JSONDict = field(default_factory=dict)
    output_json: JSONDict = field(default_factory=dict)
    id: str | None = None
    customer_id: str | None = None
    ticket_id: str | None = None


@dataclass(slots=True)
class OrchestrationResult:
    customer_response: str
    ticket_updates: list[TicketUpdate] = field(default_factory=list)
    memory_updates: list[MemoryUpdate] = field(default_factory=list)
    owner_notifications: list[OwnerNotification] = field(default_factory=list)
    skill_results: list[SkillResult] = field(default_factory=list)
    agent_runs: list[AgentRun] = field(default_factory=list)
    metadata_json: JSONDict = field(default_factory=dict)

