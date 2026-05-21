import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from wasila.core.contracts import (
    AgentRun,
    CustomerContext,
    CustomerEvent,
    MemoryUpdate,
    OwnerNotification,
    OrchestrationResult,
    SkillResult,
    TicketUpdate,
)
from wasila.core.policies import DefaultPolicyEngine
from wasila.core.workflow import Workflow


class _FakeStorage:
    def __init__(self) -> None:
        self._customers: dict[str, dict] = {}
        self._messages: list[dict] = []
        self._events: dict[tuple[str, str], dict] = {}
        self._tickets: dict[str, dict] = {}

    def initialize(self) -> None:
        pass

    def find_message_by_event(self, gateway: str, event_id: str) -> dict | None:
        return self._events.get((gateway, event_id))

    def ensure_customer(
        self,
        *,
        customer_id_hint: str | None,
        external_customer_id: str,
        gateway: str,
        external_conversation_id: str | None = None,
        display_name: str | None = None,
    ) -> str:
        if customer_id_hint and customer_id_hint in self._customers:
            return customer_id_hint
        customer_id = f"cust_{uuid4().hex[:8]}"
        self._customers[customer_id] = {"id": customer_id, "display_name": display_name or "Customer"}
        return customer_id

    def get_customer(self, customer_id: str) -> dict | None:
        return self._customers.get(customer_id)

    def create_message(
        self,
        *,
        message_id: str,
        customer_id: str,
        ticket_id: str | None,
        gateway: str,
        direction: str,
        body: str,
        metadata_json: dict,
        event_id: str | None = None,
    ) -> None:
        row = {
            "id": message_id,
            "customer_id": customer_id,
            "gateway": gateway,
            "direction": direction,
            "body": body,
            "metadata_json": metadata_json,
        }
        if event_id is not None:
            row["event_id"] = event_id
            self._events[(gateway, event_id)] = row
        self._messages.append(row)

    def update_message_metadata(self, message_id: str, metadata_json: dict) -> None:
        for message in self._messages:
            if message["id"] == message_id:
                message["metadata_json"] = metadata_json

    def list_open_tickets(self, customer_id: str):
        return self.get_open_tickets_for_context(customer_id)

    def get_open_tickets_for_context(self, customer_id: str):
        return [ticket for ticket in self._tickets.values() if ticket["customer_id"] == customer_id]

    def list_recent_messages(self, customer_id: str, limit: int = 10):
        return [
            message
            for message in self._messages
            if message["customer_id"] == customer_id
        ][:limit]

    def apply_ticket_update(self, customer_id: str, update: TicketUpdate) -> str:
        ticket_id = update.ticket_id or f"tick_{len(self._tickets) + 1}"
        self._tickets[ticket_id] = {
            "id": ticket_id,
            "customer_id": customer_id,
            "title": update.title,
            "status": update.status,
            "priority": update.priority,
            "summary": update.summary,
            "metadata_json": update.metadata_json,
        }
        return ticket_id

    def create_agent_run(self, run: AgentRun) -> str:
        return run.id or f"run_{uuid4().hex[:8]}"

    def create_skill_execution(self, result: SkillResult) -> str:
        return result.id or f"skill_{uuid4().hex[:8]}"

    def create_owner_summary(self, notification: OwnerNotification) -> str:
        return notification.id or f"own_{uuid4().hex[:8]}"

    def list_owner_summaries(self, customer_id: str | None = None, limit: int = 10):
        return []

    def list_tickets(self, status: str | None = None):
        tickets = list(self._tickets.values())
        if status:
            return [ticket for ticket in tickets if ticket["status"] == status]
        return tickets


class _FakeStorageWithTracking(_FakeStorage):
    def __init__(self) -> None:
        super().__init__()
        self.owner_summaries = 0
        self.agent_runs: list[AgentRun] = []
        self.owner_gateway_calls: list[OwnerNotification] = []

    def create_owner_summary(self, notification: OwnerNotification) -> str:
        self.owner_summaries += 1
        return super().create_owner_summary(notification)

    def create_agent_run(self, run: AgentRun) -> str:
        self.agent_runs.append(run)
        return super().create_agent_run(run)


