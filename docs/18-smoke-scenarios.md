# MVP Smoke Scenarios

Smoke scenarios should prove the MVP behavior without requiring external gateways.

The first smoke path should use the CLI sandbox.

## Scenario 1: New Customer Product Question

Purpose:

Verify basic customer response and message persistence.

Input:

```text
Customer: Hi, what does your product do?
```

Expected:

- Customer is created.
- Inbound message is stored.
- Agent uses business knowledge.
- Customer receives a concise answer.
- No owner notification unless policy requires it.

## Scenario 2: Technical Support Issue

Purpose:

Verify ticket creation and technical routing.

Input:

```text
Customer: I cannot connect our Stripe integration.
```

Expected:

- Ticket is created.
- Ticket state is `clarifying` or `in_progress`.
- Technical support agent asks for useful missing context.
- Agent run is stored.
- Customer ID, ticket ID, and run ID are shown.

## Scenario 3: Durable Customer Memory

Purpose:

Verify that `customer.md` is updated only with durable relationship context.

Input:

```text
Customer: Please keep updates short. Our team prefers concise technical summaries.
```

Expected:

- Message is stored in SQLite.
- `customer.md` gets a concise preference note.
- Full transcript is not copied into `customer.md`.

## Scenario 4: Owner Escalation

Purpose:

Verify owner notification flow.

Input:

```text
Customer: This is the third time the integration failed. We may cancel if this is not fixed today.
```

Expected:

- Ticket priority becomes `high`.
- Owner notification is created.
- Owner sandbox can show the summary.
- Customer response acknowledges escalation without making unsupported promises.

## Scenario 5: Refund Or Billing Exception

Purpose:

Verify approval boundary.

Input:

```text
Customer: I want a refund for this month.
```

Expected:

- Ticket is created or updated.
- Owner notification is created.
- AI does not approve the refund by itself.
- Customer response explains that the request is being reviewed.

## Scenario 6: Idempotent Retry

Purpose:

Verify duplicate events do not create duplicate messages or tickets.

Input:

Send the same event twice with the same `event_id`.

Expected:

- Message is stored once.
- Ticket is not duplicated.
- The second event returns or references the existing processing result.
