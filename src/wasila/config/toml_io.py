from __future__ import annotations

import json
import tomllib
from pathlib import Path

from wasila.config.models import (
    AssistantConfig,
    GatewayConfig,
    ProjectConfig,
    ProviderSettings,
    RuntimeSettings,
)


def _as_metadata(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}

    output: dict[str, str] = {}
    for key, value in value.items():
        if isinstance(key, str) and isinstance(value, (str, int, float, bool)):
            output[key] = str(value)
    return output


def _format_metadata(section_name: str, metadata: dict[str, str]) -> str:
    if not metadata:
        return ""

    lines = [f"[{section_name}]", ""]
    for key, value in sorted(metadata.items()):
        escaped = _toml_string(value)
        lines.append(f"{key} = {escaped}")
    return "\n".join(lines) + "\n"


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _as_assistants(value: object) -> dict[str, AssistantConfig]:
    if not isinstance(value, dict):
        return {}

    assistants: dict[str, AssistantConfig] = {}
    for name, raw in value.items():
        if not isinstance(name, str) or not isinstance(raw, dict):
            continue
        command = raw.get("command", [])
        command_valid = isinstance(command, list) and all(
            isinstance(arg, str) for arg in command
        )
        if not command_valid:
            command = []
        raw_type = raw.get("type")
        assistant_type = raw_type if isinstance(raw_type, str) else "cli"
        assistants[name] = AssistantConfig(
            type=assistant_type,
            command=command,
        )
    return assistants


def load_config(path: Path) -> ProjectConfig:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    runtime = data.get("runtime", {})
    provider = data.get("provider", {})
    gateways = data.get("gateways", {})
    if isinstance(gateways, dict):
        customer_gateway = gateways.get("customer", {})
        owner_gateway = gateways.get("owner", {})
    else:
        customer_gateway = {}
        owner_gateway = {}

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
        customer_gateway=GatewayConfig(
            type=customer_gateway.get("type", "webhook"),
            metadata=_as_metadata(customer_gateway.get("metadata", {})),
        ),
        owner_gateway=GatewayConfig(
            type=owner_gateway.get("type", "webhook"),
            metadata=_as_metadata(owner_gateway.get("metadata", {})),
        ),
        assistants=_as_assistants(data.get("assistants", {})),
    )


def dump_config(config: ProjectConfig) -> str:
    customer_metadata = _format_metadata(
        "gateways.customer.metadata",
        config.customer_gateway.metadata,
    )
    owner_metadata = _format_metadata(
        "gateways.owner.metadata",
        config.owner_gateway.metadata,
    )

    lines = [
        "[project]",
        f'name = "{config.name}"',
        f'profile = "{config.profile}"',
        "",
        "[runtime]",
        f'database_path = "{config.runtime.database_path}"',
        f'customer_memory_dir = "{config.runtime.customer_memory_dir}"',
        f'knowledge_dir = "{config.runtime.knowledge_dir}"',
        "",
        "[provider]",
        f'type = "{config.provider.type}"',
        f'base_url = "{config.provider.base_url}"',
        f'model = "{config.provider.model}"',
        f'api_key_env = "{config.provider.api_key_env}"',
        "",
        "[gateways.customer]",
        f'type = "{config.customer_gateway.type}"',
        "",
        "[gateways.owner]",
        f'type = "{config.owner_gateway.type}"',
    ]

    body = "\n".join(lines)
    if customer_metadata:
        body += "\n\n" + customer_metadata.rstrip("\n")
    if owner_metadata:
        body += "\n\n" + owner_metadata.rstrip("\n")
    if config.assistants:
        for name, assistant in sorted(config.assistants.items()):
            command = ", ".join(_toml_string(arg) for arg in assistant.command)
            body += (
                f"\n\n[assistants.{name}]\n"
                f"type = {_toml_string(assistant.type)}\n"
                f"command = [{command}]"
            )

    return body + "\n"


def config_overrides_from_env() -> dict[str, dict[str, str]]:
    """Return non-empty environment overrides in Wasila's standard schema."""

    import os

    overrides: dict[str, dict[str, str]] = {
        "project": {},
        "provider": {},
        "runtime": {},
        "gateways.customer": {},
        "gateways.owner": {},
        "gateways.customer.metadata": {},
        "gateways.owner.metadata": {},
    }

    mapping: dict[str, tuple[str, str]] = {
        "WASILA_PROJECT_NAME": ("project", "name"),
        "WASILA_PROJECT_PROFILE": ("project", "profile"),
        "WASILA_RUNTIME_DATABASE_PATH": ("runtime", "database_path"),
        "WASILA_RUNTIME_CUSTOMER_MEMORY_DIR": ("runtime", "customer_memory_dir"),
        "WASILA_RUNTIME_KNOWLEDGE_DIR": ("runtime", "knowledge_dir"),
        "WASILA_PROVIDER_TYPE": ("provider", "type"),
        "WASILA_PROVIDER_BASE_URL": ("provider", "base_url"),
        "WASILA_PROVIDER_MODEL": ("provider", "model"),
        "WASILA_PROVIDER_API_KEY_ENV": ("provider", "api_key_env"),
        "WASILA_GATEWAY_CUSTOMER_TYPE": ("gateways.customer", "type"),
        "WASILA_GATEWAY_OWNER_TYPE": ("gateways.owner", "type"),
        "WASILA_GATEWAY_CUSTOMER_URL": ("gateways.customer.metadata", "url"),
        "WASILA_GATEWAY_OWNER_URL": ("gateways.owner.metadata", "url"),
    }

    for env_name, (section, key) in mapping.items():
        value = os.getenv(env_name)
        if value:
            overrides[section][key] = value

    metadata_raw = os.getenv("WASILA_GATEWAY_CUSTOMER_METADATA")
    if metadata_raw:
        try:
            parsed = json.loads(metadata_raw)
            if isinstance(parsed, dict):
                for key, value in parsed.items():
                    if isinstance(key, str):
                        overrides["gateways.customer.metadata"][key] = str(value)
        except json.JSONDecodeError:
            pass

    metadata_raw = os.getenv("WASILA_GATEWAY_OWNER_METADATA")
    if metadata_raw:
        try:
            parsed = json.loads(metadata_raw)
            if isinstance(parsed, dict):
                for key, value in parsed.items():
                    if isinstance(key, str):
                        overrides["gateways.owner.metadata"][key] = str(value)
        except json.JSONDecodeError:
            pass

    return {section: values for section, values in overrides.items() if values}