class _FakeMemoryStore:
    def __init__(self, tmp_dir: Path) -> None:
        self.tmp_dir = tmp_dir

    def memory_path(self, customer_id: str) -> Path:
        path = self.tmp_dir / "customers" / customer_id / "customer.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def read(self, customer_id: str) -> str:
        path = self.memory_path(customer_id)
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def upsert_section(self, customer_id: str, section: str, body: str) -> None:
        path = self.memory_path(customer_id)
        if not path.exists():
            path.write_text(f"# {customer_id}\n\n", encoding="utf-8")
        existing = path.read_text(encoding="utf-8").strip()
        if not existing:
            existing = "# customer\n"
        path.write_text(f"{existing}\n## {section}\n{body}\n", encoding="utf-8")

    def ensure(self, customer_id: str, display_name: str | None = None) -> Path:
        path = self.memory_path(customer_id)
        if not path.exists():
            path.write_text(f"# {customer_id}\n\n", encoding="utf-8")
        return path


class _FakeKnowledgeLoader:
    def load_markdown(self) -> str:
        return "knowledge"


class _FakeOrchestrator:
    def run(self, event: CustomerEvent, context: CustomerContext) -> OrchestrationResult:
        return OrchestrationResult(
            customer_response="Handled with escalation",
            ticket_updates=[
                TicketUpdate(
                    action="create",
                    title="Billing issue",
                    summary="Customer asks for refund",
                    priority="high",
                    status="open",
                )
            ],
            memory_updates=[
                MemoryUpdate(
                    customer_id=context.customer.get("id", ""),
                    section="Preferences",
                    body="Prefers weekend support",
                    reason="initial profile",
                )
            ],
            owner_notifications=[
                OwnerNotification(
                    profile=context.profile,
                    customer_id=context.customer.get("id", ""),
                    summary="customer requested refund",
                    risk_level="high",
                    recommended_action="Review billing policy",
                )
            ],
            skill_results=[],
            agent_runs=[
                AgentRun(
                    profile=context.profile,
                    agent_name="front_office",
                    task_name="triage",
                    status="success",
                    input_json={"message": event.message_text},
                    output_json={"ok": True},
                )
            ],
            metadata_json={"from": "fake_orchestrator"},
        )


class _FakeOwnerGateway:
    def __init__(self) -> None:
        self.delivered: list[OwnerNotification] = []

    def deliver(self, notification: OwnerNotification) -> None:
        self.delivered.append(notification)


class _FakeProfile:
    id = "startup_saas"


class WorkflowTests(unittest.TestCase):
    def test_workflow_returns_duplicate_without_reprocessing_event(self):
        with TemporaryDirectory() as tmp:
            storage = _FakeStorage()
            owner_gateway = _FakeOwnerGateway()
            memory_store = _FakeMemoryStore(Path(tmp))
            workflow = Workflow(
                config=None,  # type: ignore[arg-type]
                profile=_FakeProfile(),
                storage=storage,
                orchestrator=_FakeOrchestrator(),
                memory_store=memory_store,
                knowledge_loader=_FakeKnowledgeLoader(),
                owner_gateway=owner_gateway,
                policy=DefaultPolicyEngine(),
            )

            event = CustomerEvent(
                id="evt_test_1",
                gateway="webhook",
                external_customer_id="ext_1",
                external_conversation_id="conv_1",
                message_text="Need refund.",
                message_timestamp="2026-05-21T00:00:00Z",
            )
            first = workflow.run(event)
            second = workflow.run(event)

            self.assertFalse(first.metadata_json.get("duplicate"))
            self.assertIn("ticket_ids", first.metadata_json)
            self.assertTrue(second.metadata_json.get("duplicate"))
            self.assertEqual(len(storage._messages), 2)

    def test_workflow_tracks_owner_summary_and_runs(self):
        with TemporaryDirectory() as tmp:
            storage = _FakeStorageWithTracking()
            owner_gateway = _FakeOwnerGateway()
            memory_store = _FakeMemoryStore(Path(tmp))
            workflow = Workflow(
                config=None,  # type: ignore[arg-type]
                profile=_FakeProfile(),
                storage=storage,
                orchestrator=_FakeOrchestrator(),
                memory_store=memory_store,
                knowledge_loader=_FakeKnowledgeLoader(),
                owner_gateway=owner_gateway,
                policy=DefaultPolicyEngine(),
            )

            event = CustomerEvent(
                gateway="webhook",
                external_customer_id="ext_2",
                external_conversation_id="conv_2",
                message_text="I want urgent help",
            )
            result = workflow.run(event)

            self.assertEqual(storage.owner_summaries, 1)
            self.assertGreater(len(storage.agent_runs), 0)
            self.assertEqual(len(owner_gateway.delivered), 1)
            self.assertEqual(len(result.metadata_json.get("owner_summary_ids", [])), 1)


if __name__ == "__main__":
    unittest.main()
