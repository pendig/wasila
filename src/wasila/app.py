from __future__ import annotations

from pathlib import Path

from wasila.config.layers import load_config_with_layers
from wasila.config.models import ProjectConfig
from wasila.core.policies import DefaultPolicyEngine
from wasila.core.workflow import Workflow
from wasila.gateways import build_owner_gateway
from wasila.providers import build_orchestrator
from wasila.profiles import ProfileDefinition, load_profile
from wasila.storage import CustomerMarkdownStore, MarkdownKnowledgeLoader, SqliteStorage


def load_project(
    config_path: Path,
    cli_overrides: dict[str, dict[str, str]] | None = None,
    customer_gateway_runtime: str | None = None,
    owner_gateway_runtime: str | None = None,
) -> tuple[ProjectConfig, ProfileDefinition, Workflow]:
    config = load_config_with_layers(config_path=config_path, cli_overrides=cli_overrides)
    if customer_gateway_runtime:
        config.customer_gateway.type = customer_gateway_runtime
    if owner_gateway_runtime:
        config.owner_gateway.type = owner_gateway_runtime

    storage = SqliteStorage(config.runtime)
    storage.initialize()
    memory_store = CustomerMarkdownStore(config.runtime.customer_memory_dir)
    knowledge_loader = MarkdownKnowledgeLoader(config.runtime.knowledge_dir)

    profile = load_profile(config.profile)

    orchestrator = build_orchestrator(profile=profile, provider=config.provider)
    owner_gateway = build_owner_gateway(config.owner_gateway.type, config.owner_gateway.metadata)

    workflow = Workflow(
        config=config,
        profile=profile,
        storage=storage,
        orchestrator=orchestrator,
        memory_store=memory_store,
        knowledge_loader=knowledge_loader,
        owner_gateway=owner_gateway,
        policy=DefaultPolicyEngine(),
    )

    return config, profile, workflow
