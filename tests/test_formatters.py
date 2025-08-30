"""Tests for docstring formatters.

This module contains unit tests for the docstring formatters, focusing on:
- Google-style docstring formatting
- NumPy-style docstring formatting
- Indentation and quote handling
- Section header detection
- Edge cases and error handling
"""

import unittest

from src.llm_docs_hook.docstring_processor.formatters import (
    GoogleFormatter,
    NumpyFormatter,
    get_formatter,
)
from src.llm_docs_hook.docstring_processor.types import DocstringStyle


class TestGoogleFormatter(unittest.TestCase):
    """Test the Google-style docstring formatter."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.formatter = GoogleFormatter()

    def test_format_single_line_docstring(self) -> None:
        """Test formatting a single line docstring."""
        docstring = "This is a simple docstring."
        indentation = "    "

        result = self.formatter.format_docstring(docstring, indentation)

        expected = '    """This is a simple docstring."""\n'
        self.assertEqual(result, expected)

    def test_format_multi_line_docstring(self) -> None:
        """Test formatting a multi-line docstring."""
        docstring = "This is a multi-line docstring.\n\nIt has multiple paragraphs."
        indentation = "    "

        result = self.formatter.format_docstring(docstring, indentation)

        # Should format with proper indentation and quotes
        self.assertIn('"""This is a multi-line docstring.', result)
        self.assertIn("It has multiple paragraphs.", result)
        self.assertIn('"""', result)

    def test_format_docstring_with_args_section(self) -> None:
        """Test formatting a docstring with Args section."""
        docstring = """This function does something.

Args:
    param1: Description of param1.
    param2 (int): Description of param2.
    param3 (str, optional): Description of param3.

Returns:
    bool: Description of return value."""

        indentation = "    "
        result = self.formatter.format_docstring(docstring, indentation)

        # Should format Args section properly
        self.assertIn("Args:", result)
        self.assertIn("param1:", result)
        self.assertIn("param2 (int):", result)
        self.assertIn("Returns:", result)

    def test_format_docstring_with_parameter_indentation(self) -> None:
        """Test that parameter descriptions are properly indented."""
        docstring = """This function does something.

Args:
    param1: This is a long description that should be properly indented
        and wrapped correctly.
    param2 (int): Another parameter with a description."""

        indentation = "    "
        result = self.formatter.format_docstring(docstring, indentation)

        # Parameter descriptions should have extra indentation
        self.assertIn("    param1:", result)
        # The formatter doesn't add extra indentation for wrapped lines
        self.assertIn("    and wrapped correctly.", result)

    def test_format_empty_docstring(self) -> None:
        """Test formatting an empty docstring."""
        docstring = ""
        indentation = "    "

        result = self.formatter.format_docstring(docstring, indentation)

        self.assertEqual(result, "")

    def test_format_none_docstring(self) -> None:
        """Test formatting a None docstring."""
        docstring = None
        indentation = "    "

        result = self.formatter.format_docstring(docstring, indentation)

        self.assertEqual(result, "")

    def test_format_docstring_with_whitespace_only(self) -> None:
        """Test formatting a docstring with only whitespace."""
        docstring = "   \n   \n   "
        indentation = "    "

        result = self.formatter.format_docstring(docstring, indentation)

        # Should handle whitespace-only docstrings
        self.assertIn('"""', result)

    def test_format_docstring_with_examples(self) -> None:
        """Test formatting a docstring with examples."""
        docstring = """This function does something.

Args:
    param1: Description of param1.

Example:
    >>> result = my_function("test")
    >>> print(result)
    True"""

        indentation = "    "
        result = self.formatter.format_docstring(docstring, indentation)

        self.assertIn("Example:", result)
        self.assertIn(">>> result = my_function", result)

    def test_format_docstring_with_raises_section(self) -> None:
        """Test formatting a docstring with Raises section."""
        docstring = """This function does something.

Args:
    param1: Description of param1.

Raises:
    ValueError: If param1 is invalid.
    TypeError: If param1 is not a string."""

        indentation = "    "
        result = self.formatter.format_docstring(docstring, indentation)

        self.assertIn("Raises:", result)
        self.assertIn("ValueError:", result)
        self.assertIn("TypeError:", result)

    def test_should_indent_line_google(self) -> None:
        """Test the Google indentation logic."""
        # Parameter descriptions should be indented
        self.assertTrue(
            self.formatter._should_indent_line_google("param1: description")
        )
        self.assertTrue(
            self.formatter._should_indent_line_google("param2 (int): description")
        )

        # Section headers should not be indented
        self.assertFalse(self.formatter._should_indent_line_google("Args:"))
        self.assertFalse(self.formatter._should_indent_line_google("Returns:"))
        self.assertFalse(self.formatter._should_indent_line_google("Raises:"))

        # Regular content should not be indented
        self.assertFalse(
            self.formatter._should_indent_line_google("This is regular content.")
        )


