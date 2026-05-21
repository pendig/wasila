# CLI Sandbox

The sandbox is a first-class MVP feature. It lets contributors and operators test Wasila without setting up external messaging gateways.

## Why It Exists

Wasila has two audiences in every workflow:

- The customer, who sends messages and receives responses.
- The owner, who receives summaries, escalations, and recommended actions.

The sandbox should make both sides testable from the CLI.

## Customer Sandbox

Command:

```bash
wasila sandbox customer
```

Purpose:

Send simulated customer messages through the same event path used by real customer gateways.

Expected behavior:

- Create or reuse a customer.
- Send a message to the configured profile.
- Load business knowledge.
- Run CrewAI orchestration.
- Persist inbound and outbound messages.
- Create or update tickets when needed.
- Update `customer.md` when durable memory is produced.
- Print the AI response.
- Print useful trace IDs such as customer ID, ticket ID, and run ID.

Example session:

```text
$ wasila sandbox customer --new "Acme Labs"
Customer: I cannot connect our Stripe integration.
Wasila: Thanks. I will help narrow this down. Which environment is failing?
Trace: customer=cust_acme_labs ticket=tick_001 run=run_001
```

## Owner Sandbox

Command:

```bash
wasila sandbox owner
```

Purpose:

Show owner-facing notifications without configuring OpenClaw, Hermes, or an external webhook.

Expected behavior:

- Display owner summaries.
- Display risk level.
- Display recommended owner action.
- Link the notification to customer ID and ticket ID.
- Support a watch mode in a later iteration.

Example session:

```text
$ wasila sandbox owner --latest
Owner Summary
Customer: Acme Labs
Risk: medium
Ticket: tick_001
Recommended action: Ask technical support to review the Stripe integration logs.
```

## Relationship To Real Gateways

The sandbox should not be a separate code path that hides real integration bugs.

The customer sandbox should produce the same internal `CustomerEvent` used by customer gateways.

The owner sandbox should consume the same `OwnerNotification` payload used by owner gateways.

This makes it a useful development tool, smoke test path, and demo experience.

## MVP Acceptance Criteria

- A contributor can initialize Wasila and test a customer conversation from the CLI.
- A contributor can see owner-facing output from the CLI.
- Customer memory, tickets, messages, and agent runs are persisted during sandbox usage.
- Business knowledge is loaded from the same path used by real gateway flows.
- Sandbox output includes IDs that make debugging easy.
