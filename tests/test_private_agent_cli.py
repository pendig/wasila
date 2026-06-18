import sys
import unittest

from wasila.core.contracts import PrivateAgentJob
from wasila.private_agents import CliPrivateAgentAdapter


class CliPrivateAgentAdapterTests(unittest.TestCase):
    def test_runs_fake_command_with_job_json_and_reads_result_json(self):
        code = """
import json
import sys
job = json.loads(sys.stdin.read())
print(json.dumps({
    "job_id": job["job_id"],
    "status": "done",
    "customer_reply": "Bisa kak.",
    "owner_note": "Lead baru.",
    "actions_requested": [],
}))
"""
        adapter = CliPrivateAgentAdapter([sys.executable, "-c", code])
        job = PrivateAgentJob(
            job_id="job_001",
            customer_id="cust_123",
            intent="build_website",
            summary="Customer wants a simple website.",
        )

        result = adapter.run(job)

        self.assertEqual(result.job_id, "job_001")
        self.assertEqual(result.status, "done")
        self.assertEqual(result.customer_reply, "Bisa kak.")

    def test_fails_closed_on_invalid_json(self):
        adapter = CliPrivateAgentAdapter([sys.executable, "-c", "print('not json')"])
        job = PrivateAgentJob(job_id="job_001", customer_id="cust_123", intent="x", summary="x")

        with self.assertRaises(ValueError):
            adapter.run(job)

    def test_fails_closed_on_invalid_result_status(self):
        code = """
import json
print(json.dumps({
    "job_id": "job_001",
    "status": "maybe",
    "customer_reply": "Nope",
    "owner_note": "",
    "actions_requested": [],
}))
"""
        adapter = CliPrivateAgentAdapter([sys.executable, "-c", code])
        job = PrivateAgentJob(job_id="job_001", customer_id="cust_123", intent="x", summary="x")

        with self.assertRaises(ValueError):
            adapter.run(job)

    def test_fails_closed_on_mismatched_job_id(self):
        code = """
import json
print(json.dumps({
    "job_id": "job_other",
    "status": "done",
    "customer_reply": "Nope",
    "owner_note": "",
    "actions_requested": [],
}))
"""
        adapter = CliPrivateAgentAdapter([sys.executable, "-c", code])
        job = PrivateAgentJob(job_id="job_001", customer_id="cust_123", intent="x", summary="x")

        with self.assertRaises(ValueError):
            adapter.run(job)

    def test_rejects_shell_string_command(self):
        adapter = CliPrivateAgentAdapter("echo nope")
        job = PrivateAgentJob(job_id="job_001", customer_id="cust_123", intent="x", summary="x")

        with self.assertRaises(ValueError):
            adapter.run(job)


if __name__ == "__main__":
    unittest.main()
