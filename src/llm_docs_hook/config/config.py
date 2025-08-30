"""Configuration management for LLM docs hook."""

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv


class DocstringConfig:
    """Configuration class for the docstring generation hook.

    This class manages loading and providing access to configuration settings
    from YAML files and environment variables. It allows users to customize
    the behavior of the docstring generation process, including settings for
    the language model, docstring style, file inclusion/exclusion patterns,
    and processing options.

    Attributes:
        config_path (Optional[str]): Path to the configuration file.
        config_data (dict[str, Any]): Loaded configuration data.

    Args:
        config_path (Optional[str]): Path to the configuration file. If not provided,
    the class will search for default configuration files in the current
    directory and its parents. Defaults to None.

    Returns:
        None: This constructor does not return a value. It initializes the instance
    and loads the configuration data.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration.

        Args:
            config_path (Optional[str]): Path to the configuration file.
                Optional, defaults to None which will search for default config files.
        """
        self.config_path = config_path or self._find_config_file()
        self.config_data = self._load_config()

        # Load environment variables
        load_dotenv()

    def _find_config_file(self) -> Optional[str]:
        """Find the configuration file in the current directory or its parents.

        Returns:
            Optional[str]: Path to the configuration file if found, None otherwise.
        """
        current_directory = Path.cwd()
        config_names = [
            ".docstring_config.yaml",
            ".docstring_config.yml",
            "docstring_config.yaml",
        ]

        # Search current directory and parent directories
        for directory in [current_directory, *current_directory.parents]:
            for config_name in config_names:
                config_file = directory / config_name
                if config_file.exists():
                    return str(config_file)

        return None

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from YAML file.

        Returns:
            dict[str, Any]: Configuration dictionary with default values.
        """
        default_config = {
            "llm": {
                "provider": "openai",
                "model": "openai/gpt-4o-mini",
                "temperature": 0.1,
                "max_tokens": 1000,
            },
            "docstring": {
                "style": "google",  # google or numpy
                "include_types": True,
                "include_examples": False,
            },
            "files": {
                "include_patterns": ["**/*.py"],
                "exclude_patterns": [
                    "**/test_*.py",
                    "**/tests/**/*.py",
                    "**/*_test.py",
                    "**/conftest.py",
                    "**/__pycache__/**",
                    "**/venv/**",
                    "**/env/**",
                    "**/.venv/**",
                ],
            },
            "processing": {
                "skip_existing_docstrings": True,
                "update_incomplete_docstrings": False,
                "backup_files": False,
                "verbose": False,
            },
        }

        if not self.config_path:
            return default_config

        try:
            with open(self.config_path, encoding="utf-8") as file:
                user_config = yaml.safe_load(file) or {}

            # Merge user config with defaults
            merged_config = self._merge_configs(default_config, user_config)
            return merged_config

        except (FileNotFoundError, yaml.YAMLError) as error:
            print(f"Warning: Could not load config file {self.config_path}: {error}")
            return default_config

    def _merge_configs(
        self, default: dict[str, Any], user: dict[str, Any]
    ) -> dict[str, Any]:
        """Recursively merge user configuration with defaults.

        Args:
            default (dict[str, Any]): Default configuration dictionary.
            user (dict[str, Any]): User-provided configuration dictionary.

        Returns:
            dict[str, Any]: Merged configuration dictionary.
        """
        merged = default.copy()

        for key, value in user.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value

        return merged

    @property
    def llm_provider(self) -> str:
        """Get the LLM provider.

        Returns:
            str: The LLM provider name.
        """
        return self.config_data["llm"]["provider"]

    @property
    def llm_model(self) -> str:
        """Get the LLM model.

        Returns:
            str: The LLM model identifier.
        """
        return self.config_data["llm"]["model"]

    @property
    def llm_temperature(self) -> float:
        """Get the LLM temperature setting.

        Returns:
            float: The temperature value for LLM generation.
        """
        return self.config_data["llm"]["temperature"]

    @property
    def llm_max_tokens(self) -> int:
        """Get the maximum tokens for LLM generation.

        Returns:
            int: The maximum number of tokens.
        """
        return self.config_data["llm"]["max_tokens"]

    @property
    def docstring_style(self) -> str:
        """Get the docstring style.

        Returns:
            str: The docstring style ('google' or 'numpy').
        """
        return self.config_data["docstring"]["style"]

    @property
    def include_types(self) -> bool:
        """Get whether to include type information in docstrings.

        Returns:
            bool: True if types should be included, False otherwise.
        """
        return self.config_data["docstring"]["include_types"]

    @property
    def include_examples(self) -> bool:
        """Get whether to include examples in docstrings.

        Returns:
            bool: True if examples should be included, False otherwise.
        """
        return self.config_data["docstring"]["include_examples"]

    @property
    def include_patterns(self) -> list[str]:
        """Get file inclusion patterns.

        Returns:
            list[str]: list of glob patterns for files to include.
        """
        return self.config_data["files"]["include_patterns"]

    @property
    def exclude_patterns(self) -> list[str]:
        """Get file exclusion patterns.

        Returns:
            list[str]: list of glob patterns for files to exclude.
        """
        return self.config_data["files"]["exclude_patterns"]

    @property
    def skip_existing_docstrings(self) -> bool:
        """Get whether to skip functions/classes that already have docstrings.

        Returns:
            bool: True if existing docstrings should be preserved, False otherwise.
        """
        return self.config_data["processing"]["skip_existing_docstrings"]

    @property
    def update_incomplete_docstrings(self) -> bool:
        """Get whether to update existing docstrings that lack Args/Returns sections.

        Returns:
            bool: True if incomplete docstrings should be updated, False otherwise.
        """
        return self.config_data["processing"]["update_incomplete_docstrings"]

    @property
    def backup_files(self) -> bool:
        """Get whether to create backup files.

        Returns:
            bool: True if backup files should be created, False otherwise.
        """
        return self.config_data["processing"]["backup_files"]

    @property
    def verbose(self) -> bool:
        """Get verbose mode setting.

        Returns:
            bool: True if verbose output is enabled, False otherwise.
        """
        return self.config_data["processing"]["verbose"]

    def get_api_key(self) -> Optional[str]:
        """Get the API key for the configured LLM provider.

        Returns:
            Optional[str]: The API key if found in environment variables, None otherwise.
        """
        provider = self.llm_provider.upper()

        # LLM_DOCS_HOOK_ prefixed API key environment variable names
        possible_keys = [
            f"LLM_DOCS_HOOK_{provider}_API_KEY",
            f"LLM_DOCS_HOOK_{provider}API_KEY",
            "LLM_DOCS_HOOK_OPENAI_API_KEY",  # fallback for OpenAI-compatible providers
            "LLM_DOCS_HOOK_API_KEY",
        ]

        for key in possible_keys:
            api_key = os.getenv(key)
            if api_key:
                return api_key

        return None

    def create_sample_config(self, output_path: str = ".docstring_config.yaml") -> None:
        """Create a sample configuration file for docstring generation.

        This method generates a YAML configuration file that specifies settings
        for a language model, docstring style, file inclusion/exclusion patterns,
        and processing options. The generated file can be used to customize the
        behavior of the docstring generation tool.

        Args:
            output_path (str): The file path where the sample configuration
        will be created. Defaults to ".docstring_config.yaml".

        Returns:
            None: This function does not return a value. It writes the
        configuration to the specified file and prints a confirmation
        message upon successful creation.
        """
        sample_config = {
            "llm": {
                "provider": "openai",
                "model": "openai/gpt-4o-mini",
                "temperature": 0.1,
                "max_tokens": 1000,
            },
            "docstring": {
                "style": "google",  # google or numpy
                "include_types": True,
                "include_examples": False,
            },
            "files": {
                "include_patterns": ["**/*.py"],
                "exclude_patterns": [
                    "**/test_*.py",
                    "**/tests/**/*.py",
                    "**/*_test.py",
                    "**/conftest.py",
                    "**/__pycache__/**",
                    "**/venv/**",
                    "**/env/**",
                    "**/.venv/**",
                ],
            },
            "processing": {
                "skip_existing_docstrings": True,
                "update_incomplete_docstrings": False,
                "backup_files": False,
                "verbose": False,
            },
        }

        with open(output_path, "w", encoding="utf-8") as file:
            yaml.dump(sample_config, file, default_flow_style=False, indent=2)

        print(f"Sample configuration created at: {output_path}")
