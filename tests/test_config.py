import unittest

from wasila.config.defaults import default_config
from wasila.config.toml_io import dump_config, load_config


class ConfigTests(unittest.TestCase):
    def test_config_round_trip(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            config = default_config(project_name="demo", profile="startup_saas")

            path.write_text(dump_config(config), encoding="utf-8")
            loaded = load_config(path)

        self.assertEqual(loaded.name, "demo")
        self.assertEqual(loaded.profile, "startup_saas")
        self.assertEqual(loaded.provider.type, "openai-compatible")
        self.assertEqual(loaded.provider.base_url, "https://api.openai.com/v1")
        self.assertEqual(loaded.provider.model, "openai/gpt-4.1-mini")
        self.assertEqual(loaded.customer_gateway.type, "webhook")
        self.assertEqual(loaded.owner_gateway.type, "webhook")


if __name__ == "__main__":
    unittest.main()
