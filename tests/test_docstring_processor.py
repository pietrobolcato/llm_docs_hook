"""Tests for docstring processor functionality.

This module contains unit tests for the docstring processor, focusing on:
- Docstring insertion and replacement
- Formatting and indentation
- Backup and restoration functionality
- Error handling for file operations
- Integration with LLM generator
"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from src.llm_docs_hook.ast_parser.types import CodeElement, ElementType
from src.llm_docs_hook.docstring_processor.docstring_processor import DocstringProcessor
from src.llm_docs_hook.docstring_processor.formatters import (
    GoogleFormatter,
    NumpyFormatter,
)


class TestDocstringProcessor(unittest.TestCase):
    """Test the docstring processor functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create a mock config
        self.config = MagicMock()
        self.config.processing.backup_files = False
        self.config.processing.verbose = False
        self.config.processing.parallel_count = 1
        self.config.docstring.style = "google"

        # Create processor with mocked LLM generator
        self.processor = DocstringProcessor(self.config)
        self.processor.llm_generator = MagicMock()

    def test_insert_docstring_simple_function(self) -> None:
        """Test inserting a docstring into a simple function."""
        source_code = "def test_function():\n    pass"
        element = CodeElement(
            name="test_function",
            element_type=ElementType.FUNCTION,
            line_number=1,
            end_line_number=2,
            signature="def test_function():",
            has_docstring=False,
            is_incomplete_docstring=False,
        )

        # Mock LLM generator to return a docstring (async method)
        async def mock_generate_docstrings(*args, **kwargs):
            return {"test_function": "This is a test function."}

        self.processor.llm_generator.generate_docstrings = mock_generate_docstrings

        with patch("builtins.open", mock_open(read_data=source_code)):
            with patch("pathlib.Path.exists", return_value=True):
                result = self.processor.process_file(Path("test.py"), [element])

        self.assertTrue(result)

    def test_replace_incomplete_docstring(self) -> None:
        """Test replacing an incomplete docstring."""
        source_code = '''def incomplete_function():
    """Incomplete docstring."""
    pass'''

        element = CodeElement(
            name="incomplete_function",
            element_type=ElementType.FUNCTION,
            line_number=1,
            end_line_number=3,
            signature="def incomplete_function():",
            has_docstring=True,
            docstring_content="Incomplete docstring.",
            is_incomplete_docstring=True,
        )

        # Mock LLM generator to return a complete docstring (async method)
        async def mock_generate_docstrings(*args, **kwargs):
            return {
                "incomplete_function": "Complete docstring with Args and Returns sections."
            }

        self.processor.llm_generator.generate_docstrings = mock_generate_docstrings

        with patch("builtins.open", mock_open(read_data=source_code)):
            with patch("pathlib.Path.exists", return_value=True):
                result = self.processor.process_file(Path("test.py"), [element])

        self.assertTrue(result)

    def test_process_file_no_elements(self) -> None:
        """Test processing a file with no elements to process."""
        result = self.processor.process_file(Path("test.py"), [])
        self.assertFalse(result)

    def test_process_file_llm_generation_fails(self) -> None:
        """Test handling when LLM generation fails."""
        source_code = "def test_function():\n    pass"
        element = CodeElement(
            name="test_function",
            element_type=ElementType.FUNCTION,
            line_number=1,
            end_line_number=2,
            signature="def test_function():",
            has_docstring=False,
            is_incomplete_docstring=False,
        )

        # Mock LLM generator to return None for the docstring (async method)
        async def mock_generate_docstrings(*args, **kwargs):
            return {"test_function": None}

        self.processor.llm_generator.generate_docstrings = mock_generate_docstrings

        with patch("builtins.open", mock_open(read_data=source_code)):
            with patch("pathlib.Path.exists", return_value=True):
                result = self.processor.process_file(Path("test.py"), [element])

        # Should return False when no docstring was generated
        self.assertFalse(result)

    def test_create_backup_enabled(self) -> None:
        """Test backup creation when enabled."""
        self.config.processing.backup_files = True

        with patch("shutil.copy2") as mock_copy:
            with patch("pathlib.Path.with_suffix", return_value=Path("test.py.backup")):
                self.processor._create_backup(Path("test.py"))

        mock_copy.assert_called_once()

    def test_create_backup_disabled(self) -> None:
        """Test that no backup is created when disabled."""
        self.config.processing.backup_files = False

        with patch("shutil.copy2") as mock_copy:
            # Call process_file instead of _create_backup directly
            source_code = "def test_function():\n    pass"
            element = CodeElement(
                name="test_function",
                element_type=ElementType.FUNCTION,
                line_number=1,
                end_line_number=2,
                signature="def test_function():",
                has_docstring=False,
                is_incomplete_docstring=False,
            )

            # Mock LLM generator to return a docstring (async method)
            async def mock_generate_docstrings(*args, **kwargs):
                return {"test_function": "This is a test function."}

            self.processor.llm_generator.generate_docstrings = mock_generate_docstrings

            with patch("builtins.open", mock_open(read_data=source_code)):
                with patch("pathlib.Path.exists", return_value=True):
                    self.processor.process_file(Path("test.py"), [element])

        mock_copy.assert_not_called()

    def test_find_insertion_point_function(self) -> None:
        """Test finding insertion point for a function."""
        source_code = "def test_function():\n    pass"
        element = CodeElement(
            name="test_function",
            element_type=ElementType.FUNCTION,
            line_number=1,
            end_line_number=2,
            signature="def test_function():",
            has_docstring=False,
            is_incomplete_docstring=False,
        )

        lines = source_code.splitlines(keepends=True)
        insertion_point = self.processor._find_insertion_point(lines, element)

        # Should insert after the function definition line (index 1)
        self.assertEqual(insertion_point, 1)

    def test_find_insertion_point_class(self) -> None:
        """Test finding insertion point for a class."""
        source_code = "class TestClass:\n    pass"
        element = CodeElement(
            name="TestClass",
            element_type=ElementType.CLASS,
            line_number=1,
            end_line_number=2,
            signature="class TestClass:",
            has_docstring=False,
            is_incomplete_docstring=False,
        )

        lines = source_code.splitlines(keepends=True)
        insertion_point = self.processor._find_insertion_point(lines, element)

        # Should insert after the class definition line (index 1)
        self.assertEqual(insertion_point, 1)

    def test_get_indentation_function(self) -> None:
        """Test getting proper indentation for a function."""
        source_code = "def test_function():\n    pass"
        element = CodeElement(
            name="test_function",
            element_type=ElementType.FUNCTION,
            line_number=1,
            end_line_number=2,
            signature="def test_function():",
            has_docstring=False,
            is_incomplete_docstring=False,
        )

        lines = source_code.splitlines(keepends=True)
        indentation = self.processor._get_indentation(lines, element)

        # Should return 4 spaces for function indentation
        self.assertEqual(indentation, "    ")

    def test_get_indentation_class(self) -> None:
        """Test getting proper indentation for a class."""
        source_code = "class TestClass:\n    pass"
        element = CodeElement(
            name="TestClass",
            element_type=ElementType.CLASS,
            line_number=1,
            end_line_number=2,
            signature="class TestClass:",
            has_docstring=False,
            is_incomplete_docstring=False,
        )

        lines = source_code.splitlines(keepends=True)
        indentation = self.processor._get_indentation(lines, element)

        # Should return 4 spaces for class indentation
        self.assertEqual(indentation, "    ")

    def test_detect_indentation_style_spaces(self) -> None:
        """Test detecting space-based indentation."""
        source_code = "def test():\n    pass\n        deeper = True"
        lines = source_code.splitlines(keepends=True)

        indentation = self.processor._detect_indentation_style(lines)

        self.assertEqual(indentation, "    ")

    def test_detect_indentation_style_tabs(self) -> None:
        """Test detecting tab-based indentation."""
        source_code = "def test():\n\tpass\n\t\tdeeper = True"
        lines = source_code.splitlines(keepends=True)

        indentation = self.processor._detect_indentation_style(lines)

        self.assertEqual(indentation, "\t")


