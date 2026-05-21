# Wasila

Customer AI orchestration with memory, tickets, and owner-aware agents.

Wasila is an MVP-focused CLI kit for building customer-facing AI teams with CrewAI as the default orchestration engine. It helps small teams onboard an AI customer profile, connect it to a messaging gateway, keep long-term customer memory, and trace operational work through a simple ticket store.

The first goal is not to build a universal AI platform. The first goal is to make one useful customer workflow easy to run locally, easy to inspect, and easy to extend.

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

## MVP Scope

The MVP starts with one profile and a simple gateway model:

- Profile: `startup_saas`
- Customer gateway: generic HTTP webhook
- Owner gateway: generic HTTP webhook first, with OpenClaw and Hermes planned as owner notification gateways
- Orchestration: CrewAI
- Storage: SQLite as operational source of truth plus one `customer.md` per customer for relationship memory
- Knowledge: local business knowledge base for company and product context
- Runtime: local CLI daemon plus CLI sandbox
- Agents: front office, ticket manager, technical support, owner

The MVP should prove this flow:

1. Receive an inbound customer message through a webhook.
2. Resolve or create the customer identity.
3. Load `customer.md` and SQLite context.
4. Load the business knowledge base for shared company context.
5. Route the message through a CrewAI-powered agent team.
6. Create or update a ticket when needed.
7. Update customer memory when the interaction adds durable context.
8. Return a response through the gateway.
9. Produce an owner summary for important escalations.

## Example CLI

These commands describe the intended developer experience. They are design targets for the first implementation slice.

```bash
wasila init startup_saas
wasila kb init
wasila provider set openai-compatible --base-url https://api.openai.com/v1 --model gpt-4.1-mini --api-key-env OPENAI_API_KEY
wasila gateway add customer webhook
wasila gateway add owner webhook
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

- Profiles define agents, tasks, prompts, and domain behavior.
- Customer gateways receive customer conversations.
- Owner gateways send owner summaries, alerts, and approval requests.
- Providers wrap OpenAI-compatible LLM API configuration, including `base_url`, `model`, and API key environment variable.
- Storage keeps memory and operational state inspectable.
- Skills let agents execute controlled, traceable actions.
- The orchestration layer uses CrewAI by default while keeping Wasila's own interface stable.

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

## Roadmap

After the local CLI daemon becomes stable, Wasila can grow into:

- An HTTP API for external systems.
- A web-based daemon console for inspecting customers, tickets, runs, and owner summaries.
- Additional customer gateways such as Telegram and WhatsApp.
- Owner gateways such as OpenClaw and Hermes.
- More profiles for agencies, e-commerce, education, and appointment-based businesses.

See `docs/07-roadmap.md` for the staged roadmap.

## Status

Wasila is currently in docs-first MVP planning.

Current phase:

- Repository bootstrap is complete.
- MVP docs and architecture contracts are drafted.
- GitHub milestones and backlog issues are open.

Next milestone:

- Stage 1: Local CLI MVP.

Backlog:

- Issues: https://github.com/pendig/wasila/issues
- Milestones: https://github.com/pendig/wasila/milestones

The next implementation step is to scaffold the CLI, profile format, SQLite schema, and the first CrewAI runner.
