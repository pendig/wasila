from __future__ import annotations

import json
import os
import re
from typing import Any

from wasila.config.models import ProviderSettings
from wasila.core.contracts import (
    AgentRun,
    CustomerContext,
    CustomerEvent,
    MemoryUpdate,
    OrchestrationResult,
    OwnerNotification,
    SkillResult,
    TicketUpdate,
)
from wasila.core.ports import Orchestrator
from wasila.providers.crewai_llm import build_crewai_llm
from wasila.profiles import ProfileDefinition


class CrewAIRunner(Orchestrator):
    def __init__(self, profile: ProfileDefinition, provider: ProviderSettings) -> None:
        self.profile = profile
        self.provider = provider
        self._crewai: Any | None = None
        self._llm = None
        try:
            from crewai import Agent, Crew, Task

            self._crewai = (Agent, Crew, Task)
            self._llm = build_crewai_llm(provider)
        except Exception:
            self._crewai = None

    def run(self, event: CustomerEvent, context: CustomerContext) -> OrchestrationResult:
        if not self._crewai or not self._llm:
            return _fallback_run(self.profile, event, context)

        api_key = os.getenv(self.provider.api_key_env)
        if not api_key:
            return _fallback_run(self.profile, event, context)

        try:
            return _run_crewai(self._crewai, self._llm, self.profile, event, context)
        except Exception:
            return _fallback_run(self.profile, event, context)


def _fallback_run(profile: ProfileDefinition, event: CustomerEvent, context: CustomerContext) -> OrchestrationResult:
    text = event.message_text.lower()

    memory_updates: list[MemoryUpdate] = []
    ticket_updates: list[TicketUpdate] = []
    owner_notifications: list[OwnerNotification] = []
    skill_results: list[SkillResult] = []
    agent_runs: list[AgentRun] = []

    if "refund" in text:
        ticket_updates.append(
            TicketUpdate(
                action="create",
                title="Billing refund request",
                summary="Customer asks for a refund.",
                priority="high",
                status="open",
                metadata_json={"source": "fallback"},
            )
        )
        owner_notifications.append(
            OwnerNotification(
                profile=profile.id,
                customer_id=event.customer_id or "",
                ticket_id="",
                summary="Customer requested refund; requires owner review.",
                risk_level="high",
                recommended_action="Review billing policy before approval.",
            )
        )
        response = "I can’t approve refunds directly. I’m sending this to the owner for review."
    elif any(keyword in text for keyword in ("error", "broken", "bug", "integration", "can't", "cannot", "failed")):
        ticket_updates.append(
            TicketUpdate(
                action="create",
                title="Technical support follow-up",
                summary="Customer reports a technical issue.",
                priority="medium",
                status="open",
                metadata_json={"source": "fallback"},
            )
        )
        response = "Thanks for the details. I’ve created a follow-up and will ask the technical team to investigate."
    elif "concise" in text or "short" in text:
        memory_updates.append(
            MemoryUpdate(
                customer_id=event.customer_id or "",
                section="Preferences",
                body="Customer prefers concise responses.",
                reason="message_hint",
            )
        )
        response = "Got it — I’ll keep responses short and direct."
    else:
        response = "Thanks for your message. I’ve noted it and will continue with the next best step."

    if context.open_tickets:
        response += f" Current open tickets: {', '.join(t['id'] for t in context.open_tickets[:3])}."

    if ticket_updates:
        ticket_id = ticket_updates[0].ticket_id or ""
        skill_results.append(
            SkillResult(
                skill_name="ticket.create",
                status="success",
                approval_status="not_required",
                input_json=ticket_updates[0].__dict__,
                output_json={"ticket_action": "create", "ticket_id": ticket_id},
                metadata_json={"execution_level": "write"},
            )
        )
    if memory_updates:
        skill_results.append(
            SkillResult(
                skill_name="memory.suggest_update",
                status="success",
                approval_status="not_required",
                input_json=memory_updates[0].__dict__,
                output_json={"stored": False},
                metadata_json={"execution_level": "write"},
            )
        )

    agent_runs.append(
        AgentRun(
            profile=profile.id,
            agent_name="front_office",
            task_name="triage_customer_message",
            status="success",
            input_json={"message": event.message_text[:500]},
            output_json={"customer_response": response},
        )
    )

    return OrchestrationResult(
        customer_response=response,
        ticket_updates=ticket_updates,
        memory_updates=memory_updates,
        owner_notifications=owner_notifications,
        skill_results=skill_results,
        agent_runs=agent_runs,
    )


def _run_crewai(crewai: tuple, llm: Any, profile: ProfileDefinition, event: CustomerEvent, context: CustomerContext) -> OrchestrationResult:
    Agent, Crew, Task = crewai
    prompt = _build_prompt(profile, event, context)
    response = _run_simple_crew(Agent=Agent, Crew=Crew, Task=Task, llm=llm, profile=profile, prompt=prompt)
    parsed = _parse_structured_output(response)
    return _as_result(profile.id, event, parsed)


