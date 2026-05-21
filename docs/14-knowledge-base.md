# Business Knowledge Base

Wasila needs two kinds of memory:

- Business knowledge: shared context about the company, product, policies, support rules, and owner preferences.
- Customer memory: per-customer relationship context stored in `customer.md`.

Both are important. Customer memory helps AI remember the person or account. Business knowledge helps AI understand what business it represents.

## MVP Shape

The MVP should use local Markdown files:

```text
knowledge/
  business.md
  products.md
  policies.md
  support.md
  owner.md
```

## Suggested Files

### `business.md`

Company overview, target customers, value proposition, operating hours, brand voice, and contact rules.

### `products.md`

Product or service catalog, features, pricing notes, plans, limitations, and common fit or non-fit cases.

### `policies.md`

Refund policy, billing policy, privacy posture, escalation policy, service boundaries, and approval rules.

### `support.md`

Troubleshooting steps, known issues, common questions, integration notes, and support boundaries.

### `owner.md`

Owner preferences, summary format, escalation preferences, decision rules, sensitive topics, and approval requirements.

## CLI

Suggested MVP command:

```bash
wasila kb init
```

This should create starter files with editable sections.

Future commands:

```bash
wasila kb list
wasila kb show products
wasila kb edit policies
wasila kb validate
```

## Loading Strategy

For the MVP, load all Markdown knowledge into the orchestration context.

This is simple, inspectable, and good enough for small businesses.

When implementing the CrewAI runner, prefer CrewAI knowledge sources for retrieval instead of building a custom retrieval layer. Wasila should keep the source files local and editable, while the CrewAI adapter can convert them into supported CrewAI knowledge sources.

Future versions can add:

- Chunking.
- Search.
- Embeddings.
- Source citations.
- Remote docs.
- Version history.

## Rules

- Do not store secrets in the knowledge base.
- Keep policies explicit.
- Keep product limitations honest.
- Mark uncertain or owner-required decisions clearly.
- Prefer short, maintained documents over large stale dumps.

## Relationship To Profiles

Profiles define the operating model. Business knowledge defines the specific business.

Example:

- Profile: `startup_saas`
- Business knowledge: "Acme Labs sells a B2B analytics platform with Stripe and Slack integrations."

The same profile can serve many businesses because the knowledge base changes per project.
