# ADR 0001: Use CrewAI As The Default Orchestration Core

## Status

Accepted for MVP.

## Context

Wasila needs a practical way to model customer-facing AI teams with multiple roles:

- Front office.
- Ticket manager.
- Domain expert.
- Owner agent.

The project also needs a path toward more controlled workflows as it grows.

CrewAI provides a Python-native framework for agent crews and flows. It fits the first version of Wasila because the product concept is naturally multi-agent and profile-driven.

## Decision

Wasila will use CrewAI as the default orchestration core for the MVP.

Wasila will still define its own product-level contracts:

- `CustomerEvent`
- `CustomerContext`
- `OrchestrationResult`
- `TicketUpdate`
- `MemoryUpdate`
- `OwnerNotification`

This keeps gateways, storage, CLI, and profile docs understandable without requiring every module to depend directly on CrewAI internals.

## Consequences

Positive:

- Faster MVP implementation.
- Natural mapping between Wasila profiles and CrewAI agents/tasks.
- Easier experimentation with multi-agent customer workflows.
- Clear default for contributors.

Tradeoffs:

- The first orchestration implementation depends on CrewAI behavior and API stability.
- Wasila needs a thin boundary to avoid leaking CrewAI details into every module.
- Tests should cover Wasila contracts, not only CrewAI execution.

## Follow-Up

After the MVP works, evaluate whether CrewAI Flows should power more deterministic ticket and owner escalation paths.
