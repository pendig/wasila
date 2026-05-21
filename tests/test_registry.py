import unittest

from wasila.core.registry import Registry, RegistryError


class RegistryTests(unittest.TestCase):
    def test_registry_registers_and_returns_item(self):
        registry = Registry[str]("provider")

        registry.register("openai-compatible", "adapter")

        self.assertEqual(registry.get("openai-compatible"), "adapter")
        self.assertEqual(registry.names(), ["openai-compatible"])

    def test_registry_error_lists_available_items(self):
        registry = Registry[str]("gateway")
        registry.register("webhook", "adapter")

        with self.assertRaises(RegistryError) as exc:
            registry.get("telegram")
        self.assertIn("webhook", str(exc.exception))


if __name__ == "__main__":
    unittest.main()
