from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Any
from uuid import uuid4

from wasila import __version__
from wasila.app import load_project
from wasila.config.defaults import default_config
from wasila.config.layers import load_config_with_layers
from wasila.config.models import (
    AssistantConfig,
    GatewayConfig,
    ProjectConfig,
    ProviderSettings,
)
from wasila.config.toml_io import dump_config, load_config
from wasila.core.contracts import CustomerEvent
from wasila.core.workflow import _build_dedup_event_id
from wasila.gateways import build_customer_gateway
from wasila.gateways.webhook import WebhookDaemon
from wasila.storage import SqliteStorage
from wasila.storage.file import CustomerMarkdownStore

CONFIG_PATH = Path(".wasila") / "config.toml"

KNOWLEDGE_FILES = {
    "business.md": "# Business\n\n## Overview\n\n## Audience\n\n## Brand Voice\n\n## Contact Rules\n",
    "products.md": "# Products\n\n## Catalog\n\n## Features\n\n## Pricing Notes\n\n## Limitations\n",
    "policies.md": "# Policies\n\n## Billing\n\n## Refunds\n\n## Privacy\n\n## Escalation\n\n## Approval Rules\n",
    "support.md": "# Support\n\n## Common Questions\n\n## Troubleshooting\n\n## Known Issues\n\n## Boundaries\n",
    "owner.md": "# Owner Preferences\n\n## Summary Format\n\n## Escalation Preferences\n\n## Approval Requirements\n\n## Sensitive Topics\n",
}


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wasila", description="Customer AI orchestration kit.")
    parser.add_argument("--version", action="version", version=f"wasila {__version__}")
    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_PATH,
        help="Path to .wasila/config.toml",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize a Wasila project.")
    init_parser.add_argument("profile", nargs="?", default="startup_saas")
    init_parser.add_argument("--name", default="my-customer-ai")
    init_parser.add_argument("--force", action="store_true", help="Overwrite .wasila/config.toml if it exists.")
    init_parser.set_defaults(func=handle_init)

    kb_parser = subparsers.add_parser("kb", help="Manage business knowledge files.")
    kb_subparsers = kb_parser.add_subparsers(dest="kb_command", required=True)
    kb_init = kb_subparsers.add_parser("init", help="Create starter business knowledge files.")
    kb_init.add_argument("--force", action="store_true", help="Overwrite existing knowledge files.")
    kb_init.set_defaults(func=handle_kb_init)

    provider_parser = subparsers.add_parser("provider", help="Manage LLM provider config.")
    provider_sub = provider_parser.add_subparsers(dest="provider_command", required=True)
    provider_set = provider_sub.add_parser("set", help="Set provider configuration.")
    provider_set.add_argument("type", choices=["openai-compatible"])
    provider_set.add_argument("--base-url", required=True)
    provider_set.add_argument("--model", required=True)
    provider_set.add_argument("--api-key-env", required=True)
    provider_set.set_defaults(func=handle_provider_set)

    gateway_parser = subparsers.add_parser("gateway", help="Manage gateway config.")
    gateway_sub = gateway_parser.add_subparsers(dest="gateway_command", required=True)
    gateway_add = gateway_sub.add_parser("add", help="Set gateway type and metadata.")
    gateway_add.add_argument("role", choices=["customer", "owner"])
    gateway_add.add_argument("type", choices=["webhook", "openclaw", "hermes"])
    gateway_add.add_argument("--metadata", action="append", default=[], help="KEY=VALUE metadata")
    gateway_add.set_defaults(func=handle_gateway_add)

    assistant_parser = subparsers.add_parser(
        "assistant",
        help="Manage private assistant adapters.",
    )
    assistant_sub = assistant_parser.add_subparsers(
        dest="assistant_command",
        required=True,
    )
    assistant_add = assistant_sub.add_parser(
        "add",
        help="Add a private assistant adapter.",
    )
    assistant_add_sub = assistant_add.add_subparsers(
        dest="assistant_type",
        required=True,
    )
    assistant_add_cli = assistant_add_sub.add_parser(
        "cli",
        help="Add a CLI adapter.",
    )
    assistant_add_cli.add_argument("--name", required=True)
    assistant_add_cli.add_argument("--command", required=True)
    assistant_add_cli.set_defaults(func=handle_assistant_add_cli)
    assistant_list = assistant_sub.add_parser(
        "list",
        help="List private assistant adapters.",
    )
    assistant_list.set_defaults(func=handle_assistant_list)

    daemon_parser = subparsers.add_parser("daemon", help="Start the local event daemon.")
    daemon_sub = daemon_parser.add_subparsers(dest="daemon_command", required=True)
    daemon_start = daemon_sub.add_parser("start", help="Start webhook daemon.")
    daemon_start.add_argument("--host", default="127.0.0.1")
    daemon_start.add_argument("--port", type=int, default=8000)
    daemon_start.add_argument("--customer-gateway", default=None, help="Override runtime customer gateway type.")
    daemon_start.add_argument("--owner-gateway", default=None, help="Override runtime owner gateway type.")
    daemon_start.set_defaults(func=handle_daemon_start)

    sandbox_parser = subparsers.add_parser("sandbox", help="Run sandbox sessions.")
    sandbox_sub = sandbox_parser.add_subparsers(dest="sandbox_command", required=True)
    sandbox_customer = sandbox_sub.add_parser("customer", help="Interactive customer session.")
    sandbox_customer.add_argument("--customer-id", help="Existing customer id.")
    sandbox_customer.add_argument("--new", help="New customer display name.")
    sandbox_customer.set_defaults(func=handle_sandbox_customer)
    sandbox_owner = sandbox_sub.add_parser("owner", help="Inspect latest owner notifications.")
    sandbox_owner.add_argument("--limit", type=int, default=10)
    sandbox_owner.set_defaults(func=handle_sandbox_owner)

    customer_parser = subparsers.add_parser("customer", help="Inspect a customer.")
    customer_parser.add_argument("customer_id", help="Customer ID")
    customer_parser.set_defaults(func=handle_customer_inspect)

    ticket_parser = subparsers.add_parser("ticket", help="Inspect tickets.")
    ticket_sub = ticket_parser.add_subparsers(dest="ticket_command", required=True)
    ticket_list = ticket_sub.add_parser("list", help="List tickets.")
    ticket_list.add_argument("--status", default=None)
    ticket_list.set_defaults(func=handle_ticket_list)

    return parser


