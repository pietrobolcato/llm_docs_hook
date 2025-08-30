"""Utility functions for the config module."""

from pathlib import Path
from typing import Optional

import yaml

from src.llm_docs_hook.config.types import Config


def find_config_file() -> Optional[Path]:
    """Find the configuration file in the current directory or its parents.

    Returns:
        Optional[Path]: Path to the configuration file if found, None otherwise.
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
                return config_file

    return None


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from YAML file or return defaults.

    Args:
        config_path (Optional[Path]): Path to the configuration file.
            Optional, defaults to None which will search for default config files.

    Returns:
        Config: Validated configuration object.

    Raises:
        FileNotFoundError: If specified config file doesn't exist.
        yaml.YAMLError: If YAML parsing fails.
        ValidationError: If configuration validation fails.
    """
    # Use provided path or find automatically
    if config_path is None:
        config_path = find_config_file()

    # Return defaults if no config file found
    if config_path is None:
        return Config()

    # Check if specified file exists
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, encoding="utf-8") as file:
            config_data = yaml.safe_load(file) or {}

        return Config(**config_data)

    except yaml.YAMLError as error:
        raise yaml.YAMLError(f"Error parsing YAML configuration: {error}") from error


def save_config(config: Config, config_path: Path) -> None:
    """Save configuration to a YAML file.

    This function serializes the provided configuration object and writes it to a specified YAML file.
    If the parent directory of the specified path does not exist, it will be created.

    Args:
        config (Config): The configuration object to save, which should be serializable to a dictionary.
        config_path (Path): The file path where the configuration will be saved. This should be a valid path
    where the user has write permissions.

    Returns:
        None: This function does not return a value. It performs a file write operation.
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as file:
        yaml.dump(
            config.dict(), file, default_flow_style=False, sort_keys=False, indent=2
        )


def create_sample_config(output_path: Path = Path(".docstring_config.yaml")) -> None:
    """Create a sample configuration file.

    This function generates a sample configuration file at the specified output path.
    If no path is provided, it defaults to creating a file named ".docstring_config.yaml"
    in the current directory.

    Args:
        output_path (Path, optional): The file path where the sample configuration
    file will be created. Defaults to Path(".docstring_config.yaml").

    Returns:
        None: This function does not return a value. It only creates a file and prints
    a confirmation message to the console.
    """
    default_config = Config()
    save_config(default_config, output_path)
    print(f"Sample configuration created at: {output_path}")