class TestNumpyFormatter(unittest.TestCase):
    """Test the NumPy-style docstring formatter."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.formatter = NumpyFormatter()

    def test_format_single_line_docstring(self) -> None:
        """Test formatting a single line docstring."""
        docstring = "This is a simple docstring."
        indentation = "    "

        result = self.formatter.format_docstring(docstring, indentation)

        expected = '    """This is a simple docstring."""\n'
        self.assertEqual(result, expected)

    def test_format_multi_line_docstring(self) -> None:
        """Test formatting a multi-line docstring."""
        docstring = "This is a multi-line docstring.\n\nIt has multiple paragraphs."
        indentation = "    "

        result = self.formatter.format_docstring(docstring, indentation)

        # Should format with proper indentation and quotes
        self.assertIn('"""This is a multi-line docstring.', result)
        self.assertIn("It has multiple paragraphs.", result)
        self.assertIn('"""', result)

    def test_format_docstring_with_parameters_section(self) -> None:
        """Test formatting a docstring with Parameters section."""
        docstring = """This function does something.

Parameters
----------
param1 : str
    Description of param1.
param2 : int
    Description of param2.
param3 : str, optional
    Description of param3.

Returns
-------
bool
    Description of return value."""

        indentation = "    "
        result = self.formatter.format_docstring(docstring, indentation)

        # Should format Parameters section properly
        self.assertIn("Parameters", result)
        self.assertIn("param1 : str", result)
        self.assertIn("param2 : int", result)
        self.assertIn("Returns", result)

    def test_format_docstring_with_section_headers(self) -> None:
        """Test formatting a docstring with section headers and underlines."""
        docstring = """This function does something.

Parameters
----------
param1 : str
    Description of param1.

Returns
-------
bool
    Description of return value."""

        indentation = "    "
        result = self.formatter.format_docstring(docstring, indentation)

        # Should preserve section headers and underlines
        self.assertIn("Parameters", result)
        self.assertIn("Returns", result)
        self.assertIn("----------", result)

    def test_format_docstring_with_parameter_indentation(self) -> None:
        """Test that parameter descriptions are properly indented."""
        docstring = """This function does something.

Parameters
----------
param1 : str
    This is a long description that should be properly indented
    and wrapped correctly.
param2 : int
    Another parameter with a description."""

        indentation = "    "
        result = self.formatter.format_docstring(docstring, indentation)

        # Parameter descriptions should have extra indentation
        self.assertIn("param1 : str", result)
        self.assertIn("        and wrapped correctly.", result)

    def test_format_empty_docstring(self) -> None:
        """Test formatting an empty docstring."""
        docstring = ""
        indentation = "    "

        result = self.formatter.format_docstring(docstring, indentation)

        self.assertEqual(result, "")

    def test_format_none_docstring(self) -> None:
        """Test formatting a None docstring."""
        docstring = None
        indentation = "    "

        result = self.formatter.format_docstring(docstring, indentation)

        self.assertEqual(result, "")

    def test_format_docstring_with_examples(self) -> None:
        """Test formatting a docstring with examples."""
        docstring = """This function does something.

Parameters
----------
param1 : str
    Description of param1.

Examples
--------
>>> result = my_function("test")
>>> print(result)
True"""

        indentation = "    "
        result = self.formatter.format_docstring(docstring, indentation)

        self.assertIn("Examples", result)
        self.assertIn(">>> result = my_function", result)

    def test_format_docstring_with_raises_section(self) -> None:
        """Test formatting a docstring with Raises section."""
        docstring = """This function does something.

Parameters
----------
param1 : str
    Description of param1.

Raises
------
ValueError
    If param1 is invalid.
TypeError
    If param1 is not a string."""

        indentation = "    "
        result = self.formatter.format_docstring(docstring, indentation)

        self.assertIn("Raises", result)
        self.assertIn("ValueError", result)
        self.assertIn("TypeError", result)

    def test_is_numpy_section_header(self) -> None:
        """Test NumPy section header detection."""
        lines = ["Parameters", "----------", "param1 : str", "    description"]

        # Section names should be detected
        self.assertTrue(self.formatter._is_numpy_section_header("Parameters", lines, 0))
        self.assertTrue(self.formatter._is_numpy_section_header("Returns", lines, 0))

        # Lines with dashes should NOT be detected as section headers themselves
        self.assertFalse(
            self.formatter._is_numpy_section_header("----------", lines, 1)
        )

        # Regular content should not be detected
        self.assertFalse(
            self.formatter._is_numpy_section_header("param1 : str", lines, 2)
        )

        # Test that a line is detected as header when next line has dashes
        lines_with_dashes = ["SomeSection", "----------", "content"]
        self.assertTrue(
            self.formatter._is_numpy_section_header("SomeSection", lines_with_dashes, 0)
        )

    def test_should_indent_line_numpy(self) -> None:
        """Test the NumPy indentation logic."""
        # Parameter descriptions should be indented
        self.assertTrue(
            self.formatter._should_indent_line_numpy("    Description of param1.")
        )
        self.assertTrue(self.formatter._should_indent_line_numpy("param1 : str"))

        # Section headers should not be indented
        self.assertFalse(self.formatter._should_indent_line_numpy("Parameters"))
        self.assertFalse(self.formatter._should_indent_line_numpy("Returns"))

        # Dash underlines should not be indented
        self.assertFalse(self.formatter._should_indent_line_numpy("----------"))


