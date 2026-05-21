# Profile Template

Profiles package a customer operating model into agents, tasks, prompts, rules, and defaults.

The MVP profile is `startup_saas`, but the repository should make future profiles easy to add.

## Suggested Structure

```text
profiles/
  startup_saas/
    profile.yaml
    agents.yaml
    tasks.yaml
    prompts/
      front_office.md
      ticket_manager.md
      technical_support.md
      owner.md
    skills.yaml
```

## `profile.yaml`

Suggested fields:

```yaml
id: startup_saas
name: Startup SaaS
description: Customer AI team for small software companies.
required_agents:
  - front_office
  - ticket_manager
  - technical_support
  - owner
default_customer_gateway: webhook
default_owner_gateway: webhook
allowed_skills:
  - ticket.create
  - ticket.update
  - memory.suggest_update
  - owner.notify
```

## `agents.yaml`

Suggested fields per agent:

```yaml
front_office:
  role: Front Office Agent
  goal: Understand the customer message and route it to the right next step.
  backstory: Handles first response, intake, tone, and routing.
  max_iter: 3
  allowed_skills:
    - ticket.create
    - ticket.update
```

## `tasks.yaml`

Suggested fields per task:

```yaml
triage_customer_message:
  agent: front_office
  description: Classify the customer message, identify missing context, and decide next action.
  expected_output: A concise customer response and routing decision.
```

## Prompt Files

Prompt files should define behavior that is easier to maintain in Markdown than YAML.

Each prompt should include:

- Role boundaries.
- Tone.
- Required context.
- Escalation rules.
- Output expectations.

## `skills.yaml`

Suggested fields:

```yaml
ticket.create:
  description: Create a customer ticket.
  execution_level: write
  approval_required: false

owner.notify:
  description: Send an owner-facing summary or escalation.
  execution_level: write
  approval_required: false

billing.refund:
  description: Request or issue a refund through a billing system.
  execution_level: external
  approval_required: true
```

Profiles should only expose skills that are relevant to that operating model.

## Required Profile Rule

Every profile must include an owner agent.

The owner agent is responsible for producing owner-facing summaries, risk signals, and recommended actions.

## Profile Acceptance Criteria

A profile is ready when:

- It defines all required agents.
- It defines task behavior.
- It documents memory update behavior.
- It documents owner escalation behavior.
- It documents allowed skills and approval requirements.
- It can run through the CLI sandbox.
