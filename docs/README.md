# Wasila Documentation

This directory is the product and implementation guide for Wasila.

Wasila is currently in docs-first MVP planning. The first implementation target is Stage 1: Local CLI MVP.

## Start Here

Read these first:

- `01-product-brief.md`: product name, promise, target user, and non-goals.
- `02-mvp-scope.md`: first profile, first gateways, first runtime, and MVP boundaries.
- `03-architecture.md`: high-level module layout and contracts.
- `22-architecture-boundaries.md`: modular boundaries for maintainable implementation.
- `23-crewai-alignment.md`: how Wasila maps to CrewAI features instead of replacing them.
- `10-mvp-implementation-plan.md`: phase-by-phase implementation checklist.

## Core Contracts

Use these before writing code:

- `05-data-model.md`: SQLite, customer memory, business knowledge, and skill execution storage.
- `11-configuration.md`: local config, runtime paths, provider config, and gateway config.
- `12-event-contracts.md`: CustomerEvent, CustomerContext, OrchestrationResult, OwnerNotification, SkillCall, and SkillResult.
- `20-idempotency.md`: stable event IDs and duplicate handling.

## Runtime Behavior

Use these to shape agent behavior:

- `09-sandbox.md`: CLI sandbox for customer and owner flows.
- `14-knowledge-base.md`: business knowledge base layout and loading strategy.
- `16-operational-policies.md`: handoff, memory update, owner notification, and skill execution rules.
- `18-smoke-scenarios.md`: MVP validation scenarios.
- `19-observability.md`: CLI inspection and tracing goals.
- `21-skills-and-execution.md`: skill registry, execution levels, approvals, and traces.

## Extensibility

Use these when adding new capabilities:

- `04-profiles.md`: MVP profile and future profile candidates.
- `17-profile-template.md`: profile file structure and required profile behavior.
- `15-provider-configuration.md`: OpenAI-compatible provider configuration.
- `07-roadmap.md`: staged roadmap after the local CLI MVP.

## Project Hygiene

Use these for OSS readiness:

- `08-open-source.md`: contribution model, extension points, secrets policy, and future repo files.
- `13-security-and-privacy.md`: MVP security and privacy posture.
- `adr/0001-use-crewai-as-default-core.md`: why CrewAI is the default orchestration core.

## GitHub Backlog

The implementation backlog is tracked in GitHub issues and milestones:

- Stage 0: Docs-First MVP Definition.
- Stage 1: Local CLI MVP.
- Stage 2: Gateway Expansion.
- Stage 3: Profile Expansion.
- Stage 4: API Runtime.
- Stage 5: Web-Based Daemon Console.
- Stage 6: Production Hardening.

Backlog: https://github.com/pendig/wasila/issues
Milestones: https://github.com/pendig/wasila/milestones