class TestGetFormatter(unittest.TestCase):
    """Test the get_formatter function."""

    def test_get_google_formatter(self) -> None:
        """Test getting a Google formatter."""
        formatter = get_formatter("google")
        self.assertIsInstance(formatter, GoogleFormatter)

    def test_get_numpy_formatter(self) -> None:
        """Test getting a NumPy formatter."""
        formatter = get_formatter("numpy")
        self.assertIsInstance(formatter, NumpyFormatter)

    def test_get_formatter_case_insensitive(self) -> None:
        """Test that formatter selection is case insensitive."""
        google_formatter = get_formatter("GOOGLE")
        numpy_formatter = get_formatter("NUMPY")

        self.assertIsInstance(google_formatter, GoogleFormatter)
        self.assertIsInstance(numpy_formatter, NumpyFormatter)

    def test_get_formatter_invalid_style(self) -> None:
        """Test that invalid styles raise ValueError."""
        with self.assertRaises(ValueError):
            get_formatter("invalid_style")

    def test_get_formatter_empty_style(self) -> None:
        """Test that empty style raises ValueError."""
        with self.assertRaises(ValueError):
            get_formatter("")


class TestDocstringStyle(unittest.TestCase):
    """Test the DocstringStyle enum."""

    def test_from_string_google(self) -> None:
        """Test creating DocstringStyle from 'google' string."""
        style = DocstringStyle.from_string("google")
        self.assertEqual(style, DocstringStyle.GOOGLE)

    def test_from_string_numpy(self) -> None:
        """Test creating DocstringStyle from 'numpy' string."""
        style = DocstringStyle.from_string("numpy")
        self.assertEqual(style, DocstringStyle.NUMPY)

    def test_from_string_case_insensitive(self) -> None:
        """Test that from_string is case insensitive."""
        google_style = DocstringStyle.from_string("GOOGLE")
        numpy_style = DocstringStyle.from_string("NUMPY")

        self.assertEqual(google_style, DocstringStyle.GOOGLE)
        self.assertEqual(numpy_style, DocstringStyle.NUMPY)

    def test_from_string_invalid(self) -> None:
        """Test that invalid strings raise ValueError."""
        with self.assertRaises(ValueError):
            DocstringStyle.from_string("invalid")

    def test_from_string_empty(self) -> None:
        """Test that empty string raises ValueError."""
        with self.assertRaises(ValueError):
            DocstringStyle.from_string("")


if __name__ == "__main__":
    unittest.main()
