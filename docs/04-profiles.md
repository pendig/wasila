# Profiles

Profiles package a customer operating model into agents, tasks, prompts, memory rules, and ticket behavior.

## MVP Profile

### `startup_saas`

Use case: a startup or small SaaS company that needs AI support for customer conversations.

Default agents:

- Front office agent.
- Ticket manager agent.
- Technical support agent.
- Owner agent.

Typical work:

- Product questions.
- Onboarding support.
- Bug reports.
- Feature requests.
- Account and integration troubleshooting.
- Churn-risk detection.
- Owner escalation summaries.

## Future Candidate Profiles

### `agency`

For software houses, marketing agencies, and service businesses.

Likely agents: front office, project intake, estimator, account manager, owner.

### `ecommerce`

For online stores.

Likely agents: front office, order support, complaint and refund handler, product advisor, owner.

### `education`

For course, training, and membership businesses.

Likely agents: front office, enrollment advisor, learning support, admin and payment handler, owner.

### `appointment_service`

For clinics, salons, consultants, and appointment-based service businesses.

Likely agents: front office, scheduler, service advisor, follow-up agent, owner.

## Required Profile Rule

Every profile must include an owner agent. Wasila should never optimize customer automation by hiding important customer signals from the business owner.
