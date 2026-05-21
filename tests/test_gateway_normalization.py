import unittest

from wasila.gateways import TelegramCustomerGateway, WhatsAppCustomerGateway


class GatewayNormalizationTests(unittest.TestCase):
    def test_telegram_normalization_parses_nested_payload(self):
        gateway = TelegramCustomerGateway(metadata={"id": "telegram-webhook"})
        payload = {
            "message": {"text": "How to reset password?"},
            "chat": {"id": "conv_123"},
            "from": {"id": "cust_007", "first_name": "Ari"},
        }

        event = gateway.normalize(payload)
        self.assertEqual(event.gateway, "telegram-webhook")
        self.assertEqual(event.message_text, "How to reset password?")
        self.assertEqual(event.external_customer_id, "cust_007")
        self.assertEqual(event.external_conversation_id, "conv_123")
        self.assertEqual(event.metadata_json["name"], "Ari")

    def test_whatsapp_normalization_parses_nested_messages(self):
        gateway = WhatsAppCustomerGateway(metadata={"id": "wa-webhook"})
        payload = {
            "entry": [
                {
                    "id": "123",
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "6281234567",
                                        "text": {"body": "Need invoice"},
                                    }
                                ],
                            }
                        }
                    ],
                }
            ]
        }

        event = gateway.normalize(payload)
        self.assertEqual(event.gateway, "wa-webhook")
        self.assertEqual(event.message_text, "Need invoice")
        self.assertEqual(event.external_customer_id, "6281234567")
        self.assertEqual(event.external_conversation_id, "6281234567")


if __name__ == "__main__":
    unittest.main()
