# Configuration

Wasila should keep configuration explicit and local-first.

## Configuration Goals

- Make the active profile easy to identify.
- Keep customer and owner gateways separate.
- Keep secrets out of committed files.
- Make local data paths predictable.
- Make business knowledge paths explicit.
- Allow future API and web daemon settings without changing the MVP contract.

## Suggested Local Config

The MVP can use a local ignored config file:

```text
.wasila/config.toml
```

Suggested shape:

```toml
[project]
name = "my-customer-ai"
profile = "startup_saas"

[runtime]
database_path = "data/wasila.sqlite3"
customer_memory_dir = "data/customers"
knowledge_dir = "knowledge"

[provider]
type = "openai-compatible"
base_url = "https://api.openai.com/v1"
model = "openai/gpt-4.1-mini"
api_key_env = "OPENAI_API_KEY"

[gateways.customer]
type = "webhook"

[gateways.owner]
type = "webhook"
```

## Secrets

Secrets should live in environment variables or local ignored files.

Examples:

```bash
OPENAI_API_KEY=
WASILA_OWNER_WEBHOOK_URL=
WASILA_CUSTOMER_WEBHOOK_SECRET=
```

Do not commit real API keys, gateway tokens, webhook secrets, or customer data.

## Provider Configuration

Wasila should support any OpenAI-compatible API provider.

The MVP provider contract should require:

- `type = "openai-compatible"`
- `base_url`
- `model`
- `api_key_env`

Example for OpenAI's official API:

```toml
[provider]
type = "openai-compatible"
base_url = "https://api.openai.com/v1"
model = "openai/gpt-4.1-mini"
api_key_env = "OPENAI_API_KEY"
```

Example for a custom compatible endpoint:

```toml
[provider]
type = "openai-compatible"
base_url = "http://localhost:4000/v1"
model = "my-model"
api_key_env = "CUSTOM_OPENAI_COMPATIBLE_API_KEY"
```

This lets users connect OpenAI, compatible hosted providers, local proxies, or internal model gateways without changing Wasila's orchestration code.

## Runtime Paths

Suggested local paths:

```text
data/
  wasila.sqlite3
  customers/
    cust_123/
      customer.md
knowledge/
  business.md
  products.md
  policies.md
  support.md
  owner.md
```

Suggested ignored paths:

```text
.env
.wasila/
data/
```

## Knowledge Configuration

The MVP should support a local business knowledge base.

Suggested command:

```bash
wasila kb init
```

The command should create starter Markdown files under `knowledge/`.

The first implementation can load all knowledge files into the orchestration context. Later versions can add indexing, search, embeddings, or remote knowledge sources.

## Gateway Configuration

Customer gateway config and owner gateway config must be independent.

This allows a setup such as:

```text
Customer: WhatsApp
Owner: OpenClaw
```

or:

```text
Customer: Telegram
Owner: Hermes
```

The MVP starts with webhook for both roles.

## Future Configuration

Future config can add:

- API bind host and port.
- Web console bind host and port.
- Queue settings.
- Retention settings.
- Redaction settings.
- Provider fallback settings.
