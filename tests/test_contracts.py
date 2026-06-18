import unittest

from wasila.core.contracts import (
    CustomerEvent,
    OrchestrationResult,
    private_agent_job_from_json,
    private_agent_result_from_json,
)


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

    def test_private_agent_job_round_trips_documented_example(self):
        data = {
            "job_id": "job_001",
            "customer_id": "cust_123",
            "ticket_id": "tick_001",
            "intent": "build_website",
            "summary": "Customer wants a simple company website.",
            "safe_context": {
                "customer_message": "Saya mau bikin website company profile",
                "business": "Pena Digital",
                "constraints": ["reply in Indonesian", "ask for missing requirements"],
            },
            "forbidden": [
                "do not expose internal memory",
                "do not contact the customer directly",
                "do not execute paid actions without owner approval",
            ],
        }

        job = private_agent_job_from_json(data)

        self.assertEqual(job.to_json(), data)

    def test_private_agent_result_round_trips_documented_example(self):
        data = {
            "job_id": "job_001",
            "status": "done",
            "customer_reply": "Bisa kak. Untuk mulai, saya butuh nama bisnis, jumlah halaman, referensi desain, dan deadline.",
            "owner_note": "Lead website baru. Perlu follow-up pricing.",
            "actions_requested": [],
        }

        result = private_agent_result_from_json(data)

        self.assertEqual(result.to_json(), data)

    def test_private_agent_job_rejects_customer_channel_credentials(self):
        data = {
            "job_id": "job_001",
            "customer_id": "cust_123",
            "intent": "build_website",
            "summary": "Customer wants a simple company website.",
            "safe_context": {"access_token": "nope"},
            "forbidden": [],
        }

        with self.assertRaises(ValueError):
            private_agent_job_from_json(data)


if __name__ == "__main__":
    unittest.main()
