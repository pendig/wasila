from __future__ import annotations

import json
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

from wasila.core.contracts import CustomerEvent, OwnerNotification
from wasila.core.ports import CustomerGateway, OwnerGateway


class WebhookCustomerGateway(CustomerGateway):
    def __init__(self, metadata: dict[str, str] | None = None) -> None:
        self.name = "webhook"
        self.metadata = metadata or {}

    def normalize(self, payload: dict) -> CustomerEvent:
        raw_text = payload.get("message") or payload.get("text") or payload.get("body") or ""
        if not isinstance(raw_text, str):
            raw_text = ""

        event_id = payload.get("event_id")
        if event_id is not None and not isinstance(event_id, str):
            event_id = str(event_id)

        return CustomerEvent(
            gateway=payload.get("gateway", self.metadata.get("id", "webhook")),
            gateway_role=payload.get("gateway_role", "customer"),
            external_conversation_id=str(payload.get("external_conversation_id") or ""),
            external_customer_id=str(payload.get("external_customer_id") or payload.get("customer_id") or ""),
            message_text=raw_text,
            message_timestamp=payload.get("message_timestamp") or "",
            id=event_id,
            customer_id=payload.get("customer_id"),
            metadata_json={
                "name": payload.get("name") or payload.get("display_name"),
                "source": payload.get("source", "webhook"),
                "raw": payload,
            },
        )


class WebhookOwnerGateway(OwnerGateway):
    def __init__(self, metadata: dict[str, str] | None = None) -> None:
        self.name = "webhook"
        self.metadata = metadata or {}

    def deliver(self, notification: OwnerNotification) -> None:
        endpoint = self.metadata.get("url") or self.metadata.get("endpoint")
        if not endpoint:
            print("[owner-gateway] no URL configured; logged in sqlite only")
            return
        payload = {
            "profile": notification.profile,
            "customer_id": notification.customer_id,
            "ticket_id": notification.ticket_id,
            "summary": notification.summary,
            "risk_level": notification.risk_level,
            "recommended_action": notification.recommended_action,
            "metadata_json": notification.metadata_json,
        }
        request = urllib.request.Request(
            endpoint,
            method="POST",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=3):
                pass
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:  # pragma: no cover - best-effort
            raise RuntimeError(f"owner webhook delivery failed: {exc}")


class WebhookDaemon:
    def __init__(
        self,
        handler: Callable[[dict[str, Any]], dict[str, Any]],
        gateway: CustomerGateway | None = None,
        route_gateways: dict[str, CustomerGateway] | None = None,
        host: str = "127.0.0.1",
        port: int = 8000,
    ):
        self.handler = handler
        self.gateway = gateway or WebhookCustomerGateway()
        self.route_gateways = route_gateways or {}
        self.host = host
        self.port = port

    def start(self) -> None:
        gateway = self.gateway

        class _RequestHandler(BaseHTTPRequestHandler):
            def do_GET(inner_self):  # noqa: N802
                if inner_self.path == "/health":
                    data = {"status": "ok", "service": "wasila"}
                    payload = json.dumps(data).encode("utf-8")
                    inner_self.send_response(200)
                    inner_self.send_header("Content-Type", "application/json")
                    inner_self.send_header("Content-Length", str(len(payload)))
                    inner_self.end_headers()
                    inner_self.wfile.write(payload)
                    return

                inner_self.send_response(404)
                inner_self.end_headers()

            def do_POST(inner_self):  # noqa: N802
                path = inner_self.path.split("?", 1)[0]
                request_gateway = route_gateways_for_path(path)
                if request_gateway is None:
                    inner_self.send_response(404)
                    inner_self.end_headers()
                    return
                length = int(inner_self.headers.get("Content-Length", "0") or "0")
                raw = inner_self.rfile.read(length)
                try:
                    payload = json.loads(raw.decode("utf-8"))
                except json.JSONDecodeError as exc:
                    inner_self.send_response(400)
                    inner_self.end_headers()
                    response = {"ok": False, "error": f"invalid json: {exc}"}
                    raw_response = json.dumps(response).encode("utf-8")
                    inner_self.wfile.write(raw_response)
                    return

                try:
                    event = request_gateway.normalize(payload)
                    outcome = self.handler(event.__dict__)
                except Exception as exc:
                    inner_self.send_response(500)
                    inner_self.end_headers()
                    response = {"ok": False, "error": str(exc)}
                    raw_response = json.dumps(response).encode("utf-8")
                    inner_self.wfile.write(raw_response)
                    return

                body = {
                    "ok": True,
                    "customer_id": event.customer_id,
                    "customer_response": outcome.get("customer_response", ""),
                    "metadata": outcome.get("metadata", {}),
                }
                response = json.dumps(body).encode("utf-8")
                inner_self.send_response(200)
                inner_self.send_header("Content-Type", "application/json")
                inner_self.send_header("Content-Length", str(len(response)))
                inner_self.end_headers()
                inner_self.wfile.write(response)

        print(f"starting webhook daemon on {self.host}:{self.port}")
        httpd = ThreadingHTTPServer((self.host, self.port), _RequestHandler)

        def route_gateways_for_path(path: str) -> CustomerGateway | None:
            if path in {"/webhook/customer", "/customer"}:
                return self.gateway

            if path.startswith("/webhook/"):
                return self.route_gateways.get(path)

            return None

        try:
            httpd.serve_forever()
        finally:
            httpd.server_close()
