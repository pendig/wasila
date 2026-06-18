import os
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
        job = PrivateAgentJob(
            job_id="job_001",
            customer_id="cust_123",
            intent="x",
            summary="x",
        )

        with self.assertRaisesRegex(ValueError, "not json"):
            adapter.run(job)

    def test_fails_closed_on_non_zero_exit_code(self):
        adapter = CliPrivateAgentAdapter(
            [sys.executable, "-c", "import sys; sys.stderr.write('boom'); sys.exit(7)"]
        )
        job = PrivateAgentJob(
            job_id="job_001",
            customer_id="cust_123",
            intent="x",
            summary="x",
        )

        with self.assertRaisesRegex(ValueError, "exit code 7: boom"):
            adapter.run(job)

    def test_fails_closed_on_timeout(self):
        adapter = CliPrivateAgentAdapter(
            [sys.executable, "-c", "import time; time.sleep(2)"],
            timeout_seconds=1,
        )
        job = PrivateAgentJob(
            job_id="job_001",
            customer_id="cust_123",
            intent="x",
            summary="x",
        )

        with self.assertRaisesRegex(ValueError, "timed out"):
            adapter.run(job)

    def test_fails_closed_on_missing_executable(self):
        adapter = CliPrivateAgentAdapter(["/definitely/missing/private-agent"])
        job = PrivateAgentJob(
            job_id="job_001",
            customer_id="cust_123",
            intent="x",
            summary="x",
        )

        with self.assertRaisesRegex(ValueError, "could not be executed"):
            adapter.run(job)

    def test_fails_closed_on_secret_like_safe_context_key(self):
        adapter = CliPrivateAgentAdapter([sys.executable, "-c", "print('{}')"])
        job = PrivateAgentJob(
            job_id="job_001",
            customer_id="cust_123",
            intent="x",
            summary="x",
            safe_context={"access_token": "nope"},
        )

        with self.assertRaisesRegex(ValueError, "credential"):
            adapter.run(job)

    def test_does_not_inherit_wasila_environment(self):
        code = """
import json
import os
import sys
job = json.loads(sys.stdin.read())
if os.environ.get("WASILA_SECRET"):
    raise SystemExit(9)
print(json.dumps({
    "job_id": job["job_id"],
    "status": "done",
    "customer_reply": "ok",
    "owner_note": "",
    "actions_requested": [],
}))
"""
        os.environ["WASILA_SECRET"] = "should_not_leak"
        try:
            adapter = CliPrivateAgentAdapter([sys.executable, "-c", code])
            job = PrivateAgentJob(
                job_id="job_001",
                customer_id="cust_123",
                intent="x",
                summary="x",
            )

            result = adapter.run(job)
        finally:
            os.environ.pop("WASILA_SECRET", None)

        self.assertEqual(result.status, "done")

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
        job = PrivateAgentJob(
            job_id="job_001",
            customer_id="cust_123",
            intent="x",
            summary="x",
        )

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
        job = PrivateAgentJob(
            job_id="job_001",
            customer_id="cust_123",
            intent="x",
            summary="x",
        )

        with self.assertRaises(ValueError):
            adapter.run(job)

    def test_rejects_shell_string_command(self):
        adapter = CliPrivateAgentAdapter("echo nope")
        job = PrivateAgentJob(
            job_id="job_001",
            customer_id="cust_123",
            intent="x",
            summary="x",
        )

        with self.assertRaises(ValueError):
            adapter.run(job)


if __name__ == "__main__":
    unittest.main()
