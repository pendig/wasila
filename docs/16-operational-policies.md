# Operational Policies

These policies define when Wasila agents should act, write memory, notify the owner, or pause for human approval.

## Human Handoff And Approval

AI should pause or escalate when a situation has business, legal, financial, or relationship risk.

MVP handoff triggers:

- Customer explicitly asks for a human or owner.
- Customer is angry, threatening churn, or reporting repeated unresolved issues.
- Refund, discount, cancellation, or billing exception is requested.
- The answer requires private account access that the AI does not have.
- The request involves legal, privacy, security, or compliance claims.
- The agent is uncertain and a wrong answer could harm the business relationship.
- A high-priority ticket remains unresolved after repeated attempts.

Expected behavior:

- Create or update a ticket.
- Send an owner notification.
- Avoid pretending the issue is resolved.
- Tell the customer clearly that the issue is being escalated.

## Conversation State

Tickets should track a simple state so agents know where the conversation is.

MVP states:

- `intake`
- `clarifying`
- `in_progress`
- `waiting_customer`
- `waiting_owner`
- `resolved`
- `escalated`

The state should be stored in SQLite, usually on `tickets.status` or `tickets.metadata_json` for MVP.

## Memory Update Policy

Agents should not write every message into `customer.md`.

Write to customer memory only when the fact is:

- Durable.
- Useful for future treatment.
- Specific to that customer.
- Not a raw transcript.
- Not a secret.
- Not an unverified assumption.

Good memory:

```text
Customer prefers concise technical updates and is blocked during onboarding.
```

Bad memory:

```text
Customer said: "Here is our private integration token..."
```

## Owner Notification Policy

Owner notifications should be high signal. Wasila should not notify the owner for every normal support turn.

Notify the owner when:

- Risk level is `high` or `urgent`.
- The customer asks for a human, manager, or owner.
- The ticket involves refund, billing exception, cancellation, or churn risk.
- The same customer has repeated unresolved issues.
- A support issue blocks onboarding or revenue.
- The AI needs approval before taking the next step.

Owner notification should include:

- Customer.
- Ticket.
- Risk level.
- Short summary.
- Recommended action.
- Why owner attention is needed.

## Agent Boundaries

Agents should not:

- Invent policies.
- Promise refunds, discounts, timelines, or technical fixes without approval.
- Claim access to systems they cannot inspect.
- Store secrets in memory.
- Hide risk from the owner.

Agents should:

- Ask clarifying questions when needed.
- Create traceable tickets.
- Summarize uncertainty clearly.
- Escalate when policy requires it.

## Skill And Execution Policy

Agents can use approved skills, but execution must be explicit, permissioned, and traceable.

MVP execution levels:

- `read`: inspect local state, tickets, memory, knowledge, or safe external data.
- `write`: update tickets, append notes, update customer memory, create owner summaries.
- `external`: call external APIs, gateways, or business systems.
- `approval_required`: any action that changes money, access, account status, legal posture, or customer commitment.

MVP default rule:

- Allow `read` and safe `write` skills.
- Require owner approval for `external` and `approval_required` skills unless a profile explicitly marks them safe.

All skill executions should record:

- Skill name.
- Agent name.
- Customer ID.
- Ticket ID when relevant.
- Input JSON.
- Output JSON.
- Status.
- Approval status when relevant.

Agents should not execute arbitrary shell commands in the MVP.
