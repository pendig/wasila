import io
import os
import sqlite3
import tomllib
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from wasila.cli.main import main


class CliTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
