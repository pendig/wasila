from __future__ import annotations

from wasila.config.models import GatewayConfig, ProjectConfig, ProviderSettings, RuntimeSettings


def default_config(project_name: str = "my-customer-ai", profile: str = "startup_saas") -> ProjectConfig:
    return ProjectConfig(
        name=project_name,
        profile=profile,
        runtime=RuntimeSettings(),
        provider=ProviderSettings(
            type="openai-compatible",
            base_url="https://api.openai.com/v1",
            model="gpt-4.1-mini",
            api_key_env="OPENAI_API_KEY",
        ),
        customer_gateway=GatewayConfig(type="webhook"),
        owner_gateway=GatewayConfig(type="webhook"),
    )

