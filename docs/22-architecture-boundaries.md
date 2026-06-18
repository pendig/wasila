# Architecture Boundaries

Wasila should stay modular while the MVP remains small.

The implementation should follow a ports-and-adapters shape: core workflow code owns the product logic, while CrewAI, SQLite, HTTP, gateways, and providers sit behind explicit interfaces.

## Boundary Goals

- Keep CrewAI as the default runner without leaking CrewAI details everywhere.
- Keep SQLite replaceable in the future without changing agent behavior.
- Keep customer gateways, private assistant gateways, and owner gateways independent.
- Let profiles, providers, skills, and gateways register cleanly.
- Keep policy checks deterministic and testable outside prompts.
- Make sandbox and real gateways share the same execution path.

## Core Domain

The core domain should include:

- Events and contracts.
- Workflow lifecycle.
- Policy checks.
- Skill registry and execution decisions.
- Context loading.
- Result application.

The core domain should not import gateway-specific, web-framework-specific, or provider-specific details.

## Ports

Suggested MVP interfaces:

```text
Orchestrator
PrivateAssistantGateway
Storage
CustomerGateway
OwnerGateway
ProviderConfig
ProfileRegistry
SkillRegistry
PolicyEngine
KnowledgeLoader
CustomerMemoryStore
```

### `Orchestrator`

Runs the agent workflow and returns `OrchestrationResult`.

CrewAI is the default adapter.

### `PrivateAssistantGateway`

Sends sanitized jobs to Hermes, OpenClaw, or another agent runtime and returns structured results. The first adapter should be CLI-based. Native plugins come later.

### `Storage`

Persists customers, messages, tickets, ticket events, agent runs, skill executions, owner summaries, and idempotency records.

SQLite is the default adapter.

### `CustomerGateway`

Converts customer channel input into `CustomerEvent` and sends customer responses.

Webhook is the first adapter.

### `OwnerGateway`

Delivers `OwnerNotification` payloads.

Webhook is the first adapter. OpenClaw and Hermes are planned adapters.

### `ProviderConfig`

Describes an OpenAI-compatible API endpoint with `base_url`, `model`, and `api_key_env`.

Profiles should not hardcode provider credentials.

### `ProfileRegistry`

Loads profile files such as `profile.yaml`, `agents.yaml`, `tasks.yaml`, prompts, and `skills.yaml`.

### `SkillRegistry`

Exposes approved skills to orchestration and enforces execution levels.

### `PolicyEngine`

Applies deterministic rules for handoff, memory writes, owner notifications, and skill approval.

### `KnowledgeLoader`

Loads business knowledge from `knowledge/*.md`.

### `CustomerMemoryStore`

Reads and writes per-customer `customer.md` files.

## Workflow Lifecycle

The Wasila workflow should own the full customer interaction lifecycle:

```text
1. Receive CustomerEvent.
2. Check idempotency.
3. Resolve or create customer.
4. Persist inbound message.
5. Load customer memory.
6. Load business knowledge.
7. Load open tickets and recent messages.
8. Run local orchestration.
9. Delegate a sanitized job to a private assistant when needed.
10. Filter private assistant results.
11. Execute allowed skills.
12. Apply ticket updates.
13. Apply approved memory updates.
14. Persist agent runs, private assistant jobs, and skill executions.
15. Persist owner notifications.
16. Deliver owner notifications when configured.
17. Persist outbound customer response.
18. Return response to customer gateway.
```

CrewAI should participate in step 8. Private assistants should participate in step 9. Neither should own the full lifecycle.

When CrewAI already provides a primitive for a step, prefer using it inside the relevant adapter. For example, use CrewAI agents/tasks/crews for orchestration, CrewAI tools for Wasila skills, CrewAI knowledge sources for business knowledge retrieval, and CrewAI Flows when the workflow lifecycle needs deterministic routing or persistence.

## Registry Model

Wasila should prefer explicit registries over hardcoded branching.

Registry categories:

- Profiles.
- Customer gateways.
- Private assistant gateways.
- Owner gateways.
- Providers.
- Skills.
- Orchestration runners.

Adding a future adapter should look like registration plus implementation, not rewriting core workflow code.

## Policy Modules

Policies should be normal code, not only prompt instructions.

MVP policy modules:

- `MemoryPolicy`: determines whether a memory update is durable and safe.
- `OwnerNotificationPolicy`: decides whether owner attention is needed.
- `SkillApprovalPolicy`: blocks risky skill execution until approved.
- `HandoffPolicy`: decides when the AI should pause or escalate.

Prompts can suggest behavior, but policy modules should enforce boundaries.

## Config Layering

Config should resolve in this order:

```text
Profile defaults
-> .wasila/config.toml
-> environment variables
-> CLI flags
```

Later layers override earlier layers.

Secrets should be values in environment variables, not committed config.

## Test Fixtures

The MVP should make tests and demos easy.

Suggested fixtures:

- Sample business knowledge.
- Sample customer memory.
- Sample CustomerEvent payloads.
- Fake OpenAI-compatible provider.
- Fake customer gateway.
- Fake owner gateway.
- Temporary SQLite database.

These fixtures keep sandbox behavior and automated tests aligned.
