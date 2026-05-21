"""Gateway adapters."""

from __future__ import annotations

from typing import Any

from wasila.core.ports import CustomerGateway, OwnerGateway

from wasila.gateways.webhook import WebhookCustomerGateway, WebhookOwnerGateway


class OpenClawOwnerGateway(WebhookOwnerGateway):
    """Owner gateway adapter for OpenClaw.

    Stage 1 uses the same HTTP transport contract as webhook.
    """

    def __init__(self, metadata: dict[str, str] | None = None) -> None:
        super().__init__(metadata=metadata)
        self.name = "openclaw"


class HermesOwnerGateway(WebhookOwnerGateway):
    """Owner gateway adapter for Hermes.

    Stage 1 shares the same payload transport as webhook while keeping
    configuration explicit by gateway type.
    """

    def __init__(self, metadata: dict[str, str] | None = None) -> None:
        super().__init__(metadata=metadata)
        self.name = "hermes"


def build_customer_gateway(gateway_type: str, metadata: dict[str, str] | None = None) -> CustomerGateway:
    if gateway_type == "webhook":
        return WebhookCustomerGateway(metadata=metadata)
    raise ValueError(f"unsupported customer gateway type: {gateway_type}")


def build_owner_gateway(gateway_type: str, metadata: dict[str, str] | None = None) -> OwnerGateway:
    if gateway_type == "webhook":
        return WebhookOwnerGateway(metadata=metadata)
    if gateway_type == "openclaw":
        return OpenClawOwnerGateway(metadata=metadata)
    if gateway_type == "hermes":
        return HermesOwnerGateway(metadata=metadata)

    raise ValueError(f"unsupported owner gateway type: {gateway_type}")


__all__ = [
    "WebhookCustomerGateway",
    "WebhookOwnerGateway",
    "OpenClawOwnerGateway",
    "HermesOwnerGateway",
    "build_customer_gateway",
    "build_owner_gateway",
]
