"""Sample source code for testing.

This module provides sample Python code snippets and docstrings for testing purposes.
The code is organized into logical categories and reads multiline examples from external files
to keep the main module clean and readable.
"""

from pathlib import Path


def _read_file_content(file_path: str, sample_dir_name: str = "sample_files") -> str:
    """Read content from a file and return as string.

    Args:
        file_path (str): Path to the file to read.
        sample_dir_name (str): Name of the directory containing the sample files.

    Returns:
        str: Content of the file as string.

    Raises:
        FileNotFoundError: If the file doesn't exist.
    """
    sample_dir = Path(__file__).parent / sample_dir_name
    full_path = sample_dir / file_path

    if not full_path.exists():
        raise FileNotFoundError(f"Sample file not found: {full_path}")

    with open(full_path, encoding="utf-8") as file:
        return file.read().rstrip("\n")


def _create_simple_functions() -> dict[str, str]:
    """Create simple function examples for testing.

    Returns:
        dict[str, str]: Dictionary mapping test names to function code strings.
    """
    return {
        "simple_function": "def simple_function():\n    pass",
        "function_with_args": "def function_with_args(param1, param2):\n    return param1 + param2",
        "private_function": "def _private_function():\n    pass",
        "async_function": "async def async_function():\n    pass",
    }


def _create_class_examples() -> dict[str, str]:
    """Create class examples for testing.

    Returns:
        dict[str, str]: Dictionary mapping test names to class code strings.
    """
    return {
        "simple_class": "class TestClass:\n    pass",
        "class_with_methods": _read_file_content("class_with_methods.py"),
        "init_method": "def __init__(self):\n    pass",
        "special_method": "def __str__(self):\n    pass",
    }


def _create_decorated_and_documented_functions() -> dict[str, str]:
    """Create decorated and documented function examples for testing.

    Returns:
        dict[str, str]: Dictionary mapping test names to function code strings.
    """
    return {
        "decorated_function": _read_file_content("decorated_function.py"),
        "function_with_docstring": _read_file_content("function_with_docstring.py"),
        "function_with_incomplete_docstring": _read_file_content(
            "function_with_incomplete_docstring.py"
        ),
    }


def _create_formatting_examples() -> dict[str, str]:
    """Create code examples with different formatting for testing.

    Returns:
        dict[str, str]: Dictionary mapping test names to code strings with various formatting.
    """
    return {
        "function_with_spaces": _read_file_content("function_with_spaces.py"),
        "function_with_tabs": _read_file_content("function_with_tabs.py"),
    }


def _create_simple_docstrings() -> dict[str, str]:
    """Create simple docstring examples for testing.

    Returns:
        dict[str, str]: Dictionary mapping test names to docstring strings.
    """
    return {
        "simple": "This is a simple docstring.",
        "multi_line": "This is a multi-line docstring.\n\nIt has multiple paragraphs.",
        "empty": "",
        "whitespace_only": "   \n   \n   ",
    }


def _create_google_style_docstrings() -> dict[str, str]:
    """Create Google-style docstring examples for testing.

    Returns:
        dict[str, str]: Dictionary mapping test names to Google-style docstring strings.
    """
    return {
        "google_with_args": _read_file_content("docstrings/google_with_args.txt"),
        "google_with_examples": _read_file_content(
            "docstrings/google_with_examples.txt"
        ),
        "google_with_raises": _read_file_content("docstrings/google_with_raises.txt"),
    }


def _create_numpy_style_docstrings() -> dict[str, str]:
    """Create NumPy-style docstring examples for testing.

    Returns:
        dict[str, str]: Dictionary mapping test names to NumPy-style docstring strings.
    """
    return {
        "numpy_with_parameters": _read_file_content(
            "docstrings/numpy_with_parameters.txt"
        ),
        "numpy_with_examples": _read_file_content("docstrings/numpy_with_examples.txt"),
        "numpy_with_raises": _read_file_content("docstrings/numpy_with_raises.txt"),
    }


# Combine all examples into the main dictionaries
SAMPLE_PYTHON_CODE: dict[str, str] = {
    **_create_simple_functions(),
    **_create_class_examples(),
    **_create_decorated_and_documented_functions(),
    **_create_formatting_examples(),
}

SAMPLE_DOCSTRINGS: dict[str, str] = {
    **_create_simple_docstrings(),
    **_create_google_style_docstrings(),
    **_create_numpy_style_docstrings(),
}
