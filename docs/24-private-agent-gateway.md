# Private Agent Gateway

Wasila should be a lightweight customer-support frontdesk, not the private assistant itself.

The public customer talks to Wasila. Wasila can delegate sanitized work to Hermes, OpenClaw, Codex, or another private AI assistant. The private assistant returns a structured result. Wasila reviews the result, updates memory or tickets, and sends the final customer reply.

## Default Shape

```text
Customer channel
-> Wasila customer gateway
-> Wasila frontdesk workflow
-> PrivateAgentJob
-> Hermes / OpenClaw / other private assistant
-> PrivateAgentResult
-> Wasila filter + trace
-> Customer reply
```

## MVP Adapter

Use a CLI adapter first. It is boring, debuggable, and works with almost any agent runtime.

```text
wasila writes job.json
wasila runs configured command
assistant writes result.json to stdout
wasila validates result
```

Example command shape:

```bash
wasila assistant add cli --name hermes --command "hermes -p private-assistant"
```

The command is configuration, not a hard dependency. OpenClaw or another agent can use the same JSON contract.

## `PrivateAgentJob`

Send only the context needed for the task. Prefer summaries over raw chat logs.

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

## `PrivateAgentResult`

```json
{
  "job_id": "job_001",
  "status": "done",
  "customer_reply": "Bisa kak. Untuk mulai, saya butuh nama bisnis, jumlah halaman, referensi desain, dan deadline.",
  "owner_note": "Lead website baru. Perlu follow-up pricing.",
  "actions_requested": []
}
```

## Safety Rules

- Customer gateways never call Hermes or OpenClaw directly.
- Private assistants never get customer-channel credentials.
- Private assistants never send customer replies directly.
- Wasila sends summaries and safe context, not unrestricted private memory.
- Wasila validates the result shape before using it.
- Wasila owns final delivery, memory updates, tickets, and owner notifications.

## When To Add Native Integrations

Add a native Hermes or OpenClaw adapter only after the CLI adapter proves the contract. Until then, native plugins are extra surface area without a stable product shape.

Skipped for MVP: streaming, tool passthrough, direct assistant-to-customer messaging, and multi-agent routing. Add them only when the single CLI adapter becomes the bottleneck.