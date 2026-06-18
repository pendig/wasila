from __future__ import annotations

import hashlib
from dataclasses import dataclass
from dataclasses import field
from dataclasses import asdict
from typing import Any
from uuid import uuid4

from wasila.config.models import ProjectConfig
from wasila.core.contracts import (
    AgentRun,
    CustomerContext,
    CustomerEvent,
    MemoryUpdate,
    OrchestrationResult,
    OwnerNotification,
    PrivateAgentJob,
    SkillCall,
    SkillResult,
    TicketUpdate,
)
from wasila.core.policies import DefaultPolicyEngine
from wasila.core.ports import Orchestrator, OwnerGateway, PolicyEngine, Storage
from wasila.core.ports import CustomerMemoryStore, KnowledgeLoader, PrivateAgentAdapter
from wasila.profiles import ProfileDefinition


def _build_dedup_event_id(event: CustomerEvent) -> str:
    raw = "|".join(
        [
            event.gateway,
            event.external_conversation_id,
            event.external_customer_id,
            event.message_timestamp,
            event.message_text.strip(),
            event.id or "",
        ]
    )
    return f"evt_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:24]}"


@dataclass
class Workflow:
    config: ProjectConfig
    profile: ProfileDefinition
    storage: Storage
    orchestrator: Orchestrator
    memory_store: CustomerMemoryStore
    knowledge_loader: KnowledgeLoader
    owner_gateway: OwnerGateway
    policy: PolicyEngine = field(default_factory=DefaultPolicyEngine)
    private_agent_adapter: PrivateAgentAdapter | None = None
    private_agent_name: str | None = None

    def run(self, event: CustomerEvent) -> OrchestrationResult:
        event_id = event.id or _build_dedup_event_id(event)
        if not event.external_conversation_id:
            event.external_conversation_id = event.external_customer_id

        existing = self.storage.find_message_by_event(event.gateway, event_id)
        if existing and isinstance(existing.get("metadata_json"), dict):
            prior_result = existing["metadata_json"].get("orchestration_result")
            if isinstance(prior_result, dict):
                return OrchestrationResult(
                    customer_response=str(prior_result.get("customer_response", "")),
                    metadata_json={"duplicate": True},
                )

        customer_id = self.storage.ensure_customer(
            customer_id_hint=event.customer_id,
            external_customer_id=event.external_customer_id,
            gateway=event.gateway,
            external_conversation_id=event.external_conversation_id,
            display_name=event.metadata_json.get("display_name"),
        )
        event.customer_id = customer_id

        _ = self.memory_store.ensure(customer_id, event.metadata_json.get("display_name"))
        customer_context = CustomerContext(
            customer=self.storage.get_customer(customer_id) or {},
            customer_memory_markdown=self.memory_store.read(customer_id),
            business_knowledge_markdown=self.knowledge_loader.load_markdown(),
            open_tickets=self.storage.get_open_tickets_for_context(customer_id),
            recent_messages=self.storage.list_recent_messages(customer_id, limit=6),
            profile=self.profile.id,
        )

        inbound_message_id = f"in_{uuid4().hex}"
        self.storage.create_message(
            message_id=inbound_message_id,
            customer_id=customer_id,
            ticket_id=None,
            gateway=event.gateway,
            direction="inbound",
            body=event.message_text,
            metadata_json={
                "event_id": event_id,
                "received_via": event.gateway,
                "status": "received",
                "source_event_timestamp": event.message_timestamp,
            },
            event_id=event_id,
        )

        result = self._run_orchestrator(event, customer_context)
        self._maybe_delegate_to_private_agent(event, customer_context, result)

        applied_ticket_ids = self._apply_ticket_updates(customer_id, result.ticket_updates)
        self._apply_memory_updates(customer_id, applied_ticket_ids, result.memory_updates)
        self._apply_agent_runs(customer_id, applied_ticket_ids, result.agent_runs)
        owner_summary_ids = self._apply_owner_notifications(customer_id, result.owner_notifications)
        self._apply_skill_executions(result.skill_results, customer_id, applied_ticket_ids)

        outbound_message = self._emit_customer_reply(
            event=event,
            event_id=event_id,
            customer_id=customer_id,
            inbound_message_id=inbound_message_id,
            result=result,
            ticket_ids=applied_ticket_ids,
            owner_summary_ids=owner_summary_ids,
        )

        self.storage.update_message_metadata(
            inbound_message_id,
            {
                "event_id": event_id,
                "status": "processed",
                "customer_id": customer_id,
                "ticket_ids": applied_ticket_ids,
                "owner_summary_ids": owner_summary_ids,
                "orchestration_result": {
                    "customer_response": result.customer_response,
                    "ticket_ids": applied_ticket_ids,
                    "owner_summary_ids": owner_summary_ids,
                    "outbound_message_id": outbound_message,
                },
            },
        )
        result.metadata_json.update(
            {
                "customer_id": customer_id,
                "ticket_ids": applied_ticket_ids,
                "owner_summary_ids": owner_summary_ids,
                "event_id": event_id,
            }
        )
        return result

    def _run_orchestrator(self, event: CustomerEvent, customer_context: CustomerContext) -> OrchestrationResult:
        try:
            return self.orchestrator.run(event, customer_context)
        except Exception as exc:  # pragma: no cover - guardrail fallback
            return OrchestrationResult(
                customer_response="I can help with this, and I'll pass it to a teammate for follow-up.",
                metadata_json={"failure": "orchestrator_error", "error": str(exc)},
            )

    def _maybe_delegate_to_private_agent(
        self,
        event: CustomerEvent,
        customer_context: CustomerContext,
        result: OrchestrationResult,
    ) -> None:
        if not self.private_agent_adapter or not self.config.assistants:
            return
        if not self.policy.allow_private_agent_delegation(result):
            return

        assistant_name = self.private_agent_name or self._first_cli_assistant_name()
        if not assistant_name:
            return
        job = PrivateAgentJob(
            job_id=f"paj_{uuid4().hex}",
            customer_id=customer_context.customer.get("id", event.customer_id or ""),
            intent=str(result.metadata_json.get("private_agent_intent") or "assist"),
            summary=event.message_text.strip() or "No message text provided",
            safe_context={
                "frontdesk_reply": result.customer_response,
                "customer_message": event.message_text,
            },
            forbidden=[
                "do not contact the customer directly",
                "do not expose internal memory or credentials",
            ],
        )
        try:
            private_result = self.private_agent_adapter.run(job)
        except Exception as exc:  # pragma: no cover - guardrail fallback
            result.metadata_json["private_agent_error"] = str(exc)
            return

        result.metadata_json["private_agent_delegated"] = True
        result.metadata_json["private_agent_name"] = assistant_name
        result.agent_runs.append(
            AgentRun(
                profile=customer_context.profile,
                agent_name="private_agent",
                task_name="delegation",
                status=private_result.status,
                input_json=job.to_json(),
                output_json=private_result.to_json(),
            )
        )
        if private_result.status in {"done", "needs_owner"}:
            filtered_reply = self._customer_safe_reply(private_result.customer_reply)
            if filtered_reply:
                result.customer_response = filtered_reply

    def _first_cli_assistant_name(self) -> str | None:
        for name, assistant in self.config.assistants.items():
            if assistant.type == "cli" and assistant.command:
                return name
        return None

    @staticmethod
    def _customer_safe_reply(reply: str) -> str:
        blocked = ("internal memory", "credential", "secret", "token", "do not contact the customer")
        lines = [line.strip() for line in reply.splitlines()]
        return "\n".join(line for line in lines if line and not any(word in line.lower() for word in blocked))

    def _apply_ticket_updates(self, customer_id: str, updates: list[TicketUpdate]) -> list[str]:
        ticket_ids: list[str] = []
        for update in updates:
            resolved = self.storage.apply_ticket_update(customer_id, update)
            if resolved and resolved not in ticket_ids:
                ticket_ids.append(resolved)
        return ticket_ids

    def _apply_memory_updates(
        self,
        customer_id: str,
        ticket_ids: list[str],
        updates: list[MemoryUpdate],
    ) -> None:
        for update in updates:
            if not self.policy.allow_memory_update(update):
                continue
            self.memory_store.upsert_section(customer_id, update.section, update.body)
            if ticket_ids:
                self.storage.create_skill_execution(
                    SkillResult(
                        skill_name="memory.suggest_update",
                        status="success",
                        approval_status="not_required",
                        input_json=asdict(update),
                        output_json={"stored": True},
                        metadata_json={
                            "execution_level": "write",
                            "customer_id": customer_id,
                            "ticket_id": ticket_ids[0],
                            "reason": "policy_allow",
                        },
                    )
                )

    def _apply_agent_runs(self, customer_id: str, ticket_ids: list[str], runs: list[AgentRun]) -> None:
        if not runs:
            return
        for run in runs:
            if not run.customer_id:
                run.customer_id = customer_id
            if not run.ticket_id and ticket_ids:
                run.ticket_id = ticket_ids[0]
            self.storage.create_agent_run(run)

    def _apply_skill_executions(
        self,
        skill_results: list[SkillResult],
        customer_id: str,
        ticket_ids: list[str],
    ) -> None:
        for result in skill_results:
            if not self.policy.allow_skill_execution(SkillCall(
                agent_name="orchestrator",
                skill_name=result.skill_name,
                execution_level=result.metadata_json.get("execution_level", "write"),
                approval_required=result.approval_status == "pending",
                input_json=result.input_json,
                id=result.id,
            )):
                result.status = "skipped"
            if not result.metadata_json:
                result.metadata_json = {}
            result.metadata_json.setdefault("customer_id", customer_id)
            if not result.metadata_json.get("ticket_id") and ticket_ids:
                result.metadata_json["ticket_id"] = ticket_ids[0]
            self.storage.create_skill_execution(result)

    def _apply_owner_notifications(
        self,
        customer_id: str,
        notifications: list[OwnerNotification],
    ) -> list[str]:
        created: list[str] = []
        for notification in notifications:
            notification.customer_id = customer_id
            if not notification.risk_level:
                notification.risk_level = "low"
            if not self.policy.allow_owner_notification(notification):
                continue

            notification.id = self.storage.create_owner_summary(notification)
            created.append(notification.id)
            try:
                self.owner_gateway.deliver(notification)
            except Exception:
                # Owner delivery is optional during Stage 1.
                # Keep the orchestration trace and continue without dropping the owner summary.
                continue

        return created

    def _emit_customer_reply(
        self,
        *,
        event: CustomerEvent,
        event_id: str,
        customer_id: str,
        inbound_message_id: str,
        result: OrchestrationResult,
        ticket_ids: list[str],
        owner_summary_ids: list[str],
    ) -> str:
        outbound_message = f"out_{uuid4().hex}"
        outbound_body = result.customer_response or "Thanks for reaching out. We'll follow up."
        ticket_for_reply = ticket_ids[0] if ticket_ids else None
        outbound_payload: dict[str, Any] = {
            "event_id": event_id,
            "status": "outbound",
            "ticket_ids": ticket_ids,
            "owner_summary_ids": owner_summary_ids,
            "reply_to": inbound_message_id,
        }
        if owner_summary_ids:
            outbound_payload["owner_attention"] = True

        self.storage.create_message(
            message_id=outbound_message,
            customer_id=customer_id,
            ticket_id=ticket_for_reply,
            gateway=event.gateway,
            direction="outbound",
            body=outbound_body,
            metadata_json=outbound_payload,
            event_id=None,
        )
        return outbound_message

    def context_snapshot(self, customer_id: str) -> CustomerContext:
        return CustomerContext(
            customer=self.storage.get_customer(customer_id) or {},
            customer_memory_markdown=self.memory_store.read(customer_id),
            business_knowledge_markdown=self.knowledge_loader.load_markdown(),
            open_tickets=self.storage.get_open_tickets_for_context(customer_id),
            recent_messages=self.storage.list_recent_messages(customer_id, limit=20),
            profile=self.profile.id,
        )