def _run_simple_crew(*, Agent, Crew, Task, llm: Any, profile: ProfileDefinition, prompt: str) -> str:
    front_agent = Agent(
        role=profile.agents.get("front_office", {}).get("role", "Support Agent"),
        goal=profile.agents.get("front_office", {}).get("goal", "Answer support messages."),
        backstory=profile.agents.get("front_office", {}).get("backstory", ""),
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )

    orchestration_task = Task(
        description=prompt,
        expected_output="JSON with keys: customer_response, action, ticket_summary, memory_section, memory_body, owner_needed, owner_summary, owner_action, owner_risk",
        agent=front_agent,
    )

    crew = Crew(agents=[front_agent], tasks=[orchestration_task], verbose=False)
    result = crew.kickoff()
    return str(result)


def _parse_structured_output(raw: str) -> dict[str, Any]:
    if not raw:
        return {}
    match = re.search(r"\{.*\}", raw, flags=re.S)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}


def _as_result(profile_id: str, event: CustomerEvent, payload: dict[str, Any]) -> OrchestrationResult:
    response = payload.get("customer_response") or "Thanks for sharing. I’m checking this."
    ticket_updates: list[TicketUpdate] = []
    memory_updates: list[MemoryUpdate] = []
    owner_notifications: list[OwnerNotification] = []
    skill_results: list[SkillResult] = []
    agent_runs: list[AgentRun] = []

    action = payload.get("action", "comment")
    if isinstance(action, str) and action != "none":
        ticket_updates.append(
            TicketUpdate(
                action="create" if action == "create" else "update",
                title=payload.get("ticket_title", "Customer support follow-up"),
                summary=payload.get("ticket_summary", response),
                priority=payload.get("ticket_priority", "medium"),
                status=payload.get("ticket_status", "open"),
                metadata_json={"source": "crewai"},
            )
        )
        skill_results.append(
            SkillResult(
                skill_name="ticket.update" if action != "create" else "ticket.create",
                status="success",
                approval_status="not_required",
                input_json={"action": action},
                output_json={"ticket_title": payload.get("ticket_title", "")},
                metadata_json={"execution_level": "write"},
            )
        )

    memory_section = payload.get("memory_section")
    memory_body = payload.get("memory_body")
    if memory_section and memory_body:
        memory_updates.append(
            MemoryUpdate(
                customer_id=event.customer_id or "",
                section=str(memory_section),
                body=str(memory_body),
                reason="crewai_output",
            )
        )
        skill_results.append(
            SkillResult(
                skill_name="memory.suggest_update",
                status="success",
                approval_status="not_required",
                input_json={"section": memory_section},
                output_json={"memory_body": memory_body},
                metadata_json={"execution_level": "write"},
            )
        )

    owner_needed = _normalize_bool(payload.get("owner_needed", False))
    if owner_needed:
        owner_notifications.append(
            OwnerNotification(
                profile=profile_id,
                customer_id=event.customer_id or "",
                ticket_id=payload.get("ticket_id"),
                summary=payload.get("owner_summary", "Customer message needs review."),
                risk_level=payload.get("owner_risk", "low"),
                recommended_action=payload.get("owner_action", ""),
            )
        )

    agent_runs.append(
        AgentRun(
            profile=profile_id,
            agent_name="front_office",
            task_name="triage_customer_message",
            status="success",
            input_json={"message": event.message_text[:500]},
            output_json={"parsed_payload": payload},
        )
    )

    return OrchestrationResult(
        customer_response=response,
        ticket_updates=ticket_updates,
        memory_updates=memory_updates,
        owner_notifications=owner_notifications,
        skill_results=skill_results,
        agent_runs=agent_runs,
    )


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return False


def _build_prompt(profile: ProfileDefinition, event: CustomerEvent, context: CustomerContext) -> str:
    open_tickets = ", ".join(ticket.get("id", "") for ticket in context.open_tickets[:3]) or "none"
    memory = context.customer_memory_markdown[:700].strip() or "none"
    knowledge = context.business_knowledge_markdown[:1200].strip() or "none"
    front_prompt = profile.prompts.get("front_office", "")

    return f"""{front_prompt}

Customer:
{event.message_text}

Business knowledge:
{knowledge}

Customer memory:
{memory}

Open tickets:
{open_tickets}

Produce strict JSON with keys:
- customer_response (short, helpful)
- action (one of none|create|update|comment)
- ticket_title
- ticket_summary
- ticket_priority (low|medium|high)
- ticket_status (open|in_progress|closed)
- memory_section (optional)
- memory_body (optional)
- owner_needed (true|false)
- owner_summary (required when owner_needed=true)
- owner_action (optional)
- owner_risk (low|medium|high|urgent)

"""
