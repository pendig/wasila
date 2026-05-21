# Security And Privacy

Wasila handles customer conversations, customer memory, tickets, and owner summaries. Even in the MVP, the project should treat this data carefully.

## MVP Security Principles

- Keep secrets out of committed files.
- Keep customer data local by default.
- Keep business knowledge free from secrets.
- Store only useful durable memory.
- Avoid copying full raw conversations into `customer.md`.
- Make operational traces inspectable.
- Label future security work honestly.

## Secrets

Never commit:

- LLM API keys.
- Gateway tokens.
- Webhook secrets.
- Owner notification URLs.
- Real customer data.
- Private business notes.

Use environment variables or ignored local config.

## Customer Memory

`customer.md` should contain durable, human-readable context. It should not become a raw transcript dump.

Good memory:

```text
Customer prefers concise technical updates and is currently blocked on Stripe integration.
```

Bad memory:

```text
Full copied chat transcript with tokens, private URLs, or payment details.
```

## Business Knowledge

Business knowledge should describe products, policies, support boundaries, owner preferences, and operating rules.

It should not include:

- API keys.
- Private customer data.
- Internal credentials.
- Unredacted private URLs.
- Sensitive owner-only notes that should never be sent into an LLM.

If a business rule is sensitive, prefer a short policy description over raw private detail.

## PII And Sensitive Data

The MVP should not promise automated compliance. It should provide sensible defaults and clear warnings.

Future work should include:

- Redaction rules.
- Retention settings.
- Export and delete commands.
- Audit logs.
- Role-based access for API and web console.

## Webhooks

Webhook integrations should eventually support:

- Shared secret verification.
- Request timestamp validation.
- Replay protection.
- Idempotency keys.

The MVP can start simpler, but docs and code should make the security gap explicit.

## Local Database

SQLite is local operational storage. Users are responsible for securing the host machine and backups.

Future production modes should document:

- Database encryption options.
- Backup strategy.
- Data retention policy.
- Deployment hardening.
