# Product Brief

## Name

Wasila

## Tagline

Lightweight customer-support gateway for private AI assistants, with memory, tickets, and owner-aware escalation.

## Meaning

Wasila means a connecting path, bridge, or means of connection. The product should embody that meaning: it connects customers, a safe customer frontdesk, private AI assistants, business context, operational tickets, and the owner loop into one inspectable workflow.

## Problem

Many customer AI systems are implemented as a single chatbot. That usually works for basic FAQs, but it breaks down when the business needs:

- Long-term customer memory.
- Special handling notes.
- Ticket ownership and traceability.
- Technical or domain escalation.
- Owner visibility into important customer situations.
- Modular integration with customer gateways, private AI assistants, owner gateways, and future channels.

## MVP Promise

Wasila helps a small team run a customer-facing AI frontdesk from the CLI. The system receives customer messages, loads customer memory, answers simple support messages, delegates sanitized jobs to private assistants such as Hermes or OpenClaw when needed, updates tickets, and produces owner-aware summaries.

## Open Source Posture

Wasila should be easy for outside contributors to understand, run, and extend.

The project should prefer:

- Documentation-first product decisions.
- Local-first MVP behavior.
- Explicit extension contracts for profiles, gateways, providers, and storage.
- Small issues that contributors can implement independently.
- Clear examples over hidden conventions.
- A small job contract that lets any private assistant plug in without becoming the public customer gateway.
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
- No gateway explosion before the first webhook or `wacli` flow is proven.
- No direct public customer access to private assistants.
- No web console before the CLI daemon is stable.

## Target User

The first user is a founder, operator, or technical team member at a small business who wants customer AI automation without losing business context or operational traceability.

## MVP Success Criteria

- A user can initialize the `startup_saas` profile from the CLI.
- A local daemon can receive a webhook message.
- The system can create or update a customer memory file.
- The system can create or update a ticket in SQLite.
- CrewAI can run the local frontdesk workflow.
- The system can hand a sanitized job to a private assistant adapter and consume its structured result.
- The owner can inspect important conversation summaries.
- The implementation remains easy to extend with another profile or gateway.
