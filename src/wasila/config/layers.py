from __future__ import annotations

from pathlib import Path

from wasila.config.defaults import default_config
from wasila.config.models import GatewayConfig, ProjectConfig, ProviderSettings, RuntimeSettings
from wasila.config.toml_io import config_overrides_from_env, load_config


def _merge_dict_values(source: dict[str, str], target: dict[str, str]) -> None:
    for key, value in source.items():
        target[key] = value


def load_config_with_layers(
    config_path: Path,
    cli_overrides: dict[str, str] | None = None,
) -> ProjectConfig:
    project = default_config()

    if config_path.exists():
        project = load_config(config_path)

    for section, values in config_overrides_from_env().items():
        if section == "project":
            project.name = values.get("name", project.name)
            project.profile = values.get("profile", project.profile)
        elif section == "runtime":
            if values.get("database_path"):
                project.runtime.database_path = values["database_path"]
            if values.get("customer_memory_dir"):
                project.runtime.customer_memory_dir = values["customer_memory_dir"]
            if values.get("knowledge_dir"):
                project.runtime.knowledge_dir = values["knowledge_dir"]
        elif section == "provider":
            project.provider = ProviderSettings(
                type=values.get("type", project.provider.type),
                base_url=values.get("base_url", project.provider.base_url),
                model=values.get("model", project.provider.model),
                api_key_env=values.get("api_key_env", project.provider.api_key_env),
            )
        elif section == "gateways.customer":
            project.customer_gateway = GatewayConfig(
                type=values.get("type", project.customer_gateway.type),
                metadata=project.customer_gateway.metadata.copy(),
            )
            if values.get("type"):
                project.customer_gateway.type = values["type"]
        elif section == "gateways.owner":
            project.owner_gateway = GatewayConfig(
                type=values.get("type", project.owner_gateway.type),
                metadata=project.owner_gateway.metadata.copy(),
            )
            if values.get("type"):
                project.owner_gateway.type = values["type"]
        elif section == "gateways.customer.metadata":
            merged = project.customer_gateway.metadata.copy()
            _merge_dict_values(values, merged)
            project.customer_gateway = GatewayConfig(type=project.customer_gateway.type, metadata=merged)
        elif section == "gateways.owner.metadata":
            merged = project.owner_gateway.metadata.copy()
            _merge_dict_values(values, merged)
            project.owner_gateway = GatewayConfig(type=project.owner_gateway.type, metadata=merged)

    if cli_overrides:
        for section, values in cli_overrides.items():
            section_values = values or {}
            if not section_values:
                continue
            if section == "project":
                if section_values.get("name"):
                    project.name = section_values["name"]
                if section_values.get("profile"):
                    project.profile = section_values["profile"]
            elif section == "runtime":
                if section_values.get("database_path"):
                    project.runtime.database_path = section_values["database_path"]
                if section_values.get("customer_memory_dir"):
                    project.runtime.customer_memory_dir = section_values["customer_memory_dir"]
                if section_values.get("knowledge_dir"):
                    project.runtime.knowledge_dir = section_values["knowledge_dir"]
            elif section == "provider":
                project.provider = ProviderSettings(
                    type=section_values.get("type", project.provider.type),
                    base_url=section_values.get("base_url", project.provider.base_url),
                    model=section_values.get("model", project.provider.model),
                    api_key_env=section_values.get("api_key_env", project.provider.api_key_env),
                )
            elif section.startswith("gateways.customer"):
                project.customer_gateway = GatewayConfig(
                    type=section_values.get("type", project.customer_gateway.type),
                    metadata=project.customer_gateway.metadata.copy(),
                )
                if section_values.get("type"):
                    project.customer_gateway.type = section_values["type"]
                if section == "gateways.customer.metadata":
                    metadata = project.customer_gateway.metadata.copy()
                    metadata.update(section_values)
                    project.customer_gateway = GatewayConfig(
                        type=project.customer_gateway.type,
                        metadata=metadata,
                    )
            elif section.startswith("gateways.owner"):
                project.owner_gateway = GatewayConfig(
                    type=section_values.get("type", project.owner_gateway.type),
                    metadata=project.owner_gateway.metadata.copy(),
                )
                if section_values.get("type"):
                    project.owner_gateway.type = section_values["type"]
                if section == "gateways.owner.metadata":
                    metadata = project.owner_gateway.metadata.copy()
                    metadata.update(section_values)
                    project.owner_gateway = GatewayConfig(
                        type=project.owner_gateway.type,
                        metadata=metadata,
                    )

    return project
