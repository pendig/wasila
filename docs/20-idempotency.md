# Idempotency

Gateways and webhooks can retry events. Wasila should avoid duplicate messages, tickets, and owner notifications.

## MVP Rule

Every inbound customer event should have a stable event ID.

If the external gateway provides an event ID, use it.

If not, derive one from:

- Gateway name.
- External conversation ID.
- External customer ID.
- Message timestamp.
- Message text hash.

## Suggested Fields

Add to message or gateway event storage:

- `event_id`
- `gateway`
- `external_conversation_id`
- `external_customer_id`
- `processed_at`
- `result_json`

`event_id` should be unique per gateway.

## Behavior

When receiving an event:

1. Check whether `event_id` already exists.
2. If it exists, return the existing result or mark it as duplicate.
3. If it does not exist, process normally.
4. Persist the event before or during processing so failures can be inspected.

## Why This Matters

Without idempotency:

- The same customer message can be stored twice.
- The same issue can create multiple tickets.
- The owner can receive duplicate alerts.
- Agent traces become confusing.

## MVP Acceptance Criteria

- Sending the same sandbox or webhook event twice should not create duplicate tickets.
- Duplicate handling should be visible in logs or CLI output.
