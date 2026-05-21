import unittest
from unittest.mock import patch

from wasila.config.models import ProviderSettings
from wasila.providers.crewai_llm import crewai_llm_kwargs


class CrewAILLMProviderTests(unittest.TestCase):
    def test_crewai_llm_kwargs_include_model_base_url_and_env_api_key(self):
        settings = ProviderSettings(
            type="openai-compatible",
            base_url="http://localhost:4000/v1",
            model="openai/custom-model",
            api_key_env="CUSTOM_KEY",
        )

        with patch.dict("os.environ", {"CUSTOM_KEY": "secret"}, clear=True):
            kwargs = crewai_llm_kwargs(settings)

        self.assertEqual(kwargs["model"], "openai/custom-model")
        self.assertEqual(kwargs["base_url"], "http://localhost:4000/v1")
        self.assertEqual(kwargs["api_key"], "secret")

    def test_crewai_llm_kwargs_omit_missing_api_key_value(self):
        settings = ProviderSettings(api_key_env="MISSING_KEY")

        with patch.dict("os.environ", {}, clear=True):
            kwargs = crewai_llm_kwargs(settings)

        self.assertEqual(kwargs["model"], "openai/gpt-4.1-mini")
        self.assertNotIn("api_key", kwargs)


if __name__ == "__main__":
    unittest.main()
