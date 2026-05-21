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

    def test_telegram_normalization_handles_nested_sender_and_external_conversation(self):
        gateway = TelegramCustomerGateway(metadata={"id": "telegram-webhook"})
        payload = {
            "external_conversation_id": "canonical_conv",
            "message": {"text": "Status update", "from": {"id": "cust_nested", "first_name": "Bima"}},
            "chat": None,
        }

        event = gateway.normalize(payload)
        self.assertEqual(event.external_customer_id, "cust_nested")
        self.assertEqual(event.external_conversation_id, "canonical_conv")
        self.assertEqual(event.message_text, "Status update")

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

    def test_whatsapp_normalization_uses_nested_event_id_and_external_conversation(self):
        gateway = WhatsAppCustomerGateway(metadata={"id": "wa-webhook"})
        payload = {
            "external_conversation_id": "wa_conv_custom",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "id": "wamid.12345",
                                        "from": {
                                            "id": "6281234567",
                                            "profile": {"name": "Budi"},
                                        },
                                        "text": {"body": "Tagihan belum dibayar"},
                                    }
                                ],
                            }
                        }
                    ],
                }
            ],
        }

        event = gateway.normalize(payload)
        self.assertEqual(event.id, "wamid.12345")
        self.assertEqual(event.external_conversation_id, "wa_conv_custom")
        self.assertEqual(event.external_customer_id, "6281234567")
        self.assertEqual(event.message_text, "Tagihan belum dibayar")


if __name__ == "__main__":
    unittest.main()
