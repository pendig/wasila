from __future__ import annotations

from dataclasses import asdict, dataclass, field
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
    input_json: JSONDict = field(default_factory=dict)
    output_json: JSONDict = field(default_factory=dict)
    skill_call_id: str | None = None
    id: str | None = None
    error: str | None = None
    metadata_json: JSONDict = field(default_factory=dict)


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
class PrivateAgentJob:
    job_id: str
    customer_id: str
    intent: str
    summary: str
    ticket_id: str | None = None
    safe_context: JSONDict = field(default_factory=dict)
    forbidden: list[str] = field(default_factory=list)

    def to_json(self) -> JSONDict:
        return asdict(self)


@dataclass(slots=True)
class PrivateAgentResult:
    job_id: str
    status: Literal["done", "needs_owner", "failed"]
    customer_reply: str
    owner_note: str = ""
    actions_requested: list[JSONDict] = field(default_factory=list)

    def to_json(self) -> JSONDict:
        return asdict(self)


_PRIVATE_AGENT_JOB_KEYS = {
    "job_id",
    "customer_id",
    "ticket_id",
    "intent",
    "summary",
    "safe_context",
    "forbidden",
}
_PRIVATE_AGENT_RESULT_KEYS = {
    "job_id",
    "status",
    "customer_reply",
    "owner_note",
    "actions_requested",
}
_SECRET_KEY_NAMES = {
    "api_key",
    "access_token",
    "auth_token",
    "cookie",
    "credentials",
    "gateway_credentials",
    "password",
    "secret",
    "session",
    "token",
}


def _reject_unknown_keys(data: JSONDict, allowed: set[str], contract: str) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ValueError(f"{contract} has unsupported fields: {', '.join(unknown)}")


def _reject_secret_keys(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in _SECRET_KEY_NAMES:
                raise ValueError(f"private agent payload must not include customer-channel credential field: {path}.{key}")
            _reject_secret_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_secret_keys(child, f"{path}[{index}]")


def _require_str(data: JSONDict, key: str, contract: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{contract}.{key} must be a non-empty string")
    return value


def _optional_str(data: JSONDict, key: str, contract: str) -> str | None:
    value = data.get(key)
    if value is None or isinstance(value, str):
        return value
    raise ValueError(f"{contract}.{key} must be a string or null")


def private_agent_job_from_json(data: JSONDict) -> PrivateAgentJob:
    _reject_unknown_keys(data, _PRIVATE_AGENT_JOB_KEYS, "PrivateAgentJob")
    _reject_secret_keys(data)
    safe_context = data.get("safe_context", {})
    forbidden = data.get("forbidden", [])
    if not isinstance(safe_context, dict):
        raise ValueError("PrivateAgentJob.safe_context must be an object")
    if not isinstance(forbidden, list) or not all(isinstance(item, str) for item in forbidden):
        raise ValueError("PrivateAgentJob.forbidden must be a list of strings")
    return PrivateAgentJob(
        job_id=_require_str(data, "job_id", "PrivateAgentJob"),
        customer_id=_require_str(data, "customer_id", "PrivateAgentJob"),
        ticket_id=_optional_str(data, "ticket_id", "PrivateAgentJob"),
        intent=_require_str(data, "intent", "PrivateAgentJob"),
        summary=_require_str(data, "summary", "PrivateAgentJob"),
        safe_context=safe_context,
        forbidden=forbidden,
    )


def private_agent_result_from_json(data: JSONDict) -> PrivateAgentResult:
    _reject_unknown_keys(data, _PRIVATE_AGENT_RESULT_KEYS, "PrivateAgentResult")
    actions_requested = data.get("actions_requested", [])
    if data.get("status") not in {"done", "needs_owner", "failed"}:
        raise ValueError("PrivateAgentResult.status must be done, needs_owner, or failed")
    if not isinstance(actions_requested, list) or not all(isinstance(item, dict) for item in actions_requested):
        raise ValueError("PrivateAgentResult.actions_requested must be a list of objects")
    owner_note = data.get("owner_note", "")
    if not isinstance(owner_note, str):
        raise ValueError("PrivateAgentResult.owner_note must be a string")
    return PrivateAgentResult(
        job_id=_require_str(data, "job_id", "PrivateAgentResult"),
        status=data["status"],
        customer_reply=_require_str(data, "customer_reply", "PrivateAgentResult"),
        owner_note=owner_note,
        actions_requested=actions_requested,
    )


@dataclass(slots=True)
class OrchestrationResult:
    customer_response: str
    ticket_updates: list[TicketUpdate] = field(default_factory=list)
    memory_updates: list[MemoryUpdate] = field(default_factory=list)
    owner_notifications: list[OwnerNotification] = field(default_factory=list)
    skill_results: list[SkillResult] = field(default_factory=list)
    agent_runs: list[AgentRun] = field(default_factory=list)
    metadata_json: JSONDict = field(default_factory=dict)
