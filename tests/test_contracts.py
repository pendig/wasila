import unittest

from wasila.core.contracts import CustomerEvent, OrchestrationResult


class ContractTests(unittest.TestCase):
    def test_customer_event_defaults_to_customer_gateway_role(self):
        event = CustomerEvent(
            gateway="sandbox",
            external_conversation_id="conv_1",
            external_customer_id="cust_ext_1",
            message_text="Hello",
        )

        self.assertEqual(event.gateway_role, "customer")
        self.assertTrue(event.message_timestamp.endswith("Z"))

    def test_orchestration_result_defaults_to_empty_collections(self):
        result = OrchestrationResult(customer_response="Hi")

        self.assertEqual(result.ticket_updates, [])
        self.assertEqual(result.memory_updates, [])
        self.assertEqual(result.owner_notifications, [])
        self.assertEqual(result.skill_results, [])
        self.assertEqual(result.agent_runs, [])


if __name__ == "__main__":
    unittest.main()
