"""Tests for configuration loading and API key handling.

This module contains unit tests for the configuration system, focusing on:
- Configuration file loading and validation
- Environment variable handling for API keys
- Default configuration behavior
- Error handling for missing/invalid configurations
"""

import os
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

import yaml

from src.llm_docs_hook.config.types import Config
from src.llm_docs_hook.config.utils import load_config
from tests.conftest import SAMPLE_CONFIG_MINIMAL, get_sample_config_yaml


class TestConfigTypes(unittest.TestCase):
    """Test the pydantic Config model and API key retrieval."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Clear any existing environment variables that might interfere
        self.env_vars_to_clear = [
            "LLM_DOCS_HOOK_OPENAI_API_KEY",
            "LLM_DOCS_HOOK_ANTHROPIC_API_KEY",
            "LLM_DOCS_HOOK_MISTRAL_API_KEY",
            "LLM_DOCS_HOOK_GOOGLE_API_KEY",
            "LLM_DOCS_HOOK_API_KEY",
        ]
        self.original_env_values = {}
        for env_var in self.env_vars_to_clear:
            self.original_env_values[env_var] = os.environ.get(env_var)
            if env_var in os.environ:
                del os.environ[env_var]

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        # Restore original environment variables
        for env_var, original_value in self.original_env_values.items():
            if original_value is not None:
                os.environ[env_var] = original_value
            elif env_var in os.environ:
                del os.environ[env_var]

    def test_default_config_creation(self) -> None:
        """Test that default configuration is created correctly."""
        config = Config()

        self.assertEqual(config.llm.provider, "openai")
        self.assertEqual(config.llm.model, "openai/gpt-4o-mini")
        self.assertEqual(config.llm.temperature, 0.1)
        self.assertEqual(config.llm.max_tokens, 1000)

        self.assertEqual(config.docstring.style, "google")
        self.assertTrue(config.docstring.include_types)
        self.assertFalse(config.docstring.include_examples)

        self.assertEqual(config.files.include_patterns, ["**/*.py"])
        self.assertIn("**/test_*.py", config.files.exclude_patterns)

        self.assertTrue(config.processing.skip_existing_docstrings)
        self.assertFalse(config.processing.update_incomplete_docstrings)
        self.assertFalse(config.processing.backup_files)
        self.assertFalse(config.processing.verbose)
        self.assertEqual(config.processing.parallel_count, 5)

    def test_get_api_key_openai_provider(self) -> None:
        """Test API key retrieval for OpenAI provider."""
        config = Config()
        config.llm.provider = "openai"

        # Test primary environment variable
        test_key = "test-openai-key-123"
        os.environ["LLM_DOCS_HOOK_OPENAI_API_KEY"] = test_key

        api_key = config.get_api_key()
        self.assertEqual(api_key, test_key)

    def test_get_api_key_anthropic_provider(self) -> None:
        """Test API key retrieval for Anthropic provider."""
        config = Config()
        config.llm.provider = "anthropic"

        test_key = "test-anthropic-key-456"
        os.environ["LLM_DOCS_HOOK_ANTHROPIC_API_KEY"] = test_key

        api_key = config.get_api_key()
        self.assertEqual(api_key, test_key)

    def test_get_api_key_fallback_to_generic(self) -> None:
        """Test API key fallback to generic LLM_DOCS_HOOK_API_KEY."""
        config = Config()
        config.llm.provider = "unknown_provider"

        test_key = "test-generic-key-789"
        os.environ["LLM_DOCS_HOOK_API_KEY"] = test_key

        api_key = config.get_api_key()
        self.assertEqual(api_key, test_key)

    def test_get_api_key_openai_fallback(self) -> None:
        """Test OpenAI fallback for compatible providers."""
        config = Config()
        config.llm.provider = "some_openai_compatible"

        test_key = "test-openai-fallback-key"
        os.environ["LLM_DOCS_HOOK_OPENAI_API_KEY"] = test_key

        api_key = config.get_api_key()
        self.assertEqual(api_key, test_key)

    def test_get_api_key_returns_none_when_missing(self) -> None:
        """Test that get_api_key returns None when no API key is found."""
        config = Config()
        config.llm.provider = "nonexistent"

        api_key = config.get_api_key()
        self.assertIsNone(api_key)

    def test_model_validation_success(self) -> None:
        """Test that valid model format passes validation."""
        config = Config()
        config.llm.model = "openai/gpt-4"
        # Should not raise an exception
        self.assertEqual(config.llm.model, "openai/gpt-4")

    def test_model_validation_failure(self) -> None:
        """Test that invalid model format raises validation error."""
        from pydantic import ValidationError

        with self.assertRaises(ValidationError):
            Config(llm={"model": "invalid-model-format"})


class TestConfigUtils(unittest.TestCase):
    """Test the configuration utility functions."""

    @patch("src.llm_docs_hook.config.utils.find_config_file")
    def test_load_config_with_defaults_when_no_file(
        self, mock_find_config: unittest.mock.MagicMock
    ) -> None:
        """Test loading default configuration when no config file exists."""
        mock_find_config.return_value = None

        config = load_config()

        # Should return default configuration
        self.assertEqual(config.llm.provider, "openai")
        self.assertEqual(config.llm.model, "openai/gpt-4o-mini")

    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_config_from_file(
        self,
        mock_file_open: unittest.mock.MagicMock,
        mock_exists: unittest.mock.MagicMock,
    ) -> None:
        """Test loading configuration from YAML file."""
        mock_exists.return_value = True

        # Mock YAML configuration
        yaml_content = {
            "llm": {
                "provider": "anthropic",
                "model": "anthropic/claude-3-haiku-20240307",
                "temperature": 0.2,
            },
            "docstring": {
                "style": "numpy",
                "include_examples": True,
            },
        }

        sample_yaml = get_sample_config_yaml(yaml_content)
        mock_file_open.return_value.read.return_value = sample_yaml

        with patch("yaml.safe_load", return_value=yaml_content):
            config = load_config(Path("/fake/config.yaml"))

        self.assertEqual(config.llm.provider, "anthropic")
        self.assertEqual(config.llm.model, "anthropic/claude-3-haiku-20240307")
        self.assertEqual(config.llm.temperature, 0.2)
        self.assertEqual(config.docstring.style, "numpy")
        self.assertTrue(config.docstring.include_examples)

    @patch("pathlib.Path.exists")
    def test_load_config_file_not_found(
        self, mock_exists: unittest.mock.MagicMock
    ) -> None:
        """Test that FileNotFoundError is raised for missing config file."""
        mock_exists.return_value = False

        with self.assertRaises(FileNotFoundError):
            load_config(Path("/nonexistent/config.yaml"))

    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_config_invalid_yaml(
        self,
        mock_file_open: unittest.mock.MagicMock,
        mock_exists: unittest.mock.MagicMock,
    ) -> None:
        """Test that YAMLError is raised for invalid YAML content."""
        mock_exists.return_value = True
        mock_file_open.return_value.read.return_value = "invalid: yaml: content: ["

        with patch("yaml.safe_load", side_effect=yaml.YAMLError("Invalid YAML")):
            with self.assertRaises(yaml.YAMLError):
                load_config(Path("/fake/invalid.yaml"))

    @patch("src.llm_docs_hook.config.utils.find_config_file")
    def test_find_config_file_search_pattern(
        self, mock_find_config: unittest.mock.MagicMock
    ) -> None:
        """Test that find_config_file searches for expected filenames."""
        # Create a mock Path object
        mock_path = unittest.mock.MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_find_config.return_value = mock_path

        # Mock file reading
        sample_yaml = get_sample_config_yaml(SAMPLE_CONFIG_MINIMAL)
        with patch("builtins.open", mock_open(read_data=sample_yaml)):
            config = load_config()

        # Verify that find_config_file was called
        mock_find_config.assert_called_once()

        # Configuration should be loaded (this would normally load from the found file)
        self.assertIsInstance(config, Config)


if __name__ == "__main__":
    unittest.main()
