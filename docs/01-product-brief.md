# Product Brief

## Name

Wasila

## Tagline

Customer AI orchestration with memory, tickets, and owner-aware agents.

## Meaning

Wasila means a connecting path, bridge, or means of connection. The product should embody that meaning: it connects customers, AI agents, business context, operational tickets, and the owner loop into one inspectable workflow.

## Problem

Many customer AI systems are implemented as a single chatbot. That usually works for basic FAQs, but it breaks down when the business needs:

- Long-term customer memory.
- Special handling notes.
- Ticket ownership and traceability.
- Technical or domain escalation.
- Owner visibility into important customer situations.
- Modular integration with customer gateways, owner gateways, and future channels.

## MVP Promise

Wasila helps a small team run a customer-facing AI team from the CLI. The system receives customer messages, loads customer memory, routes work across CrewAI agents, updates tickets, and produces owner-aware summaries when needed.

## Open Source Posture

Wasila should be easy for outside contributors to understand, run, and extend.

The project should prefer:

- Documentation-first product decisions.
- Local-first MVP behavior.
- Explicit extension contracts for profiles, gateways, providers, and storage.
- Small issues that contributors can implement independently.
- Clear examples over hidden conventions.
- Honest roadmap labels for planned features.

The project should avoid:

- Requiring a hosted cloud service for the MVP.
- Mixing secrets into templates, docs, examples, or committed config.
- Treating future roadmap items as already implemented.
- Building a broad platform before the first customer workflow is proven.

## Non-Goals For MVP

- No multi-tenant cloud dashboard.
- No complex RBAC.
- No full CRM replacement.
- No production-grade queue system yet.
- No deep analytics dashboard.
- No many-profile marketplace.
- No gateway explosion before the first webhook flow is proven.
- No web console before the CLI daemon is stable.

## Target User

The first user is a founder, operator, or technical team member at a small business who wants customer AI automation without losing business context or operational traceability.

## MVP Success Criteria

- A user can initialize the `startup_saas` profile from the CLI.
- A local daemon can receive a webhook message.
- The system can create or update a customer memory file.
- The system can create or update a ticket in SQLite.
- CrewAI can route work across the default profile agents.
- The owner can inspect important conversation summaries.
- The implementation remains easy to extend with another profile or gateway.
