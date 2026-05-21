import unittest

from wasila.gateways import build_customer_gateway, build_owner_gateway


class GatewayTypeTests(unittest.TestCase):
    def test_build_customer_gateway_supports_webhook_and_stage2_customer_types(self):
        customer_gateway = build_customer_gateway("webhook", {"id": "sbx"})
        customer_telegram = build_customer_gateway("telegram", {"id": "tg"})
        customer_whatsapp = build_customer_gateway("whatsapp", {"id": "wa"})
        self.assertEqual(customer_gateway.name, "webhook")
        self.assertEqual(customer_telegram.name, "telegram")
        self.assertEqual(customer_whatsapp.name, "whatsapp")
        self.assertTrue(callable(getattr(customer_gateway, "normalize", None)))
        self.assertTrue(callable(getattr(customer_telegram, "normalize", None)))
        self.assertTrue(callable(getattr(customer_whatsapp, "normalize", None)))

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
