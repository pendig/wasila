# Contributing

Thanks for helping improve Wasila.

Wasila is early and MVP-focused. Contributions should keep the first customer workflow simple, inspectable, and easy to run locally.

## Good First Contribution Areas

- Documentation improvements.
- CLI help text.
- SQLite migrations.
- Sandbox behavior.
- Customer gateway adapters.
- Owner gateway adapters.
- Profile definitions.
- Smoke tests.

## Contribution Principles

- Keep changes small and easy to review.
- Update docs when behavior changes.
- Avoid committing secrets, private URLs, or real customer data.
- Prefer local-first behavior for MVP features.
- Keep customer gateways separate from owner gateways.
- Preserve CrewAI as the default orchestration core unless an ADR changes that decision.

## Development Status

The project is currently in docs-first MVP planning. The implementation scaffold is expected to follow the plan in `docs/10-mvp-implementation-plan.md`.