def handle_init(args: argparse.Namespace) -> None:
    config = default_config(project_name=args.name, profile=args.profile)
    args.config.parent.mkdir(parents=True, exist_ok=True)
    runtime = config.runtime
    Path(runtime.customer_memory_dir).mkdir(parents=True, exist_ok=True)
    Path(runtime.knowledge_dir).mkdir(parents=True, exist_ok=True)
    Path(runtime.database_path).parent.mkdir(parents=True, exist_ok=True)

    if args.config.exists() and not args.force:
        print(f"Config already exists: {args.config}")
    else:
        args.config.write_text(dump_config(config), encoding="utf-8")
        print(f"Created config: {args.config}")

    storage = SqliteStorage(config.runtime)
    storage.initialize()
    print(f"Initialized database: {config.runtime.database_path}")
    print("Next: wasila kb init")


def handle_kb_init(args: argparse.Namespace) -> None:
    knowledge_dir = Path("knowledge")
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    skipped: list[Path] = []

    for filename, body in KNOWLEDGE_FILES.items():
        path = knowledge_dir / filename
        if path.exists() and not args.force:
            skipped.append(path)
            continue
        path.write_text(body, encoding="utf-8")
        created.append(path)

    for path in created:
        print(f"Created knowledge file: {path}")
    for path in skipped:
        print(f"Skipped existing knowledge file: {path}")


def handle_provider_set(args: argparse.Namespace) -> None:
    config = _load_or_default(args.config)
    config.provider = ProviderSettings(
        type=args.type,
        base_url=args.base_url,
        model=args.model,
        api_key_env=args.api_key_env,
    )
    _write_config(args.config, config)
    print(f"Updated provider in {args.config}")


def handle_gateway_add(args: argparse.Namespace) -> None:
    config = _load_or_default(args.config)
    metadata = _parse_metadata_args(args.metadata)
    if args.role == "customer" and args.type not in {"webhook"}:
        raise SystemExit("customer gateway currently only supports webhook in Stage 1")
    if args.role == "customer":
        config.customer_gateway = GatewayConfig(
            type=args.type,
            metadata={**config.customer_gateway.metadata, **metadata},
        )
    else:
        config.owner_gateway = GatewayConfig(
            type=args.type,
            metadata={**config.owner_gateway.metadata, **metadata},
        )
    _write_config(args.config, config)
    print(f"Updated {args.role} gateway in {args.config}")


def handle_assistant_add_cli(args: argparse.Namespace) -> None:
    if not _is_toml_bare_key(args.name):
        raise SystemExit("assistant name must be ASCII letters, numbers, _ or -")

    try:
        command = shlex.split(args.command)
    except ValueError as exc:
        raise SystemExit(f"invalid assistant command: {exc}") from exc
    if not command:
        raise SystemExit("assistant command must not be empty")
    if _command_has_secret(command):
        raise SystemExit("assistant command must not contain secrets")

    config = _load_or_default(args.config)
    config.assistants[args.name] = AssistantConfig(type="cli", command=command)
    _write_config(args.config, config)
    print(f"Updated assistant {args.name} in {args.config}")


def handle_assistant_list(args: argparse.Namespace) -> None:
    config = _load_or_default(args.config)
    if not config.assistants:
        print("No assistants configured.")
        return

    for name, assistant in sorted(config.assistants.items()):
        command = shlex.join(assistant.command)
        print(f"{name}\t{assistant.type}\t{command}")


def _is_toml_bare_key(value: str) -> bool:
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
    return bool(value) and all(char in allowed for char in value)