class TestDocstringFormatters(unittest.TestCase):
    """Test the docstring formatters."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.google_formatter = GoogleFormatter()
        self.numpy_formatter = NumpyFormatter()

    def test_google_formatter_single_line(self) -> None:
        """Test Google formatter with single line docstring."""
        docstring = "This is a simple docstring."
        indentation = "    "

        result = self.google_formatter.format_docstring(docstring, indentation)

        expected = '    """This is a simple docstring."""\n'
        self.assertEqual(result, expected)

    def test_google_formatter_multi_line(self) -> None:
        """Test Google formatter with multi-line docstring."""
        docstring = "This is a multi-line docstring.\n\nArgs:\n    param: Description"
        indentation = "    "

        result = self.google_formatter.format_docstring(docstring, indentation)

        # Should format with proper indentation
        self.assertIn('"""This is a multi-line docstring.', result)
        self.assertIn("Args:", result)
        self.assertIn('"""', result)

    def test_numpy_formatter_single_line(self) -> None:
        """Test NumPy formatter with single line docstring."""
        docstring = "This is a simple docstring."
        indentation = "    "

        result = self.numpy_formatter.format_docstring(docstring, indentation)

        expected = '    """This is a simple docstring."""\n'
        self.assertEqual(result, expected)

    def test_numpy_formatter_multi_line(self) -> None:
        """Test NumPy formatter with multi-line docstring."""
        docstring = "This is a multi-line docstring.\n\nParameters\n----------\nparam : type\n    Description"
        indentation = "    "

        result = self.numpy_formatter.format_docstring(docstring, indentation)

        # Should format with proper indentation
        self.assertIn('"""This is a multi-line docstring.', result)
        self.assertIn("Parameters", result)
        self.assertIn('"""', result)

    def test_formatter_empty_docstring(self) -> None:
        """Test formatter with empty docstring."""
        docstring = ""
        indentation = "    "

        result = self.google_formatter.format_docstring(docstring, indentation)

        self.assertEqual(result, "")

    def test_formatter_none_docstring(self) -> None:
        """Test formatter with None docstring."""
        docstring = None
        indentation = "    "

        result = self.google_formatter.format_docstring(docstring, indentation)

        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
