from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

from wasila.config.models import RuntimeSettings
from wasila.core.contracts import AgentRun, OwnerNotification, SkillResult, TicketUpdate, utc_now_iso
from wasila.core.ports import Storage


SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customers (
  id TEXT PRIMARY KEY,
  display_name TEXT,
  primary_channel TEXT,
  external_refs_json TEXT NOT NULL DEFAULT '{}',
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
  id TEXT PRIMARY KEY,
  event_id TEXT,
  customer_id TEXT,
  ticket_id TEXT,
  gateway TEXT NOT NULL,
  direction TEXT NOT NULL,
  body TEXT NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(gateway, event_id)
);

CREATE TABLE IF NOT EXISTS tickets (
  id TEXT PRIMARY KEY,
  customer_id TEXT NOT NULL,
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open',
  priority TEXT NOT NULL DEFAULT 'medium',
  owner_agent TEXT,
  summary TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ticket_events (
  id TEXT PRIMARY KEY,
  ticket_id TEXT NOT NULL,
  actor_type TEXT NOT NULL,
  actor_name TEXT NOT NULL,
  event_type TEXT NOT NULL,
  body TEXT NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_runs (
  id TEXT PRIMARY KEY,
  customer_id TEXT,
  ticket_id TEXT,
  profile TEXT NOT NULL,
  agent_name TEXT NOT NULL,
  task_name TEXT NOT NULL,
  status TEXT NOT NULL,
  input_json TEXT NOT NULL DEFAULT '{}',
  output_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS owner_summaries (
  id TEXT PRIMARY KEY,
  customer_id TEXT NOT NULL,
  ticket_id TEXT,
  summary TEXT NOT NULL,
  risk_level TEXT NOT NULL DEFAULT 'low',
  recommended_action TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS skill_executions (
  id TEXT PRIMARY KEY,
  customer_id TEXT,
  ticket_id TEXT,
  agent_run_id TEXT,
  skill_name TEXT NOT NULL,
  execution_level TEXT NOT NULL,
  approval_required INTEGER NOT NULL DEFAULT 0,
  approval_status TEXT NOT NULL DEFAULT 'not_required',
  input_json TEXT NOT NULL DEFAULT '{}',
  output_json TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL,
  error TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO schema_migrations (version) VALUES (1);
"""


class SqliteStorage(Storage):
    def __init__(self, runtime: RuntimeSettings | str) -> None:
        if isinstance(runtime, RuntimeSettings):
            database_path = Path(runtime.database_path)
        else:
            database_path = Path(runtime)
        self.database_path = database_path

    @contextmanager
    def _connect(self):
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    @staticmethod
    def _rows(connection: sqlite3.Connection, query: str, *params: Any) -> list[dict[str, Any]]:
        rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _row(connection: sqlite3.Connection, query: str, *params: Any) -> dict[str, Any] | None:
        row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    @staticmethod
    def _json_load(raw: str | None, default: Any | None = None) -> Any:
        if not raw:
            return {} if default is None else default
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {} if default is None else default

    @classmethod
    def _normalize_row(cls, row: dict[str, Any] | None) -> dict[str, Any] | None:
        if not row:
            return None

        if "external_refs_json" in row and isinstance(row.get("external_refs_json"), str):
            row["external_refs_json"] = cls._json_load(row["external_refs_json"])
        if "metadata_json" in row and isinstance(row.get("metadata_json"), str):
            row["metadata_json"] = cls._json_load(row["metadata_json"])
        if "input_json" in row and isinstance(row.get("input_json"), str):
            row["input_json"] = cls._json_load(row["input_json"])
        if "output_json" in row and isinstance(row.get("output_json"), str):
            row["output_json"] = cls._json_load(row["output_json"])
        return row

    @classmethod
    def _normalize_rows(cls, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [cls._normalize_row(row) or {} for row in rows]

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(SCHEMA)
            connection.commit()

    def find_message_by_event(self, gateway: str, event_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = self._row(
                connection,
                "SELECT * FROM messages WHERE gateway = ? AND event_id = ? ORDER BY created_at ASC LIMIT 1",
                gateway,
                event_id,
            )
        return self._normalize_row(row)

    def ensure_customer(
        self,
        *,
        customer_id_hint: str | None,
        external_customer_id: str,
        gateway: str,
        external_conversation_id: str | None = None,
        display_name: str | None = None,
    ) -> str:
        if customer_id_hint:
            existing = self.get_customer(customer_id_hint)
            if existing:
                self._upsert_external_ref(
                    customer_id_hint,
                    gateway,
                    external_customer_id,
                    external_conversation_id,
                )
                return customer_id_hint

        if external_customer_id:
            with self._connect() as connection:
                rows = self._rows(connection, "SELECT id, external_refs_json FROM customers")
            for row in self._normalize_rows(rows):
                refs = row.get("external_refs_json", {})
                existing = refs.get(gateway)
                if isinstance(existing, dict) and existing.get("customer_id") == external_customer_id:
                    customer_id = row["id"]
                    self._upsert_external_ref(
                        customer_id,
                        gateway,
                        external_customer_id,
                        external_conversation_id,
                    )
                    return customer_id

        customer_id = _new_customer_id(external_customer_id, display_name)
        created = utc_now_iso()
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO customers (id, display_name, primary_channel, external_refs_json, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    customer_id,
                    display_name,
                    gateway,
                    json.dumps(
                        {gateway: {"customer_id": external_customer_id, "conversation_id": external_conversation_id}},
                    ),
                    created,
                    created,
                ),
            )
            connection.commit()
        return customer_id

    def _upsert_external_ref(
        self,
        customer_id: str,
        gateway: str,
        external_customer_id: str,
        external_conversation_id: str | None,
    ) -> None:
        customer = self.get_customer(customer_id)
        if not customer:
            return
        refs = customer.get("external_refs_json", {})
        if not isinstance(refs, dict):
            refs = {}
        refs[gateway] = {"customer_id": external_customer_id, "conversation_id": external_conversation_id}
        with self._connect() as connection:
            connection.execute(
                "UPDATE customers SET external_refs_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (json.dumps(refs), customer_id),
            )
            connection.commit()

    def get_customer(self, customer_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = self._row(connection, "SELECT * FROM customers WHERE id = ?", customer_id)
        return self._normalize_row(row)

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
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO messages (id, customer_id, ticket_id, gateway, event_id, direction, body, metadata_json)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    message_id,
                    customer_id,
                    ticket_id,
                    gateway,
                    event_id,
                    direction,
                    body,
                    json.dumps(metadata_json),
                ),
            )
            connection.commit()

    def update_message_metadata(self, message_id: str, metadata_json: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE messages SET metadata_json = ? WHERE id = ?",
                (json.dumps(metadata_json), message_id),
            )
            connection.commit()

    def list_open_tickets(self, customer_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = self._rows(
                connection,
                "SELECT * FROM tickets WHERE customer_id = ? AND status NOT IN ('resolved', 'closed') ORDER BY updated_at DESC",
                customer_id,
            )
        return self._normalize_rows(rows)

    def get_open_tickets_for_context(self, customer_id: str) -> list[dict[str, Any]]:
        return self.list_open_tickets(customer_id)

    def list_tickets(self, status: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM tickets"
        params: tuple[Any, ...] = tuple()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY updated_at DESC"
        with self._connect() as connection:
            rows = self._rows(connection, query, *params)
        return self._normalize_rows(rows)

    def list_recent_messages(self, customer_id: str, limit: int = 10) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = self._rows(
                connection,
                "SELECT * FROM messages WHERE customer_id = ? ORDER BY created_at DESC LIMIT ?",
                customer_id,
                limit,
            )
        return self._normalize_rows(rows)

    def apply_ticket_update(self, customer_id: str, update: TicketUpdate) -> str:
        ticket_id = update.ticket_id or ""
        action = update.action
        if action == "create":
            ticket_id = _new_id("tick")
            self._create_ticket(
                customer_id=customer_id,
                title=update.title or "Customer support follow-up",
                status=update.status,
                priority=update.priority,
                summary=update.summary,
                metadata_json={"status_source": "orchestration", **update.metadata_json},
            )
            self.add_ticket_event(
                ticket_id=ticket_id,
                actor_type="assistant",
                actor_name="workflow",
                event_type="created",
                body=f"Ticket created: {update.summary}",
                metadata_json={"status": update.status, "priority": update.priority},
            )
            return ticket_id

        if not ticket_id:
            open_tickets = self.list_open_tickets(customer_id)
            if not open_tickets:
                ticket_id = _new_id("tick")
                self._create_ticket(
                    customer_id=customer_id,
                    title=update.title or "Customer support follow-up",
                    status="open",
                    priority=update.priority,
                    summary=update.summary,
                    metadata_json={"status_source": "orchestration", **update.metadata_json},
                )
            else:
                ticket_id = open_tickets[0]["id"]

        if action == "update":
            self._update_ticket(
                ticket_id=ticket_id,
                status=update.status,
                priority=update.priority,
                summary=update.summary,
            )
            self.add_ticket_event(
                ticket_id=ticket_id,
                actor_type="assistant",
                actor_name="workflow",
                event_type="status_changed",
                body=update.summary or "Ticket updated.",
                metadata_json={"status": update.status, "priority": update.priority},
            )
        elif action == "comment":
            self.add_ticket_event(
                ticket_id=ticket_id,
                actor_type="assistant",
                actor_name="workflow",
                event_type="agent_comment",
                body=update.summary,
                metadata_json={"priority": update.priority},
            )
        elif action == "close":
            self._update_ticket(ticket_id=ticket_id, status="closed", summary=update.summary)
            self.add_ticket_event(
                ticket_id=ticket_id,
                actor_type="assistant",
                actor_name="workflow",
                event_type="status_changed",
                body=update.summary or "Ticket closed by workflow",
                metadata_json={"status": "closed"},
            )
        return ticket_id

    def _create_ticket(
        self,
        customer_id: str,
        title: str,
        status: str,
        priority: str,
        summary: str,
        metadata_json: dict[str, Any] | None = None,
        owner_agent: str | None = None,
    ) -> str:
        ticket_id = _new_id("tick")
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO tickets (id, customer_id, title, status, priority, owner_agent, summary, metadata_json)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    ticket_id,
                    customer_id,
                    title,
                    status,
                    priority,
                    owner_agent,
                    summary,
                    json.dumps(metadata_json or {}),
                ),
            )
            connection.commit()
        return ticket_id

    def _update_ticket(
        self,
        ticket_id: str,
        status: str | None = None,
        priority: str | None = None,
        summary: str | None = None,
        owner_agent: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> None:
        updates: list[str] = []
        values: list[Any] = []
        if status is not None:
            updates.append("status = ?")
            values.append(status)
        if priority is not None:
            updates.append("priority = ?")
            values.append(priority)
        if summary is not None:
            updates.append("summary = ?")
            values.append(summary)
        if owner_agent is not None:
            updates.append("owner_agent = ?")
            values.append(owner_agent)
        if metadata_json is not None:
            updates.append("metadata_json = ?")
            values.append(json.dumps(metadata_json))
        updates.append("updated_at = CURRENT_TIMESTAMP")

        if not updates:
            return

        with self._connect() as connection:
            connection.execute(
                f"UPDATE tickets SET {', '.join(updates)} WHERE id = ?",
                (*values, ticket_id),
            )
            connection.commit()

    def add_ticket_event(
        self,
        *,
        ticket_id: str,
        actor_type: str,
        actor_name: str,
        event_type: str,
        body: str,
        metadata_json: dict[str, Any] | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO ticket_events (id, ticket_id, actor_type, actor_name, event_type, body, metadata_json)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    _new_id("tkevt"),
                    ticket_id,
                    actor_type,
                    actor_name,
                    event_type,
                    body,
                    json.dumps(metadata_json or {}),
                ),
            )
            connection.commit()

    def create_agent_run(self, run: AgentRun) -> str:
        run_id = run.id or _new_id("run")
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO agent_runs (id, customer_id, ticket_id, profile, agent_name, task_name, status, input_json, output_json)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    run.customer_id,
                    run.ticket_id,
                    run.profile,
                    run.agent_name,
                    run.task_name,
                    run.status,
                    json.dumps(run.input_json),
                    json.dumps(run.output_json),
                ),
            )
            connection.commit()
        return run_id

    def create_skill_execution(self, result: SkillResult) -> str:
        execution_id = result.id or _new_id("skex")
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO skill_executions (id, customer_id, ticket_id, agent_run_id, skill_name, execution_level, approval_required, approval_status, input_json, output_json, status, error)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    execution_id,
                    result.metadata_json.get("customer_id"),
                    result.metadata_json.get("ticket_id"),
                    result.metadata_json.get("agent_run_id"),
                    result.skill_name,
                    result.metadata_json.get("execution_level", "write"),
                    int(bool(result.approval_status in {"pending"})),
                    result.approval_status,
                    json.dumps(result.input_json),
                    json.dumps(result.output_json),
                    result.status,
                    result.error,
                ),
            )
            connection.commit()
        return execution_id

    def create_owner_summary(self, notification: OwnerNotification) -> str:
        summary_id = notification.id or _new_id("own")
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO owner_summaries (id, customer_id, ticket_id, summary, risk_level, recommended_action)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    summary_id,
                    notification.customer_id,
                    notification.ticket_id,
                    notification.summary,
                    notification.risk_level,
                    notification.recommended_action,
                ),
            )
            connection.commit()
        return summary_id

    def list_owner_summaries(self, customer_id: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        query = "SELECT * FROM owner_summaries"
        params: tuple[Any, ...] = tuple()
        if customer_id:
            query += " WHERE customer_id = ?"
            params = (customer_id,)
        query += " ORDER BY created_at DESC LIMIT ?"
        params = (*params, limit)
        with self._connect() as connection:
            rows = self._rows(connection, query, *params)
        return self._normalize_rows(rows)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def _slugify(value: str | None) -> str:
    if not value:
        return "customer"
    safe = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower()).strip("_")
    return safe[:28] if safe else "customer"


def _new_customer_id(external_customer_id: str, display_name: str | None) -> str:
    return f"cust_{_slugify(display_name or external_customer_id)}_{uuid4().hex[:6]}"
