# Observability

Wasila should be easy to inspect from the CLI during MVP development.

The goal is not full production observability yet. The goal is enough traceability to debug customer workflows.

## MVP Trace Data

Persist:

- Messages.
- Tickets.
- Ticket events.
- Agent runs.
- Owner summaries.
- Gateway event IDs.

## Useful CLI Commands

Target commands:

```bash
wasila runs latest
wasila runs failed
wasila ticket show tick_001
wasila customer inspect cust_001
wasila owner summary --latest
```

## Agent Runs

Each agent run should record:

- Run ID.
- Customer ID.
- Ticket ID when relevant.
- Profile.
- Agent name.
- Task name.
- Status.
- Input JSON.
- Output JSON.
- Error message when failed.
- Created timestamp.

## Ticket Timeline

`ticket_events` should allow a human to reconstruct what happened.

Useful event types:

- `created`
- `status_changed`
- `priority_changed`
- `agent_comment`
- `customer_message`
- `owner_notified`
- `resolved`

## Failure Visibility

When orchestration fails, Wasila should:

- Store the failed run.
- Keep the inbound message.
- Avoid losing the event.
- Provide a clear CLI inspection path.

For MVP, retries can be manual. Automatic retry behavior can come later.
