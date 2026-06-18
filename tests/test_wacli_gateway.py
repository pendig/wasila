import subprocess
import unittest
from unittest.mock import patch

from wasila.gateways import build_customer_gateway
from wasila.gateways.wacli import WacliCustomerGateway


class WacliGatewayTests(unittest.TestCase):
    def test_normalize_sample_inbound_message(self):
        gateway = WacliCustomerGateway()

        event = gateway.normalize(
            {
                "id": "wamid.1",
                "from": "+628123",
                "text": "Halo Wasila",
                "timestamp": "2026-06-18T11:00:00Z",
            }
        )

        self.assertEqual(event.gateway, "wacli")
        self.assertEqual(event.external_customer_id, "+628123")
        self.assertEqual(event.external_conversation_id, "+628123")
        self.assertEqual(event.message_text, "Halo Wasila")
        self.assertEqual(event.id, "wamid.1")
        self.assertEqual(event.metadata_json["source"], "wacli")

    def test_send_reply_uses_safe_subprocess_wrapper(self):
        gateway = WacliCustomerGateway(command=["wacli-test"])

        with patch("wasila.gateways.wacli.subprocess.run") as run:
            gateway.send_reply("+628123", "Siap")

        run.assert_called_once_with(
            ["wacli-test", "send", "+628123", "Siap"],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        )

    def test_normalize_missing_timestamp_falls_back_to_now(self):
        event = WacliCustomerGateway().normalize(
            {"id": "wamid.1", "from": "+628123", "text": "Halo Wasila"}
        )

        self.assertTrue(event.message_timestamp.endswith("Z"))

    def test_normalize_preserves_zero_timestamp(self):
        event = WacliCustomerGateway().normalize({"from": "+628123", "text": "Halo", "timestamp": 0})

        self.assertEqual(event.message_timestamp, "0")

    def test_normalize_missing_chat_id_raises_value_error(self):
        with self.assertRaises(ValueError):
            WacliCustomerGateway().normalize({"id": "wamid.1", "text": "Halo Wasila"})

    def test_normalize_skips_non_string_text_fallback(self):
        event = WacliCustomerGateway().normalize({"from": "+628123", "text": {"bad": True}, "body": "fallback"})

        self.assertEqual(event.message_text, "fallback")

    def test_send_reply_raises_runtime_error_on_failure(self):
        gateway = WacliCustomerGateway(command=["wacli-test"])

        with patch("wasila.gateways.wacli.subprocess.run") as run:
            run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd=["wacli-test", "send"],
                stderr="Error: connection failed",
            )
            with self.assertRaises(RuntimeError) as ctx:
                gateway.send_reply("+628123", "Siap")

        self.assertIn("wacli command failed with exit code 1: Error: connection failed", str(ctx.exception))

    def test_send_reply_raises_runtime_error_on_timeout(self):
        gateway = WacliCustomerGateway(command=["wacli-test"])

        with patch("wasila.gateways.wacli.subprocess.run") as run:
            run.side_effect = subprocess.TimeoutExpired(cmd=["wacli-test", "send"], timeout=15)
            with self.assertRaises(RuntimeError) as ctx:
                gateway.send_reply("+628123", "Siap")

        self.assertIn("wacli command timed out", str(ctx.exception))

    def test_send_reply_raises_runtime_error_when_command_missing(self):
        gateway = WacliCustomerGateway(command=["wacli-test"])

        with patch("wasila.gateways.wacli.subprocess.run") as run:
            run.side_effect = OSError("not found")
            with self.assertRaises(RuntimeError) as ctx:
                gateway.send_reply("+628123", "Siap")

        self.assertIn("wacli command could not be executed", str(ctx.exception))

    def test_build_customer_gateway_supports_wacli(self):
        gateway = build_customer_gateway("wacli", {"command": "wacli-test"})

        self.assertIsInstance(gateway, WacliCustomerGateway)
        self.assertEqual(getattr(gateway, "command"), ["wacli-test"])


if __name__ == "__main__":
    unittest.main()
