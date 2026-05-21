import json
import socket
import threading
import time
import unittest
from contextlib import closing
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from wasila.core.contracts import CustomerEvent
from wasila.gateways.webhook import WebhookCustomerGateway, WebhookDaemon


def _free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_service(port: int) -> None:
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            with urlopen(f"http://127.0.0.1:{port}/health", timeout=0.5):
                return
        except Exception:
            time.sleep(0.05)
    raise AssertionError("daemon did not become healthy in time")


class WebhookDaemonTests(unittest.TestCase):
    def test_webhook_customer_endpoint_accepts_message(self) -> None:
        captured: list[CustomerEvent] = []
        gateway = WebhookCustomerGateway(metadata={"id": "webhook-it"})
        port = _free_port()

        def handle(event: CustomerEvent) -> dict[str, object]:
            captured.append(event)
            return {
                "customer_response": "ok",
                "metadata": {"received": event.external_customer_id},
                "customer_id": event.customer_id,
            }

        daemon = WebhookDaemon(
            handler=handle,
            gateway=gateway,
            host="127.0.0.1",
            port=port,
        )
        thread = threading.Thread(target=daemon.start, daemon=True)
        thread.start()

        try:
            _wait_for_service(port)
            request = Request(
                f"http://127.0.0.1:{port}/webhook/customer",
                method="POST",
                data=json.dumps(
                    {
                        "message": "Hello",
                        "customer_id": "cust_001",
                        "external_customer_id": "cust_ext_001",
                    },
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urlopen(request, timeout=2) as response:
                body = json.loads(response.read().decode("utf-8"))

            self.assertEqual(response.status, 200)
            self.assertTrue(body["ok"])
            self.assertEqual(body["customer_id"], "cust_001")
            self.assertEqual(len(captured), 1)
            self.assertEqual(captured[0].external_customer_id, "cust_ext_001")
        finally:
            daemon.stop()
            thread.join(timeout=1.0)

    def test_webhook_customer_endpoint_rejects_empty_body(self) -> None:
        gateway = WebhookCustomerGateway(metadata={"id": "webhook-it"})
        port = _free_port()

        def handle(event: CustomerEvent) -> dict[str, object]:
            self.fail("handler should not be called for empty body")
            return {}

        daemon = WebhookDaemon(
            handler=handle,
            gateway=gateway,
            host="127.0.0.1",
            port=port,
        )
        thread = threading.Thread(target=daemon.start, daemon=True)
        thread.start()

        try:
            _wait_for_service(port)
            request = Request(
                f"http://127.0.0.1:{port}/webhook/customer",
                method="POST",
                data=b"",
                headers={"Content-Type": "application/json"},
            )
            with self.assertRaises(HTTPError) as context:
                urlopen(request, timeout=2)
            self.assertEqual(context.exception.code, 400)
        finally:
            daemon.stop()
            thread.join(timeout=1.0)


if __name__ == "__main__":
    unittest.main()
