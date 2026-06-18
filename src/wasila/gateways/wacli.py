from __future__ import annotations

import subprocess
from typing import Any

from wasila.core.contracts import CustomerEvent, utc_now_iso
from wasila.core.ports import CustomerGateway


class WacliCustomerGateway(CustomerGateway):
    def __init__(self, command: list[str] | None = None) -> None:
        self.name = "wacli"
        self.command = command or ["wacli"]

    def normalize(self, payload: dict[str, Any]) -> CustomerEvent:
        chat_id = str(payload.get("chat_id") or payload.get("from") or payload.get("phone") or "")
        if not chat_id:
            raise ValueError("wacli payload missing chat_id, from, or phone")
        text = payload.get("text") or payload.get("message") or payload.get("body") or ""
        if not isinstance(text, str):
            text = ""
        event_id = payload.get("id") or payload.get("message_id")
        timestamp = payload.get("timestamp")
        return CustomerEvent(
            gateway="wacli",
            external_conversation_id=chat_id,
            external_customer_id=chat_id,
            message_text=text,
            message_timestamp=str(timestamp) if timestamp else utc_now_iso(),
            id=str(event_id) if event_id is not None else None,
            metadata_json={"source": "wacli", "raw": payload},
        )

    def send_reply(self, chat_id: str, text: str) -> None:
        if not chat_id.strip() or not text.strip():
            raise ValueError("wacli reply needs chat_id and text")
        try:
            subprocess.run(
                [*self.command, "send", chat_id, text],
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15,
            )
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip() if exc.stderr else ""
            raise RuntimeError(f"wacli command failed with exit code {exc.returncode}: {stderr}") from exc
