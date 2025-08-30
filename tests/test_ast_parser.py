"""Tests for AST parser functionality.

This module contains unit tests for the Python AST parser, focusing on:
- File parsing and AST tree creation
- Function and class detection
- Docstring detection and analysis
- Private element filtering
- Error handling for invalid syntax and missing files
"""

import unittest
from unittest.mock import mock_open, patch

from llm_docs_hook.ast_parser.ast_parser import PythonASTParser
from llm_docs_hook.ast_parser.types import ElementType


class TestPythonASTParser(unittest.TestCase):
    """Test the Python AST parser functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.parser = PythonASTParser()

    def test_parse_simple_function(self) -> None:
        """Test parsing a simple function without docstring."""
        source_code = "def simple_function():\n    pass"

        with patch("builtins.open", mock_open(read_data=source_code)):
            with patch("pathlib.Path.exists", return_value=True):
                elements = self.parser.parse_file("test.py")

        self.assertEqual(len(elements), 1)
        element = elements[0]
        self.assertEqual(element.name, "simple_function")
        self.assertEqual(element.element_type, ElementType.FUNCTION)
        self.assertFalse(element.has_docstring)
        self.assertFalse(element.is_private)

    def test_parse_function_with_docstring(self) -> None:
        """Test parsing a function with a complete docstring."""
        source_code = '''def documented_function():
    """This is a complete docstring."""
    pass'''

        with patch("builtins.open", mock_open(read_data=source_code)):
            with patch("pathlib.Path.exists", return_value=True):
                elements = self.parser.parse_file("test.py")

        # Should not include functions with complete docstrings
        self.assertEqual(len(elements), 0)

    def test_parse_class_without_docstring(self) -> None:
        """Test parsing a class without docstring."""
        source_code = "class TestClass:\n    pass"

        with patch("builtins.open", mock_open(read_data=source_code)):
            with patch("pathlib.Path.exists", return_value=True):
                elements = self.parser.parse_file("test.py")

        self.assertEqual(len(elements), 1)
        element = elements[0]
        self.assertEqual(element.name, "TestClass")
        self.assertEqual(element.element_type, ElementType.CLASS)
        self.assertFalse(element.has_docstring)

    def test_parse_private_function_excluded(self) -> None:
        """Test that private functions are excluded by default."""
        source_code = "def _private_function():\n    pass"

        with patch("builtins.open", mock_open(read_data=source_code)):
            with patch("pathlib.Path.exists", return_value=True):
                elements = self.parser.parse_file("test.py")

        # Private functions should be excluded by default
        self.assertEqual(len(elements), 0)

    def test_parse_private_function_included(self) -> None:
        """Test that private functions are included when configured."""
        parser = PythonASTParser(include_private=True)
        source_code = "def _private_function():\n    pass"

        with patch("builtins.open", mock_open(read_data=source_code)):
            with patch("pathlib.Path.exists", return_value=True):
                elements = parser.parse_file("test.py")

        # Private functions should be included when configured
        self.assertEqual(len(elements), 1)
        element = elements[0]
        self.assertEqual(element.name, "_private_function")
        self.assertTrue(element.is_private)

    def test_parse_special_methods_excluded(self) -> None:
        """Test that special methods (except __init__) are excluded."""
        source_code = "def __str__(self):\n    pass"

        with patch("builtins.open", mock_open(read_data=source_code)):
            with patch("pathlib.Path.exists", return_value=True):
                elements = self.parser.parse_file("test.py")

        # Special methods should be excluded
        self.assertEqual(len(elements), 0)

    def test_parse_init_method_included(self) -> None:
        """Test that __init__ method is included."""
        source_code = "def __init__(self):\n    pass"

        with patch("builtins.open", mock_open(read_data=source_code)):
            with patch("pathlib.Path.exists", return_value=True):
                elements = self.parser.parse_file("test.py")

        # __init__ should be included
        self.assertEqual(len(elements), 1)
        element = elements[0]
        self.assertEqual(element.name, "__init__")

    def test_parse_file_not_found(self) -> None:
        """Test that FileNotFoundError is raised for missing files."""
        with patch("pathlib.Path.exists", return_value=False):
            with self.assertRaises(FileNotFoundError):
                self.parser.parse_file("nonexistent.py")

    def test_parse_invalid_syntax(self) -> None:
        """Test that SyntaxError is raised for invalid Python syntax."""
        invalid_code = "def invalid_function(\n    pass"  # Missing closing parenthesis

        with patch("builtins.open", mock_open(read_data=invalid_code)):
            with patch("pathlib.Path.exists", return_value=True):
                with self.assertRaises(SyntaxError):
                    self.parser.parse_file("test.py")

    def test_parse_function_with_arguments(self) -> None:
        """Test parsing a function with arguments."""
        source_code = (
            "def function_with_args(param1, param2):\n    return param1 + param2"
        )

        with patch("builtins.open", mock_open(read_data=source_code)):
            with patch("pathlib.Path.exists", return_value=True):
                elements = self.parser.parse_file("test.py")

        self.assertEqual(len(elements), 1)
        element = elements[0]
        self.assertEqual(element.name, "function_with_args")
        self.assertIn("param1", element.arguments)
        self.assertIn("param2", element.arguments)

    def test_parse_class_with_methods(self) -> None:
        """Test parsing a class with methods."""
        source_code = """class TestClass:
    def method1(self):
        pass
    def method2(self):
        pass"""

        with patch("builtins.open", mock_open(read_data=source_code)):
            with patch("pathlib.Path.exists", return_value=True):
                elements = self.parser.parse_file("test.py")

        # Should find the class and its methods
        self.assertEqual(len(elements), 3)  # class + 2 methods

        element_names = [elem.name for elem in elements]
        self.assertIn("TestClass", element_names)
        self.assertIn("method1", element_names)
        self.assertIn("method2", element_names)

    def test_parse_incomplete_docstring(self) -> None:
        """Test parsing a function with incomplete docstring."""
        source_code = '''def incomplete_function(param1):
    """This is incomplete."""
    pass'''

        parser = PythonASTParser(update_incomplete=True)

        with patch("builtins.open", mock_open(read_data=source_code)):
            with patch("pathlib.Path.exists", return_value=True):
                elements = parser.parse_file("test.py")

        # Should include functions with incomplete docstrings when configured
        self.assertEqual(len(elements), 1)
        element = elements[0]
        self.assertTrue(element.has_docstring)
        self.assertTrue(element.is_incomplete_docstring)

    def test_parse_async_function(self) -> None:
        """Test parsing an async function."""
        source_code = "async def async_function():\n    pass"

        with patch("builtins.open", mock_open(read_data=source_code)):
            with patch("pathlib.Path.exists", return_value=True):
                elements = self.parser.parse_file("test.py")

        self.assertEqual(len(elements), 1)
        element = elements[0]
        self.assertEqual(element.name, "async_function")
        self.assertEqual(element.element_type, ElementType.FUNCTION)

    def test_parse_decorated_function(self) -> None:
        """Test parsing a function with decorators."""
        source_code = """@decorator1
@decorator2
def decorated_function():
    pass"""

        with patch("builtins.open", mock_open(read_data=source_code)):
            with patch("pathlib.Path.exists", return_value=True):
                elements = self.parser.parse_file("test.py")

        self.assertEqual(len(elements), 1)
        element = elements[0]
        self.assertEqual(element.name, "decorated_function")
        self.assertIn("decorator1", element.decorators)
        self.assertIn("decorator2", element.decorators)


if __name__ == "__main__":
    unittest.main()
