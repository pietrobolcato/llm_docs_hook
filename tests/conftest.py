"""Test configuration and fixtures for the llm_docs_hook package.

This module provides common test fixtures, sample data, and helper functions
that can be used across all test modules.
"""

import tempfile
from pathlib import Path
from typing import Any

import yaml

# Sample configuration data for testing
SAMPLE_CONFIG_MINIMAL = {"llm": {"provider": "openai", "model": "openai/gpt-4o-mini"}}

SAMPLE_CONFIG_FULL = {
    "llm": {
        "provider": "anthropic",
        "model": "anthropic/claude-3-haiku-20240307",
        "temperature": 0.2,
        "max_tokens": 1500,
    },
    "docstring": {"style": "numpy", "include_types": True, "include_examples": True},
    "files": {
        "include_patterns": ["**/*.py", "**/*.js"],
        "exclude_patterns": ["**/test_*.py", "**/__pycache__/**"],
    },
    "processing": {
        "skip_existing_docstrings": False,
        "update_incomplete_docstrings": True,
        "backup_files": True,
        "verbose": True,
        "parallel_count": 3,
    },
}

SAMPLE_CONFIG_INVALID = {
    "llm": {"provider": "invalid_provider", "model": "invalid-model-format"}
}


def create_temp_config_file(config_data: dict[str, Any], suffix: str = ".yaml") -> Path:
    """Create a temporary configuration file with the given data.

    Args:
        config_data (dict[str, Any]): Configuration data to write to the file.
        suffix (str): File extension suffix. Optional, defaults to ".yaml".

    Returns:
        Path: Path to the created temporary configuration file.
    """
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
    yaml.dump(
        config_data, temp_file, default_flow_style=False, sort_keys=False, indent=2
    )
    temp_file.close()
    return Path(temp_file.name)


def get_sample_config_yaml(config_data: dict[str, Any]) -> str:
    """Convert configuration data to YAML string.

    Args:
        config_data (dict[str, Any]): Configuration data to convert.

    Returns:
        str: YAML string representation of the configuration data.
    """
    return yaml.dump(config_data, default_flow_style=False, sort_keys=False, indent=2)
