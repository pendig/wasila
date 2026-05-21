# MVP Implementation Plan

This plan keeps the first implementation small enough to finish while preserving the core Wasila architecture.

## Phase 1: Project Scaffold

Goals:

- Create Python package structure.
- Define core ports and adapters boundaries.
- Add registry scaffolding for profiles, gateways, providers, skills, and runners.
- Add CLI entrypoint.
- Add basic local config loading.
- Add config layering from profile defaults, project config, environment variables, and CLI flags.
- Add `.env.example`.
- Add SQLite initialization command.
- Add business knowledge base initialization command.

Target commands:

```bash
wasila --help
wasila init startup_saas
wasila kb init
```

Done when:

- A new local project can be initialized.
- Core interfaces exist for storage, orchestration, gateways, providers, profiles, skills, policies, knowledge, and customer memory.
- The expected data directories and SQLite database are created.
- Starter business knowledge files are created.

## Phase 2: Storage And Memory

Goals:

- Implement SQLite migrations.
- Implement customer lookup and creation.
- Implement message persistence.
- Implement ticket and ticket event persistence.
- Implement owner summary persistence.
- Implement skill execution persistence.
- Implement `customer.md` read and write helpers.
- Implement business knowledge file read helpers.

Done when:

- The CLI can create a customer.
- The CLI can inspect a customer.
- Tickets and messages are visible from SQLite-backed commands.
- The orchestration context can include business knowledge.

## Phase 3: Event Contracts

Goals:

- Define `CustomerEvent`.
- Define `OwnerNotification`.
- Define `OrchestrationResult`.
- Define `MemoryUpdate`.
- Define `TicketUpdate`.
- Define `SkillCall` and `SkillResult`.
- Define idempotency behavior for repeated gateway events.

Done when:

- Customer sandbox and webhook gateway can produce the same internal event shape.
- Owner sandbox and owner gateway can consume the same notification shape.
- Duplicate events do not create duplicate messages, tickets, or owner notifications.

## Phase 4: CLI Sandbox

Goals:

- Implement `wasila sandbox customer`.
- Implement `wasila sandbox owner`.
- Persist messages, tickets, agent runs, and owner summaries during sandbox use.
- Print customer ID, ticket ID, and run ID for debugging.

Done when:

- A contributor can test the full customer and owner loop without external gateways.

## Phase 5: CrewAI Runner

Goals:

- Implement a CrewAI-backed orchestration runner.
- Implement the Wasila workflow lifecycle around the runner.
- Load the `startup_saas` profile.
- Load the profile template files.
- Run front office, ticket manager, technical support, and owner behavior.
- Register MVP-safe skills for ticket updates, memory suggestions, and owner notifications.
- Apply memory update and owner notification policies.
- Return a normalized `OrchestrationResult`.

Done when:

- A sandbox customer message can produce an AI response and operational trace.
- CrewAI owns orchestration execution but not the full workflow lifecycle.

## Phase 6: Webhook Gateway

Goals:

- Implement generic customer webhook input.
- Implement generic owner webhook output.
- Keep webhook behavior aligned with sandbox event contracts.

Done when:

- A local daemon can receive a webhook customer message and emit owner notifications through webhook or sandbox inspection.

## Phase 7: MVP Smoke Test

Goals:

- Add a documented smoke test.
- Verify init, sandbox customer, sandbox owner, customer inspect, and ticket list.
- Cover product question, technical support issue, customer memory update, owner escalation, refund approval boundary, and idempotent retry.

Expected smoke path:

```bash
wasila init startup_saas
wasila provider set openai-compatible --base-url https://api.openai.com/v1 --model gpt-4.1-mini --api-key-env OPENAI_API_KEY
wasila gateway add customer webhook
wasila gateway add owner webhook
wasila sandbox customer --new "Acme Labs"
wasila sandbox owner --latest
wasila customer inspect cust_acme_labs
wasila ticket list
```

Done when:

- The smoke path works on a fresh checkout with documented environment setup.
