from __future__ import annotations

import tomllib
from pathlib import Path

from wasila.config.models import GatewayConfig, ProjectConfig, ProviderSettings, RuntimeSettings


def load_config(path: Path) -> ProjectConfig:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    runtime = data.get("runtime", {})
    provider = data.get("provider", {})
    gateways = data.get("gateways", {})

    return ProjectConfig(
        name=project.get("name", "my-customer-ai"),
        profile=project.get("profile", "startup_saas"),
        runtime=RuntimeSettings(
            database_path=runtime.get("database_path", "data/wasila.sqlite3"),
            customer_memory_dir=runtime.get("customer_memory_dir", "data/customers"),
            knowledge_dir=runtime.get("knowledge_dir", "knowledge"),
        ),
        provider=ProviderSettings(
            type=provider.get("type", "openai-compatible"),
            base_url=provider.get("base_url", "https://api.openai.com/v1"),
            model=provider.get("model", "openai/gpt-4.1-mini"),
            api_key_env=provider.get("api_key_env", "OPENAI_API_KEY"),
        ),
        customer_gateway=GatewayConfig(type=gateways.get("customer", {}).get("type", "webhook")),
        owner_gateway=GatewayConfig(type=gateways.get("owner", {}).get("type", "webhook")),
    )


def dump_config(config: ProjectConfig) -> str:
    return f"""[project]
name = "{config.name}"
profile = "{config.profile}"

[runtime]
database_path = "{config.runtime.database_path}"
customer_memory_dir = "{config.runtime.customer_memory_dir}"
knowledge_dir = "{config.runtime.knowledge_dir}"

[provider]
type = "{config.provider.type}"
base_url = "{config.provider.base_url}"
model = "{config.provider.model}"
api_key_env = "{config.provider.api_key_env}"

[gateways.customer]
type = "{config.customer_gateway.type}"

[gateways.owner]
type = "{config.owner_gateway.type}"
"""
