import unittest

from wasila.gateways import build_customer_gateway, build_owner_gateway


class GatewayTypeTests(unittest.TestCase):
    def test_build_customer_gateway_only_supports_webhook_now(self):
        customer_gateway = build_customer_gateway("webhook", {"id": "sbx"})
        self.assertEqual(customer_gateway.name, "webhook")
        self.assertTrue(callable(getattr(customer_gateway, "normalize", None)))

        with self.assertRaises(ValueError):
            build_customer_gateway("openclaw", {})

    def test_build_owner_gateway_supports_planned_options(self):
        webhook_gateway = build_owner_gateway("webhook", {})
        openclaw_gateway = build_owner_gateway("openclaw", {})
        hermes_gateway = build_owner_gateway("hermes", {})

        self.assertEqual(webhook_gateway.name, "webhook")
        self.assertEqual(openclaw_gateway.name, "openclaw")
        self.assertEqual(hermes_gateway.name, "hermes")
        self.assertTrue(callable(getattr(openclaw_gateway, "deliver", None)))
        self.assertTrue(callable(getattr(hermes_gateway, "deliver", None)))

        with self.assertRaises(ValueError):
            build_owner_gateway("telegram", {})


if __name__ == "__main__":
    unittest.main()
