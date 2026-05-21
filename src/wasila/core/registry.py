from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


class RegistryError(KeyError):
    """Raised when a registry lookup fails."""


@dataclass(slots=True)
class Registry(Generic[T]):
    kind: str
    _items: dict[str, T] = field(default_factory=dict)

    def register(self, name: str, item: T) -> None:
        if not name:
            raise ValueError(f"{self.kind} name cannot be empty")
        self._items[name] = item

    def get(self, name: str) -> T:
        try:
            return self._items[name]
        except KeyError as exc:
            available = ", ".join(sorted(self._items)) or "none"
            raise RegistryError(f"Unknown {self.kind} '{name}'. Available: {available}") from exc

    def names(self) -> list[str]:
        return sorted(self._items)


@dataclass(slots=True)
class WasilaRegistries:
    profiles: Registry[object] = field(default_factory=lambda: Registry("profile"))
    customer_gateways: Registry[object] = field(default_factory=lambda: Registry("customer gateway"))
    owner_gateways: Registry[object] = field(default_factory=lambda: Registry("owner gateway"))
    providers: Registry[object] = field(default_factory=lambda: Registry("provider"))
    skills: Registry[object] = field(default_factory=lambda: Registry("skill"))
    runners: Registry[object] = field(default_factory=lambda: Registry("orchestration runner"))

