# Roadmap

This roadmap is intentionally staged. Wasila should first prove a useful local customer workflow before growing into a broader platform.

## Stage 0: Docs-First MVP Definition

Status: in progress.

Goals:

- Define product promise and non-goals.
- Document the MVP profile and architecture.
- Keep CrewAI as the default orchestration core.
- Define profile, gateway, provider, storage, and owner-loop boundaries.

## Stage 1: Local CLI MVP

Goals:

- Create the Python package and CLI.
- Implement `wasila init startup_saas`.
- Create the initial SQLite schema.
- Create customer memory files at `data/customers/{customer_id}/customer.md`.
- Implement the generic customer webhook gateway.
- Implement the generic owner webhook gateway.
- Implement the CLI customer sandbox.
- Implement the CLI owner sandbox.
- Implement the first CrewAI runner.
- Implement MVP-safe skills and skill execution tracing.
- Implement MVP operational policies for handoff, memory updates, and owner notifications.
- Implement basic idempotency for repeated events.
- Store messages, tickets, ticket events, agent runs, and owner summaries.

Exit criteria:

- A local user can run a daemon, simulate a customer conversation from the CLI, inspect owner notifications from the CLI, inspect a customer, and inspect tickets.

## Stage 2: Gateway Expansion

Goals:

- Add Telegram as a customer gateway.
- Add WhatsApp as a customer gateway.
- Add OpenClaw as an owner gateway.
- Add Hermes as an owner gateway.
- Keep customer gateway configuration separate from owner gateway configuration.

Exit criteria:

- A business can receive customer conversations through one gateway while sending owner summaries through another gateway.

## Stage 3: Profile Expansion

Goals:

- Add `agency`.
- Add `ecommerce`.
- Add `education`.
- Add `appointment_service`.
- Document each profile's default agents, tasks, ticket rules, memory rules, and owner escalation rules.

Exit criteria:

- New profiles can be added without changing gateway or storage internals.

## Stage 4: API Runtime

Goals:

- Add an HTTP API for external systems.
- Expose customer, ticket, message, owner summary, and agent run endpoints.
- Keep the API compatible with the CLI daemon's storage and orchestration model.

Exit criteria:

- External systems can integrate with Wasila without shelling out to the CLI.

## Stage 5: Web-Based Daemon Console

Goals:

- Add a web console for the daemon.
- Inspect customers, tickets, messages, agent runs, memory files, and owner summaries.
- Add simple operational controls such as pause profile, retry run, and view gateway health.

Exit criteria:

- A small operator team can monitor Wasila without reading SQLite manually.

## Stage 6: Production Hardening

Goals:

- Add queue workers.
- Add better retry and idempotency behavior.
- Add observability hooks.
- Add deployment examples.
- Add permission and approval workflows.

Exit criteria:

- Wasila can support more serious production pilots while keeping the local-first developer experience.
