# CrewAI Alignment

Wasila uses CrewAI as the default orchestration core. The project should reuse CrewAI features instead of rebuilding them when CrewAI already provides the right primitive.

This document maps Wasila concepts to CrewAI concepts so implementation stays aligned.

## Use CrewAI Directly For

### Agents

CrewAI agents already model role, goal, backstory, tools, memory, delegation, iteration limits, reasoning, and code execution settings.

Wasila profiles should map agent YAML into CrewAI `Agent` configuration rather than inventing a separate runtime.

### Tasks

CrewAI tasks already support descriptions, expected output, context, async execution, human input, callbacks, guardrails, and structured output.

Wasila task YAML should map into CrewAI `Task` configuration.

When Wasila needs structured orchestration output, prefer CrewAI task structured output such as Pydantic or JSON output rather than parsing raw text.

### Crews

CrewAI crews should execute the profile's agent team.

The `startup_saas` profile should become a CrewAI crew with front office, ticket manager, technical support, and owner agents.

### Flows

CrewAI Flows should be used when Wasila needs deterministic lifecycle orchestration, routing, branching, persistence, or resume behavior.

Wasila's workflow lifecycle can start as normal Python orchestration, but the long-term target should map stable lifecycle steps into CrewAI Flows where that improves clarity.

### Tools

CrewAI tools already provide the right primitive for agent capabilities.

Wasila skills should be exposed to CrewAI agents as tools, with Wasila owning permission checks, approval rules, and execution traces around those tool calls.

### Knowledge

CrewAI knowledge sources should be used for business knowledge where practical.

For MVP, Wasila keeps editable Markdown files in `knowledge/`. The CrewAI adapter should load them into CrewAI knowledge sources, likely through string knowledge sources or compatible text-file sources depending on supported formats.

Wasila should keep the editable source files local and human-readable while letting CrewAI handle retrieval when available.

### Memory

CrewAI memory can support short-term and cross-run agent recall.

Wasila still keeps `customer.md` and SQLite because they are product-level customer records, not just agent memory. The CrewAI adapter can pass relevant customer memory into tasks and may use CrewAI memory for agent recall where useful.

## Wasila Owns

Wasila should own the product workflow around CrewAI:

- Customer and owner gateway contracts.
- Customer identity resolution.
- SQLite operational source of truth.
- Per-customer `customer.md` relationship memory.
- Business knowledge source files.
- Ticket lifecycle.
- Owner notification delivery.
- Skill permission and approval policy.
- Idempotency.
- CLI sandbox.
- Repository profile format and extension registry.

CrewAI should own agent execution, task execution, tools, knowledge retrieval, memory primitives, and Flow orchestration where appropriate.

## Implementation Rule

Before implementing a custom orchestration, tool, memory, knowledge, or structured-output mechanism, check whether CrewAI already provides it.

If CrewAI provides it:

- Use CrewAI as the execution primitive.
- Keep Wasila's wrapper focused on customer/business workflow concerns.
- Preserve Wasila's contracts so gateways, storage, and profiles remain stable.

If CrewAI does not provide it:

- Add the smallest Wasila abstraction needed.
- Keep it behind a port or adapter.
- Document why the custom layer exists.

## Current Base Scaffold

The current scaffold intentionally defines Wasila contracts and CLI setup first. It does not implement the CrewAI runner yet.

The next CrewAI-facing implementation should:

- Add the CrewAI adapter behind the `Orchestrator` port.
- Convert profile YAML into CrewAI agents and tasks.
- Expose Wasila skills as CrewAI tools.
- Load business knowledge into CrewAI knowledge sources.
- Return a normalized `OrchestrationResult`.
