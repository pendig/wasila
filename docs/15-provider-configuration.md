# Provider Configuration

Wasila should support any LLM provider that CrewAI can configure through its `LLM` primitive.

OpenAI's official API can be the default example, but the project should not assume it is the only provider. Wasila should translate project config into CrewAI `LLM(...)` settings instead of creating its own provider HTTP client.

## MVP Provider Contract

Required fields:

- `type`
- `base_url`
- `model`
- `api_key_env`

Suggested config:

```toml
[provider]
type = "openai-compatible"
base_url = "https://api.openai.com/v1"
model = "openai/gpt-4.1-mini"
api_key_env = "OPENAI_API_KEY"
```

## Custom Compatible Provider

Example:

```toml
[provider]
type = "openai-compatible"
base_url = "http://localhost:4000/v1"
model = "my-custom-model"
api_key_env = "CUSTOM_OPENAI_COMPATIBLE_API_KEY"
```

This can represent:

- A hosted OpenAI-compatible provider.
- A LiteLLM-style proxy.
- A local inference gateway.
- An internal company model router.

## CrewAI Mapping

Wasila provider config maps to CrewAI like this:

```python
from crewai import LLM

llm = LLM(
    model="openai/gpt-4.1-mini",
    base_url="https://api.openai.com/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
)
```

The `api_key_env` setting stores the environment variable name only. The adapter reads that value at runtime and passes it to CrewAI when present.

CrewAI also supports provider-prefixed model names such as `openai/...`, `anthropic/...`, `google/...`, and other providers through its documented LLM support. Wasila should keep provider details in config and let CrewAI handle execution.

## CLI

Suggested MVP command:

```bash
wasila provider set openai-compatible \
  --base-url https://api.openai.com/v1 \
  --model openai/gpt-4.1-mini \
  --api-key-env OPENAI_API_KEY
```

Suggested custom endpoint:

```bash
wasila provider set openai-compatible \
  --base-url http://localhost:4000/v1 \
  --model my-custom-model \
  --api-key-env CUSTOM_OPENAI_COMPATIBLE_API_KEY
```

## Rules

- Never write API key values into committed config.
- Store only the environment variable name in config.
- Keep provider config separate from gateway config.
- Keep provider behavior swappable without changing profile definitions.

## Future Work

Future provider work can add:

- Provider health checks.
- Model capability metadata.
- Fallback models.
- Cost tracking.
- Per-agent model selection.
- Per-task model overrides.
