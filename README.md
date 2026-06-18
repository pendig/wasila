# Wasila

Lightweight customer-support gateway for private AI assistants, with memory, tickets, and owner-aware escalation.

Wasila is an MVP-focused CLI kit for putting a safe customer frontdesk in front of private AI assistants such as Hermes, OpenClaw, or any other agent runtime. It helps small teams connect customer messages to a lightweight support workflow, keep long-term customer memory, trace tickets, and delegate sanitized work to private assistants when needed.

The first goal is not to build a universal AI platform. The first goal is to make one useful customer workflow easy to run locally, easy to inspect, and safe to connect to private assistants.

Wasila is intended to be open-source friendly: clear docs, small extension points, local-first defaults, no hidden cloud dependency for the MVP, and a roadmap that separates what is implemented from what is planned.

## Why Wasila

Customer conversations usually fail when context is lost: prior promises, special handling, recurring issues, unresolved tickets, or owner-level decisions. Wasila treats memory and operational trace as first-class parts of the agent system.

Each customer can have:

- A human-readable `customer.md` memory file for long-term context.
- Shared business knowledge so every agent understands the company, product, policies, tone, and escalation rules.
- A SQLite record for structured customer data.
- Tickets and ticket events for traceable work.
- Agent run logs for debugging orchestration decisions.
- Owner summaries when a conversation needs business attention.
- Sanitized private-assistant jobs when work should be delegated to Hermes, OpenClaw, or another AI agent.

## MVP Scope

The MVP starts with one profile and a simple gateway model:

- Profile: `startup_saas`
- Customer gateway: generic HTTP webhook first, with WhatsApp via `wacli` planned as the first platform adapter
- Private assistant gateway: CLI job adapter first, so Hermes, OpenClaw, or another agent can process sanitized work without seeing the raw customer channel
- Owner gateway: generic HTTP webhook first, with OpenClaw and Hermes planned as owner notification gateways
- Orchestration: Wasila workflow with CrewAI as the default in-process runner; private assistants are external workers behind a job contract
- Storage: SQLite as operational source of truth plus one `customer.md` per customer for relationship memory
- Knowledge: local business knowledge base for company and product context
- Runtime: local CLI daemon plus CLI sandbox
- Agents: front office, ticket manager, technical support, owner

The MVP should prove this flow:

1. Receive an inbound customer message through a webhook.
2. Resolve or create the customer identity.
3. Load `customer.md` and SQLite context.
4. Load the business knowledge base for shared company context.
5. Answer directly when the frontdesk can safely handle it.
6. Delegate a sanitized `PrivateAgentJob` to Hermes, OpenClaw, or another assistant when deeper work is needed.
7. Receive a `PrivateAgentResult` and filter it before customer delivery.
8. Create or update a ticket when needed.
9. Update customer memory when the interaction adds durable context.
10. Return a response through the customer gateway.
11. Produce an owner summary for important escalations.

## Example CLI

These commands describe the intended developer experience. They are design targets for the first implementation slice.

```bash
wasila init startup_saas
wasila kb init
wasila provider set openai-compatible --base-url https://api.openai.com/v1 --model openai/gpt-4.1-mini --api-key-env OPENAI_API_KEY
wasila gateway add customer webhook
wasila gateway add owner webhook
wasila assistant add cli --name hermes --command "hermes -p private-assistant"
wasila daemon start
wasila sandbox customer
wasila sandbox owner
wasila customer inspect cust_123
wasila ticket list
```

## Development

The current scaffold can run locally without installing external runtime dependencies:

```bash
PYTHONPATH=src python3 -m wasila --help
PYTHONPATH=src python3 -m wasila init startup_saas
PYTHONPATH=src python3 -m wasila kb init
PYTHONPATH=src python3 -m unittest discover -s tests
```

CrewAI is the default orchestration core for the MVP runner and is declared as an optional dependency group for the upcoming adapter:

```bash
pip install -e ".[crewai]"
```

## Repository Direction

Wasila should stay modular even while the MVP is small:

- Profiles define frontdesk behavior, prompts, escalation rules, and safe delegation policy.
- Customer gateways receive customer conversations.
- Private assistant gateways send sanitized jobs to Hermes, OpenClaw, or any other worker agent and receive structured results.
- Owner gateways send owner summaries, alerts, and approval requests.
- Providers wrap OpenAI-compatible LLM API configuration, including `base_url`, `model`, and API key environment variable.
- Storage keeps memory and operational state inspectable.
- Skills let agents execute controlled, traceable actions.
- The orchestration layer uses CrewAI by default for local workflow while keeping Wasila's private-assistant job contract stable.

See the documentation in `docs/` for the MVP architecture and product decisions. Start with `docs/README.md`.

Useful starting points:

- `docs/01-product-brief.md`
- `docs/02-mvp-scope.md`
- `docs/03-architecture.md`
- `docs/22-architecture-boundaries.md`
- `docs/05-data-model.md`
- `docs/09-sandbox.md`
- `docs/10-mvp-implementation-plan.md`
- `docs/12-event-contracts.md`
- `docs/14-knowledge-base.md`
- `docs/15-provider-configuration.md`
- `docs/16-operational-policies.md`
- `docs/17-profile-template.md`
- `docs/18-smoke-scenarios.md`
- `docs/21-skills-and-execution.md`
- `docs/23-crewai-alignment.md`
- `docs/24-private-agent-gateway.md`

## Roadmap

After the local CLI daemon becomes stable, Wasila can grow into:

- An HTTP API for external systems.
- A web-based daemon console for inspecting customers, tickets, runs, and owner summaries.
- Additional customer gateways such as Telegram and WhatsApp.
- Private assistant adapters for Hermes, OpenClaw, and other agents.
- Owner gateways such as OpenClaw and Hermes.
- More profiles for agencies, e-commerce, education, and appointment-based businesses.

See `docs/07-roadmap.md` for the staged roadmap.

## Status

Wasila is now in **Stage 1: Local CLI MVP (implemented and runnable)**.

What already works:

- `wasila init`, `wasila kb init`, provider and gateway config commands.
- SQLite bootstrap and schema migrations.
- Customer memory directory and knowledge file bootstrap.
- Webhook daemon + idempotent customer message handling.
- Customer and owner CLI sandbox.
- Customer inspect and ticket list commands.
- CrewAI-first orchestration runner with SQLite-backed workflow, policy checks, and skill trace persistence.

Backlog:

- Issues: https://github.com/pendig/wasila/issues
- Milestones: https://github.com/pendig/wasila/milestones
