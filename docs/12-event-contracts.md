# Event Contracts

Wasila should use explicit internal contracts so profiles, gateways, storage, and orchestration can evolve independently.

These are MVP design contracts, not final API schemas.

## CustomerEvent

Produced by customer gateways and the customer sandbox.

```json
{
  "id": "evt_001",
  "gateway": "webhook",
  "gateway_role": "customer",
  "external_conversation_id": "conv_123",
  "external_customer_id": "ext_456",
  "customer_id": "cust_123",
  "message_text": "I cannot connect our Stripe integration.",
  "message_timestamp": "2026-05-21T12:00:00Z",
  "metadata_json": {}
}
```

Required MVP fields:

- `gateway`
- `gateway_role`
- `external_conversation_id`
- `external_customer_id`
- `message_text`
- `message_timestamp`

## CustomerContext

Loaded before orchestration.

```json
{
  "customer": {},
  "customer_memory_markdown": "",
  "business_knowledge_markdown": "",
  "open_tickets": [],
  "recent_messages": [],
  "profile": "startup_saas"
}
```

The `customer` object and operational history should come from SQLite. The `customer_memory_markdown` field should come from that customer's own `data/customers/{customer_id}/customer.md` file.

The MVP can provide `business_knowledge_markdown` as a concatenated Markdown string loaded from the local `knowledge/` directory.

Later versions can replace or supplement this with retrieved knowledge chunks.

## OrchestrationResult

Returned by the local orchestration runner after optional private-assistant delegation.

```json
{
  "customer_response": "Thanks. I will help narrow this down.",
  "ticket_updates": [],
  "memory_updates": [],
  "owner_notifications": [],
  "skill_results": [],
  "agent_runs": [],
  "metadata_json": {}
}
```

Required MVP fields:

- `customer_response`
- `ticket_updates`
- `memory_updates`
- `owner_notifications`
- `skill_results`
- `agent_runs`

Planned field after the private assistant adapter is implemented:

- `private_agent_jobs`

## TicketUpdate

Returned by orchestration and persisted by storage.

```json
{
  "ticket_id": "tick_001",
  "action": "create",
  "title": "Stripe integration connection issue",
  "status": "open",
  "priority": "medium",
  "summary": "Customer cannot connect Stripe integration.",
  "metadata_json": {}
}
```

Allowed MVP actions:

- `create`
- `update`
- `comment`
- `close`

## MemoryUpdate

Returned by orchestration when durable customer context should be written.

```json
{
  "customer_id": "cust_123",
  "section": "Important History",
  "body": "Customer reported a Stripe integration issue during onboarding.",
  "reason": "Useful for future technical support context."
}
```

Memory updates should be concise and durable. They should not copy full conversation logs or secrets.

## KnowledgeSource

Loaded from business knowledge files and passed into orchestration context.

```json
{
  "id": "kb_products",
  "path": "knowledge/products.md",
  "title": "Products",
  "body": "Product catalog and limitations.",
  "metadata_json": {}
}
```

The MVP can load Markdown files directly. Later versions can add source IDs, chunking, timestamps, and retrieval scores.

## SkillCall

Requested by an agent when it needs to execute a controlled capability.

```json
{
  "id": "skill_call_001",
  "agent_name": "ticket_manager",
  "skill_name": "ticket.create",
  "execution_level": "write",
  "approval_required": false,
  "input_json": {
    "title": "Stripe integration issue",
    "priority": "medium"
  }
}
```

## SkillResult

Returned after skill execution or recorded when approval is required.

```json
{
  "id": "skill_result_001",
  "skill_call_id": "skill_call_001",
  "skill_name": "ticket.create",
  "status": "success",
  "approval_status": "not_required",
  "output_json": {
    "ticket_id": "tick_001"
  },
  "error": null
}
```

Allowed MVP statuses:

- `success`
- `failed`
- `pending_approval`
- `skipped`

Allowed MVP approval statuses:

- `not_required`
- `pending`
- `approved`
- `rejected`

## OwnerNotification

Produced by the owner agent and consumed by owner gateways or owner sandbox.

```json
{
  "id": "own_001",
  "profile": "startup_saas",
  "customer_id": "cust_123",
  "ticket_id": "tick_001",
  "summary": "Acme Labs has a medium-risk onboarding blocker around Stripe integration.",
  "risk_level": "medium",
  "recommended_action": "Ask technical support to review integration logs.",
  "metadata_json": {}
}
```

Risk levels:

- `low`
- `medium`
- `high`
- `urgent`

## AgentRun

Persisted for debugging and traceability.

```json
{
  "id": "run_001",
  "profile": "startup_saas",
  "agent_name": "technical_support",
  "task_name": "handle_integration_issue",
  "status": "success",
  "input_json": {},
  "output_json": {}
}
```

## PrivateAgentJob

Produced by Wasila when a customer request needs deeper private-assistant work. This is the trust boundary between public customer support and private assistants such as Hermes or OpenClaw.

```json
{
  "job_id": "job_001",
  "customer_id": "cust_123",
  "ticket_id": "tick_001",
  "intent": "build_website",
  "summary": "Customer wants a simple company website.",
  "safe_context": {
    "customer_message": "Saya mau bikin website company profile",
    "business": "Pena Digital",
    "constraints": ["reply in Indonesian", "ask for missing requirements"]
  },
  "forbidden": [
    "do not expose internal memory",
    "do not contact the customer directly",
    "do not execute paid actions without owner approval"
  ]
}
```

## PrivateAgentResult

Returned by a private assistant adapter and filtered by Wasila before customer delivery.

```json
{
  "job_id": "job_001",
  "status": "done",
  "customer_reply": "Bisa kak. Untuk mulai, saya butuh nama bisnis, jumlah halaman, referensi desain, dan deadline.",
  "owner_note": "Lead website baru. Perlu follow-up pricing.",
  "actions_requested": []
}
```

Allowed MVP statuses:

- `done`
- `needs_owner`
- `failed`

Private assistants must not send customer replies themselves. Wasila owns final delivery and trace persistence.

## Contract Rule

Sandbox and real gateways should use the same contracts. This keeps local testing honest and reduces integration drift.
