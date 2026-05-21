from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ProfileDefinition:
    id: str
    name: str
    description: str
    required_agents: list[str]
    default_customer_gateway: str
    default_owner_gateway: str
    agents: dict[str, dict[str, Any]]
    tasks: dict[str, dict[str, Any]]
    prompts: dict[str, str]
    skills: dict[str, dict[str, Any]]
    allowed_skills: list[str]

    def allowed_skill_names(self) -> list[str]:
        return self.allowed_skills


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Profile parsing requires PyYAML. Install with: pip install -e \".[crewai]\""
        ) from exc

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected dict in profile file {path}")
    return data


def _read_prompt_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def load_profile(profile_name: str, base_dir: Path | None = None) -> ProfileDefinition:
    root = Path(__file__).resolve().parent if base_dir is None else Path(base_dir)
    profile_dir = root / profile_name
    if not profile_dir.is_dir():
        raise FileNotFoundError(f"Profile '{profile_name}' not found at {profile_dir}")

    profile_yaml = _load_yaml(profile_dir / "profile.yaml")
    agents_yaml = _load_yaml(profile_dir / "agents.yaml")
    tasks_yaml = _load_yaml(profile_dir / "tasks.yaml")
    skills_yaml = _load_yaml(profile_dir / "skills.yaml")

    prompts_dir = profile_dir / "prompts"
    prompts: dict[str, str] = {
        "front_office": _read_prompt_file(prompts_dir / "front_office.md"),
        "ticket_manager": _read_prompt_file(prompts_dir / "ticket_manager.md"),
        "technical_support": _read_prompt_file(prompts_dir / "technical_support.md"),
        "owner": _read_prompt_file(prompts_dir / "owner.md"),
    }

    required_agents = profile_yaml.get("required_agents", [])
    if not isinstance(required_agents, list):
        raise ValueError("required_agents must be list")

    allowed_skills = profile_yaml.get("allowed_skills", [])
    if not isinstance(allowed_skills, list):
        raise ValueError("allowed_skills must be list")

    return ProfileDefinition(
        id=str(profile_yaml.get("id", profile_name)),
        name=str(profile_yaml.get("name", profile_name)),
        description=str(profile_yaml.get("description", "")),
        required_agents=[str(name) for name in required_agents],
        default_customer_gateway=str(profile_yaml.get("default_customer_gateway", "webhook")),
        default_owner_gateway=str(profile_yaml.get("default_owner_gateway", "webhook")),
        agents={key: dict(value or {}) for key, value in agents_yaml.items()},
        tasks={key: dict(value or {}) for key, value in tasks_yaml.items()},
        prompts={key: value for key, value in prompts.items() if value},
        skills={key: dict(value or {}) for key, value in skills_yaml.items()},
        allowed_skills=[str(name) for name in allowed_skills],
    )
