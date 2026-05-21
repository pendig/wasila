"""Gateway adapters."""

from __future__ import annotations

from wasila.core.contracts import CustomerEvent
from wasila.core.ports import CustomerGateway, OwnerGateway

from wasila.gateways.webhook import WebhookCustomerGateway, WebhookOwnerGateway


class TelegramCustomerGateway(WebhookCustomerGateway):
    """Customer gateway adapter for Telegram payloads.

    Stage 2 keeps Telegram transport compatible with webhook payload ingestion.
    """

    def __init__(self, metadata: dict[str, str] | None = None) -> None:
        super().__init__(metadata=metadata)
        self.name = "telegram"

    def normalize(self, payload: dict) -> CustomerEvent:
        message = payload.get("message")
        raw_text = message if isinstance(message, str) else (
            message.get("text")
            if isinstance(message, dict)
            else ""
        )
        if raw_text == "" and isinstance(message, dict):
            raw_text = message.get("body") or message.get("caption") or ""
        if raw_text == "":
            raw_text = payload.get("text") or payload.get("body") or ""

        if not isinstance(raw_text, str):
            raw_text = ""

        sender = payload.get("from")
        if not isinstance(sender, dict):
            sender = payload.get("sender")

        event_id = payload.get("event_id")
        if event_id is not None and not isinstance(event_id, str):
            event_id = str(event_id)
        sender_id = ""
        sender_name = ""
        if isinstance(sender, dict):
            sender_id = str(
                sender.get("id")
                or sender.get("username")
                or sender.get("first_name")
                or ""
            )
            sender_name = str(sender.get("first_name") or sender.get("username") or "")

        return CustomerEvent(
            gateway=payload.get("gateway", self.metadata.get("id", "telegram")),
            gateway_role=payload.get("gateway_role", "customer"),
            external_conversation_id=str(payload.get("chat", {}).get("id") or payload.get("conversation_id") or ""),
            external_customer_id=str(payload.get("external_customer_id") or payload.get("customer_id") or sender_id or ""),
            message_text=raw_text,
            message_timestamp=payload.get("message_timestamp") or "",
            id=event_id,
            customer_id=payload.get("customer_id"),
            metadata_json={
                "name": sender_name or payload.get("name") or payload.get("display_name"),
                "source": "telegram",
                "raw": payload,
            },
        )


class WhatsAppCustomerGateway(WebhookCustomerGateway):
    """Customer gateway adapter for WhatsApp payloads.

    Stage 2 keeps WhatsApp transport compatible with webhook payload ingestion.
    """

    def __init__(self, metadata: dict[str, str] | None = None) -> None:
        super().__init__(metadata=metadata)
        self.name = "whatsapp"

    def normalize(self, payload: dict) -> CustomerEvent:
        raw_text = payload.get("message") or payload.get("body") or ""
        raw_msg: dict | None = None
        if isinstance(payload.get("entry"), list) and payload["entry"]:
            first_entry = payload["entry"][0]
            if isinstance(first_entry, dict):
                changes = first_entry.get("changes")
                if isinstance(changes, list) and changes:
                    raw_msg = changes[0]
                if isinstance(raw_msg, dict):
                    value = raw_msg.get("value")
                    if isinstance(value, dict):
                        messages = value.get("messages")
                        if isinstance(messages, list) and messages:
                            raw_msg = messages[0]
                if isinstance(raw_msg, dict):
                    text_candidate = (
                        raw_msg.get("text")
                        if isinstance(raw_msg.get("text"), str)
                        else (
                            raw_msg.get("text", {}).get("body")
                            if isinstance(raw_msg.get("text"), dict)
                            else None
                        )
                    )
                    if isinstance(text_candidate, str):
                        raw_text = text_candidate
                    else:
                        raw_text = raw_msg.get("message") or raw_msg.get("body") or raw_text

                    payload["from"] = raw_msg.get("from", first_entry.get("from"))

        if isinstance(raw_text, dict):
            raw_text = ""
        if not isinstance(raw_text, str):
            raw_text = str(raw_text)

        event_id = payload.get("event_id")
        if event_id is not None and not isinstance(event_id, str):
            event_id = str(event_id)

        sender = payload.get("from")
        sender_id = ""
        sender_name = ""
        if isinstance(sender, dict):
            sender_id = str(
                sender.get("id")
                or sender.get("wa_id")
                or sender.get("phone")
                or sender.get("username")
                or ""
            )
            sender_name = str(sender.get("name") or sender.get("profile_name") or sender_id)
        else:
            sender_id = str(sender or "")

        return CustomerEvent(
            gateway=payload.get("gateway", self.metadata.get("id", "whatsapp")),
            gateway_role=payload.get("gateway_role", "customer"),
            external_conversation_id=str(payload.get("conversation_id") or payload.get("wa_id") or sender_id or ""),
            external_customer_id=str(payload.get("external_customer_id") or payload.get("customer_id") or sender_id or ""),
            message_text=raw_text,
            message_timestamp=payload.get("message_timestamp") or "",
            id=event_id,
            customer_id=payload.get("customer_id"),
            metadata_json={
                "name": sender_name or payload.get("name") or payload.get("display_name"),
                "source": "whatsapp",
                "raw": payload,
            },
        )


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
    if gateway_type == "telegram":
        return TelegramCustomerGateway(metadata=metadata)
    if gateway_type == "whatsapp":
        return WhatsAppCustomerGateway(metadata=metadata)
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
    "TelegramCustomerGateway",
    "WhatsAppCustomerGateway",
    "OpenClawOwnerGateway",
    "HermesOwnerGateway",
    "build_customer_gateway",
    "build_owner_gateway",
]
