# Open Source Readiness

Wasila should be understandable and useful even before it is feature-complete.

## Documentation Standards

- The README should clearly state current status.
- Roadmap items should be labeled as planned, not implied as implemented.
- MVP scope should be narrow and testable.
- Architecture docs should explain extension points before code grows around them.
- Examples should avoid real secrets, private URLs, or private customer data.

## Contribution Model

The project should favor small, well-scoped contributions:

- Add a profile.
- Add a customer gateway.
- Add an owner gateway.
- Add a provider adapter.
- Add a storage migration.
- Improve documentation.
- Add smoke tests.

Each contribution should include documentation when it changes user-facing behavior.

## Extension Points

The primary extension points are:

- Profiles.
- Customer gateways.
- Owner gateways.
- Providers.
- Storage adapters.
- Orchestration runners.

CrewAI is the default runner for the project, but Wasila should keep its own product-level contracts clear so contributors can work on gateways, storage, profiles, and CLI features without needing to rewrite orchestration internals.

## Secrets Policy

Do not commit secrets in:

- Docs.
- Examples.
- Templates.
- Test fixtures.
- Default config.
- Customer memory files.

Use environment variables or local ignored config for API keys and gateway credentials.

## Future Repository Files

Before a public release, the repository should include:

- `LICENSE`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- Issue templates.
- Pull request template.
- Local development guide.
- Smoke test guide.