def _command_has_secret(command: list[str]) -> bool:
    secret_words = {"api_key", "apikey", "password", "secret", "token"}
    for arg in command:
        _, value = arg.split("=", 1) if "=" in arg else ("", arg)
        if value.startswith(("-", "$")):
            continue
        if "/" in value or "\\" in value or "." in value:
            continue
        normalized = "".join(
            char for char in value.lower() if char.isalnum() or char == "_"
        )
        if any(word in normalized for word in secret_words):
            return True
    return False


def handle_daemon_start(args: argparse.Namespace) -> None:
    config, _, workflow = load_project(
        config_path=args.config,
        customer_gateway_runtime=args.customer_gateway,
        owner_gateway_runtime=args.owner_gateway,
    )
    gateway = build_customer_gateway(
        config.customer_gateway.type,
        config.customer_gateway.metadata,
    )

    def process(event_payload: dict[str, Any]) -> dict[str, Any]:
        event = gateway.normalize(event_payload)
        result = workflow.run(event)
        return {
            "customer_response": result.customer_response,
            "metadata": result.metadata_json,
            "customer_id": event.customer_id,
            "gateway": event.gateway,
        }

    daemon = WebhookDaemon(handler=process, gateway=gateway, host=args.host, port=args.port)
    daemon.start()


def handle_sandbox_customer(args: argparse.Namespace) -> None:
    _, _, workflow = load_project(config_path=args.config)
    conversation_id = f"sbx_{uuid4().hex[:10]}"
    customer_id = args.customer_id
    ext_customer = customer_id or f"sbx_{uuid4().hex[:8]}"
    display_name = args.new
    print("Customer sandbox started. Press Enter on empty input to exit.")

    while True:
        text = input("customer> ").strip()
        if not text:
            break

        event = CustomerEvent(
            gateway="sandbox",
            external_conversation_id=conversation_id,
            external_customer_id=ext_customer,
            message_text=text,
            customer_id=customer_id,
            metadata_json={"display_name": display_name, "name": display_name},
        )
        event.id = _build_dedup_event_id(event)
        result = workflow.run(event)

        if customer_id is None:
            customer_id = result.metadata_json.get("customer_id") or event.customer_id
            if customer_id:
                ext_customer = customer_id
        if customer_id:
            event.customer_id = customer_id

        ticket_ref = ", ".join(result.metadata_json.get("ticket_ids", [])) or "none"
        owner_ref = ", ".join(result.metadata_json.get("owner_summary_ids", [])) or "none"
        print(f"\nassistant> {result.customer_response}")
        print(f"customer_id={event.customer_id} tickets={ticket_ref} owner_notifications={owner_ref}")
        print("-" * 40)


def handle_sandbox_owner(args: argparse.Namespace) -> None:
    config, _, _ = load_project(config_path=args.config)
    storage = SqliteStorage(config.runtime)
    storage.initialize()
    summaries = storage.list_owner_summaries(limit=args.limit)

    if not summaries:
        print("No owner summaries yet.")
        return

    for summary in summaries:
        print(
            f"[{summary.get('risk_level')}] ticket={summary.get('ticket_id')} customer={summary.get('customer_id')} id={summary.get('id')}"
        )
        print(f"  {summary.get('summary')}")
        print(f"  action={summary.get('recommended_action')}")


def handle_customer_inspect(args: argparse.Namespace) -> None:
    config = load_config_with_layers(args.config, cli_overrides=None)
    storage = SqliteStorage(config.runtime)
    storage.initialize()
    customer = storage.get_customer(args.customer_id)
    if not customer:
        print(f"Customer not found: {args.customer_id}")
        return

    memory_store = CustomerMarkdownStore(config.runtime.customer_memory_dir)
    memory_path = memory_store.memory_path(args.customer_id)
    memory = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""

    payload = {
        "customer": customer,
        "open_tickets": storage.get_open_tickets_for_context(args.customer_id),
        "recent_messages": storage.list_recent_messages(args.customer_id),
        "memory": memory.strip()[:2000],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def handle_ticket_list(args: argparse.Namespace) -> None:
    config = load_config_with_layers(args.config, cli_overrides=None)
    storage = SqliteStorage(config.runtime)
    storage.initialize()
    tickets = storage.list_tickets(status=args.status)
    if not tickets:
        print("No tickets found.")
        return

    print("ticket_id | customer_id | status | priority | title")
    print("-" * 80)
    for ticket in tickets:
        print(f"{ticket['id']} | {ticket['customer_id']} | {ticket['status']} | {ticket['priority']} | {ticket['title']}")


def _load_or_default(config_path: Path) -> ProjectConfig:
    if config_path.exists():
        return load_config(config_path)
    return default_config()


def _parse_metadata_args(values: list[str]) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for item in values:
        if "=" not in item:
            raise SystemExit(f"Metadata must be KEY=VALUE, got: {item}")
        key, value = item.split("=", 1)
        metadata[key.strip()] = value.strip()
    return metadata


def _write_config(config_path: Path, config: ProjectConfig) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(dump_config(config), encoding="utf-8")
