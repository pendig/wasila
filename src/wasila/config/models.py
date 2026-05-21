from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RuntimeSettings:
    database_path: str = "data/wasila.sqlite3"
    customer_memory_dir: str = "data/customers"
    knowledge_dir: str = "knowledge"


@dataclass(slots=True)
class ProviderSettings:
    type: str = "openai-compatible"
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4.1-mini"
    api_key_env: str = "OPENAI_API_KEY"


@dataclass(slots=True)
class GatewayConfig:
    type: str = "webhook"
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ProjectConfig:
    name: str
    profile: str
    runtime: RuntimeSettings
    provider: ProviderSettings
    customer_gateway: GatewayConfig
    owner_gateway: GatewayConfig

