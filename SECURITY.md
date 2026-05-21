# Security Policy

Wasila is early-stage software and is not yet production hardened.

## Reporting Security Issues

Please report security issues privately to the project maintainers once a public maintainer contact exists.

Until then, do not publish exploit details in public issues.

## Current Security Scope

The MVP is local-first and intended for development, demos, and early pilots.

Known areas that need hardening before serious production use:

- Webhook signature verification.
- Request replay protection.
- Secret redaction.
- Data retention controls.
- Customer data export and delete flows.
- API authentication and authorization.
- Web console access control.

## Secrets Guidance

Do not commit real secrets or customer data. Use environment variables or ignored local config files.
