from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from wasila import __version__
from wasila.config.defaults import default_config
from wasila.config.toml_io import dump_config

CONFIG_DIR = ".wasila"
CONFIG_PATH = Path(CONFIG_DIR) / "config.toml"

KNOWLEDGE_FILES = {
    "business.md": "# Business\n\n## Overview\n\n## Audience\n\n## Brand Voice\n\n## Contact Rules\n",
    "products.md": "# Products\n\n## Catalog\n\n## Features\n\n## Pricing Notes\n\n## Limitations\n",
    "policies.md": "# Policies\n\n## Billing\n\n## Refunds\n\n## Privacy\n\n## Escalation\n\n## Approval Rules\n",
    "support.md": "# Support\n\n## Common Questions\n\n## Troubleshooting\n\n## Known Issues\n\n## Boundaries\n",
    "owner.md": "# Owner Preferences\n\n## Summary Format\n\n## Escalation Preferences\n\n## Approval Requirements\n\n## Sensitive Topics\n",
}

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


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wasila", description="Customer AI orchestration kit.")
    parser.add_argument("--version", action="version", version=f"wasila {__version__}")
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

    return parser


def handle_init(args: argparse.Namespace) -> None:
    if args.profile != "startup_saas":
        raise SystemExit(f"Unsupported MVP profile: {args.profile}")

    config = default_config(project_name=args.name, profile=args.profile)
    Path(CONFIG_DIR).mkdir(exist_ok=True)
    Path(config.runtime.customer_memory_dir).mkdir(parents=True, exist_ok=True)
    Path(config.runtime.knowledge_dir).mkdir(parents=True, exist_ok=True)
    Path(config.runtime.database_path).parent.mkdir(parents=True, exist_ok=True)

    if CONFIG_PATH.exists() and not args.force:
        print(f"Config already exists: {CONFIG_PATH}")
    else:
        CONFIG_PATH.write_text(dump_config(config), encoding="utf-8")
        print(f"Created config: {CONFIG_PATH}")

    initialize_sqlite(Path(config.runtime.database_path))
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


def initialize_sqlite(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA)

