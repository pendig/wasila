# Skills And Execution

Wasila agents should be able to do useful work, not only write replies.

Skills are controlled capabilities that an agent can call during orchestration. They must be permissioned, traceable, and safe by default.

## MVP Skill Philosophy

Start with safe internal skills:

- Create or update tickets.
- Append ticket events.
- Suggest customer memory updates.
- Create owner notifications.
- Read business knowledge.
- Read recent customer context.

Defer risky external skills until approval and audit behavior are stronger.

## Skill Types

### Read Skills

Read local context without changing state.

Examples:

- `customer.read`
- `ticket.list_open`
- `knowledge.read`

### Write Skills

Change Wasila's local operational state.

Examples:

- `ticket.create`
- `ticket.update`
- `ticket.add_event`
- `memory.suggest_update`
- `owner.notify`

### External Skills

Call external services or business systems.

Examples:

- `billing.lookup_invoice`
- `crm.update_customer`
- `statuspage.create_incident`

External skills should usually require explicit configuration and may require owner approval.

### Approval-Required Skills

Actions that can affect money, access, commitments, or legal posture.

Examples:

- `billing.issue_refund`
- `account.disable`
- `subscription.cancel`
- `legal.send_notice`
- `customer.promise_sla_exception`

## MVP Skill Registry

Suggested local registry:

```text
skills/
  ticket.yaml
  memory.yaml
  owner.yaml
```

Suggested skill definition:

```yaml
name: ticket.create
description: Create a customer ticket.
execution_level: write
approval_required: false
input_schema:
  title: string
  priority: string
  summary: string
```

## Execution Trace

Every skill call should be persisted.

Suggested fields:

- `id`
- `customer_id`
- `ticket_id`
- `agent_run_id`
- `skill_name`
- `execution_level`
- `approval_required`
- `approval_status`
- `input_json`
- `output_json`
- `status`
- `error`
- `created_at`

## Approval Flow

For MVP, approval-required skills should not execute automatically.

Expected behavior:

1. Agent proposes the skill call.
2. Wasila records the pending action.
3. Owner notification is created.
4. Owner approves, rejects, or comments in a later iteration.

Until approval tooling exists, the safe MVP behavior is to notify the owner and stop before executing the action.

## Relationship To CrewAI

CrewAI should expose Wasila skills as tools.

Wasila should still own:

- Skill registry.
- Permission levels.
- Approval rules.
- Execution trace.
- Storage of skill results.

This keeps tool behavior consistent even if orchestration internals change later.

## CrewAI Tool Mapping

When implementing the CrewAI runner, prefer CrewAI's tool primitives instead of creating a separate tool runtime.

Wasila should wrap each approved skill as a CrewAI tool and keep permission checks around the tool execution.

For risky actions, the tool should return a pending approval result instead of executing the external action.
