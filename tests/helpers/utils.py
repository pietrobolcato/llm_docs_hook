"""Utility functions for testing."""

import tempfile
from pathlib import Path
from typing import Any, Optional
from unittest.mock import MagicMock

import yaml

from llm_docs_hook.ast_parser.types import CodeElement, ElementType


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


def create_mock_config(
    provider: str = "openai",
    model: str = "openai/gpt-4o-mini",
    style: str = "google",
    backup_files: bool = False,
    verbose: bool = False,
    update_incomplete: bool = False,
    parallel_count: int = 1,
) -> MagicMock:
    """Create a mock configuration object for testing.

    Args:
        provider (str): LLM provider. Optional, defaults to "openai".
        model (str): LLM model. Optional, defaults to "openai/gpt-4o-mini".
        style (str): Docstring style. Optional, defaults to "google".
        backup_files (bool): Whether to backup files. Optional, defaults to False.
        verbose (bool): Whether to enable verbose output. Optional, defaults to False.
        update_incomplete (bool): Whether to update incomplete docstrings. Optional, defaults to False.
        parallel_count (int): Number of parallel requests. Optional, defaults to 1.

    Returns:
        MagicMock: Mock configuration object.
    """
    config = MagicMock()

    # Mock LLM config
    llm_mock = MagicMock()
    llm_mock.provider = provider
    llm_mock.model = model
    llm_mock.temperature = 0.1
    llm_mock.max_tokens = 1000
    llm_mock.custom_requirements = None
    config.llm = llm_mock

    # Mock docstring config
    docstring_mock = MagicMock()
    docstring_mock.style = style
    docstring_mock.include_types = True
    docstring_mock.include_examples = False
    config.docstring = docstring_mock

    # Mock processing config
    processing_mock = MagicMock()
    processing_mock.backup_files = backup_files
    processing_mock.verbose = verbose
    processing_mock.update_incomplete_docstrings = update_incomplete
    processing_mock.parallel_count = parallel_count
    config.processing = processing_mock

    # Mock API key method
    config.get_api_key.return_value = "test-api-key-123"

    return config


def create_code_element(
    name: str,
    element_type: ElementType = ElementType.FUNCTION,
    line_number: int = 1,
    end_line_number: int = 3,
    signature: Optional[str] = None,
    has_docstring: bool = False,
    docstring_content: Optional[str] = None,
    is_incomplete_docstring: bool = False,
    is_private: bool = False,
    parent_class: Optional[str] = None,
    decorators: Optional[list[str]] = None,
    arguments: Optional[list[str]] = None,
    return_annotation: Optional[str] = None,
) -> CodeElement:
    """Create a CodeElement for testing.

    Args:
        name (str): Element name.
        element_type (ElementType): Type of element. Optional, defaults to ElementType.FUNCTION.
        line_number (int): Starting line number. Optional, defaults to 1.
        end_line_number (int): Ending line number. Optional, defaults to 3.
        signature (Optional[str]): Element signature. Optional, defaults to None.
        has_docstring (bool): Whether element has docstring. Optional, defaults to False.
        docstring_content (Optional[str]): Docstring content. Optional, defaults to None.
        is_incomplete_docstring (bool): Whether docstring is incomplete. Optional, defaults to False.
        is_private (bool): Whether element is private. Optional, defaults to False.
        parent_class (Optional[str]): Parent class name. Optional, defaults to None.
        decorators (Optional[list[str]]): List of decorators. Optional, defaults to None.
        arguments (Optional[list[str]]): List of arguments. Optional, defaults to None.
        return_annotation (Optional[str]): Return annotation. Optional, defaults to None.

    Returns:
        CodeElement: Created code element.
    """
    # Generate default signature if not provided
    if signature is None:
        if element_type == ElementType.FUNCTION:
            signature = f"def {name}():"
        else:
            signature = f"class {name}:"

    # Set default values for optional parameters
    if decorators is None:
        decorators = []
    if arguments is None:
        arguments = []

    return CodeElement(
        name=name,
        element_type=element_type,
        line_number=line_number,
        end_line_number=end_line_number,
        signature=signature,
        has_docstring=has_docstring,
        docstring_content=docstring_content,
        is_incomplete_docstring=is_incomplete_docstring,
        is_private=is_private,
        parent_class=parent_class,
        decorators=decorators,
        arguments=arguments,
        return_annotation=return_annotation,
    )


def create_mock_llm_response(content: str) -> MagicMock:
    """Create a mock LLM response for testing.

    Args:
        content (str): Response content.

    Returns:
        MagicMock: Mock LLM response object.
    """
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    return mock_response


def create_async_mock_generator(results: dict[str, Optional[str]]) -> callable:
    """Create an async mock generator function for testing.

    Args:
        results (dict[str, Optional[str]]): Dictionary mapping element names to docstrings.

    Returns:
        callable: Async function that returns the results.
    """

    async def mock_generate_docstrings(*args, **kwargs):
        return results

    return mock_generate_docstrings
