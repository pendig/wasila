import io
import os
import sqlite3
import tomllib
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from wasila.cli.main import _deliver_customer_reply, main
from wasila.core.contracts import CustomerEvent, OrchestrationResult


class CliTests(unittest.TestCase):
    def test_deliver_customer_reply_calls_gateway_sender_when_available(self):
        class Gateway:
            def __init__(self):
                self.sent = []

            def send_reply(self, chat_id, text):
                self.sent.append((chat_id, text))

        gateway = Gateway()
        event = CustomerEvent(gateway="wacli", external_conversation_id="+628123")
        result = OrchestrationResult(customer_response="Siap")

        _deliver_customer_reply(gateway, event, result)

        self.assertEqual(gateway.sent, [("+628123", "Siap")])

    def test_init_creates_config_database_and_runtime_dirs(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            current = Path.cwd()
            try:
                os.chdir(tmp_path)
                main(["init", "startup_saas", "--name", "demo"])
            finally:
                os.chdir(current)

            self.assertTrue((tmp_path / ".wasila" / "config.toml").exists())
            self.assertTrue((tmp_path / "data" / "wasila.sqlite3").exists())
            self.assertTrue((tmp_path / "data" / "customers").is_dir())
            self.assertTrue((tmp_path / "knowledge").is_dir())

            with sqlite3.connect(tmp_path / "data" / "wasila.sqlite3") as connection:
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                }

        self.assertIn("customers", tables)
        self.assertIn("skill_executions", tables)

    def test_kb_init_creates_starter_knowledge_files(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            current = Path.cwd()
            try:
                os.chdir(tmp_path)
                main(["kb", "init"])
            finally:
                os.chdir(current)

            self.assertTrue((tmp_path / "knowledge" / "business.md").exists())
            self.assertTrue((tmp_path / "knowledge" / "products.md").exists())
            self.assertTrue((tmp_path / "knowledge" / "policies.md").exists())
            self.assertTrue((tmp_path / "knowledge" / "support.md").exists())
            self.assertTrue((tmp_path / "knowledge" / "owner.md").exists())

    def test_assistant_add_cli_stores_config_and_list_shows_it(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = tmp_path / ".wasila" / "config.toml"

            main(
                [
                    "--config",
                    str(config_path),
                    "assistant",
                    "add",
                    "cli",
                    "--name",
                    "hermes",
                    "--command",
                    "hermes -p private-assistant",
                ]
            )

            data = tomllib.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(
                data["assistants"]["hermes"],
                {"type": "cli", "command": ["hermes", "-p", "private-assistant"]},
            )

            output = io.StringIO()
            with redirect_stdout(output):
                main(["--config", str(config_path), "assistant", "list"])

        self.assertIn("hermes", output.getvalue())
        self.assertIn("cli", output.getvalue())
        self.assertIn("hermes -p private-assistant", output.getvalue())

    def test_assistant_add_cli_rejects_secret_like_command_args(self):
        with TemporaryDirectory() as tmp:
            config_path = Path(tmp) / ".wasila" / "config.toml"
            with self.assertRaises(SystemExit):
                main(
                    [
                        "--config",
                        str(config_path),
                        "assistant",
                        "add",
                        "cli",
                        "--name",
                        "bad",
                        "--command",
                        "agent --api-key secret",
                    ]
                )

            self.assertFalse(config_path.exists())

    def test_assistant_add_cli_rejects_invalid_shell_command(self):
        with TemporaryDirectory() as tmp:
            config_path = Path(tmp) / ".wasila" / "config.toml"
            with self.assertRaises(SystemExit):
                main(
                    [
                        "--config",
                        str(config_path),
                        "assistant",
                        "add",
                        "cli",
                        "--name",
                        "bad",
                        "--command",
                        "agent 'unterminated",
                    ]
                )

    def test_assistant_add_cli_allows_secret_named_options_without_values(self):
        with TemporaryDirectory() as tmp:
            config_path = Path(tmp) / ".wasila" / "config.toml"
            main(
                [
                    "--config",
                    str(config_path),
                    "assistant",
                    "add",
                    "cli",
                    "--name",
                    "env_agent",
                    "--command",
                    "agent --api-key-env WASILA_AGENT_KEY --token-file /tmp/token",
                ]
            )

            data = tomllib.loads(config_path.read_text(encoding="utf-8"))

        self.assertEqual(data["assistants"]["env_agent"]["type"], "cli")

    def test_assistant_name_must_be_ascii_toml_bare_key(self):
        with TemporaryDirectory() as tmp:
            config_path = Path(tmp) / ".wasila" / "config.toml"
            with self.assertRaises(SystemExit):
                main(
                    [
                        "--config",
                        str(config_path),
                        "assistant",
                        "add",
                        "cli",
                        "--name",
                        "café",
                        "--command",
                        "agent",
                    ]
                )

    def test_assistant_config_round_trips_escaped_strings_and_bad_type(self):
        with TemporaryDirectory() as tmp:
            config_path = Path(tmp) / ".wasila" / "config.toml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                '[project]\nname = "demo"\nprofile = "startup_saas"\n\n'
                '[assistants.quoted]\n'
                'type = 123\n'
                'command = ["agent", "line\\nbreak", "tab\\tvalue"]\n',
                encoding="utf-8",
            )

            output = io.StringIO()
            with redirect_stdout(output):
                main(["--config", str(config_path), "assistant", "list"])

        self.assertIn("quoted", output.getvalue())
        self.assertIn("cli", output.getvalue())


if __name__ == "__main__":
    unittest.main()
