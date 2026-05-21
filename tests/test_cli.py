import sqlite3
import unittest
import os
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


if __name__ == "__main__":
    unittest.main()
