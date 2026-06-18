# Architecture

## Design Principles

- Wasila is the customer-support airlock between public customers and private AI assistants.
- CrewAI is the default in-process orchestration core.
- Wasila owns the product workflow, profile format, storage model, gateway contracts, and private-assistant job contract.
- The MVP should be small, but module boundaries should make extension natural.
- Every customer interaction should be inspectable through memory, tickets, and agent run records.

## High-Level Flow

```text
Customer Gateway
-> CustomerEvent
-> Customer context loader
-> Business knowledge loader
-> Wasila frontdesk workflow
-> CrewAI orchestration when local handling is enough
-> Private assistant job when deeper work is needed
-> Result filtering
-> Skill execution when allowed
-> Ticket and memory updates
-> Customer Gateway response
-> Owner Gateway notification when needed
```

## Proposed Modules

```text
wasila/
  cli/
  core/
    events/
    knowledge/
    memory/
    tickets/
    skills/
    storage/
    orchestration/
    daemon/
  profiles/
    startup_saas/
  gateways/
    webhook/
    wacli/
    openclaw/
    hermes/
  assistants/
    cli/
    http/
  providers/
    openai/
```

## Profile Contract

A profile should define:

- Profile metadata.
- Agent definitions.
- Task definitions.
- Prompt templates.
- Knowledge base defaults.
- Skill and execution permissions.
- Escalation rules.
- Memory update rules.
- Ticket defaults.

The profile should be declarative where possible, with code hooks only when a domain needs custom behavior.

## Gateway Contract

Wasila has three gateway roles:

- Customer gateways receive public customer conversations and send replies back to the customer channel.
- Private assistant gateways send sanitized jobs to trusted worker agents and return structured results.
- Owner gateways deliver owner-facing summaries, alerts, and approval requests.

A customer gateway converts external events into Wasila's internal `CustomerEvent`.

The internal event should contain:

- `gateway`
- `gateway_role`
- `external_conversation_id`
- `external_customer_id`
- `customer_id` when already known
- `message_text`
- `message_timestamp`
- `metadata_json`

The first customer gateway should support webhook input. `wacli` should be the first WhatsApp adapter. Telegram and other channels should become separate adapters that produce the same internal event shape.

An owner gateway should accept an `OwnerNotification` payload and deliver it to the configured owner channel.

The owner notification should contain:

- `profile`
- `customer_id`
- `ticket_id` when relevant
- `summary`
- `risk_level`
- `recommended_action`
- `metadata_json`

The first owner gateway should be webhook. OpenClaw and Hermes are planned owner gateway integrations. They are also planned private assistant integrations, but only behind the sanitized job contract.

## Orchestration Contract

CrewAI should be the first local runner. Wasila should still expose a small internal boundary:

```text
Orchestrator.run(event, context) -> OrchestrationResult
```

This keeps the CLI, daemon, storage, and gateway modules independent from direct CrewAI details.

## Private Assistant Contract

Private assistants such as Hermes, OpenClaw, Codex, or another agent runtime are workers, not customer gateways. Wasila sends them only sanitized jobs and keeps the final customer reply path.

```text
PrivateAgent.run(job) -> PrivateAgentResult
```

A `PrivateAgentJob` should contain:

- `job_id`
- `customer_id`
- `ticket_id` when relevant
- `intent`
- `summary`
- `safe_context`
- `forbidden`

A `PrivateAgentResult` should contain:

- `job_id`
- `status`
- `customer_reply`
- `owner_note`
- `actions_requested`

Wasila must review or filter the result before sending anything to the customer. The private assistant should never receive direct customer-channel credentials or send messages to the customer directly.

## Knowledge Contract

The business knowledge base is shared context for all agents in a Wasila project. It is different from `customer.md`.

- Business knowledge answers: "What does this business do, what are its products, policies, tone, and escalation rules?"
- Customer memory answers: "What do we know about this specific customer and how should we treat them?"

For the MVP, the knowledge base should be local Markdown files under:

```text
knowledge/
  business.md
  products.md
  policies.md
  support.md
  owner.md
```

The context loader should provide relevant knowledge to CrewAI agents before they act. The first implementation can load the full Markdown set for simplicity. Retrieval, chunking, embeddings, and search can come later.

## Storage Contract

SQLite owns structured operational data. Markdown owns human-readable customer memory and business knowledge.

The storage layer should support:

- Customer lookup and creation.
- Message persistence.
- Ticket creation and updates.
- Ticket event append.
- Agent run append.
- Skill execution append.
- Memory file read and write.
- Knowledge file read.

## Owner Loop

Every profile must define an owner-facing behavior.

The owner loop should be triggered by:

- High-priority tickets.
- Angry or churn-risk customer signals.
- Refund or billing risk.
- Technical blockers.
- Repeated unresolved issues.
- Explicit customer request for a human or owner.

The CLI should let users configure owner delivery independently from customer handling. For example, customer messages can arrive through WhatsApp while owner summaries are sent through OpenClaw, Hermes, or webhook.
