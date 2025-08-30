"""Tests for LLM client functionality.

This module contains unit tests for the LLM docstring generator, focusing on:
- API key validation and initialization
- Prompt creation and formatting
- Docstring extraction and cleaning
- Error handling for API failures
"""

import unittest
from unittest.mock import MagicMock, patch

from src.llm_docs_hook.ast_parser.types import CodeElement
from src.llm_docs_hook.llm_client.llm_client import LLMDocstringGenerator


class TestLLMDocstringGenerator(unittest.TestCase):
    """Test the LLM docstring generator functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create a mock config object with nested structure
        self.config = MagicMock()

        # Mock LLM config
        llm_mock = MagicMock()
        llm_mock.provider = "openai"
        llm_mock.model = "openai/gpt-4o-mini"
        llm_mock.temperature = 0.1
        llm_mock.max_tokens = 1000
        llm_mock.custom_requirements = None
        self.config.llm = llm_mock

        # Mock docstring config
        docstring_mock = MagicMock()
        docstring_mock.style = "google"
        docstring_mock.include_types = True
        docstring_mock.include_examples = False
        self.config.docstring = docstring_mock

        # Mock API key method
        self.config.get_api_key.return_value = "test-api-key-123"

        self.generator = LLMDocstringGenerator(self.config)

    def test_initialization_with_valid_config(self) -> None:
        """Test that LLM client initializes correctly with valid config."""
        self.assertEqual(self.generator.config, self.config)
        self.assertEqual(self.generator.api_key, "test-api-key-123")

    def test_initialization_without_api_key_raises_error(self) -> None:
        """Test that initialization fails when no API key is provided."""
        # Create a mock config object
        config = MagicMock()
        llm_mock = MagicMock()
        llm_mock.provider = "openai"
        config.llm = llm_mock
        config.get_api_key.return_value = None

        with self.assertRaises(ValueError) as context:
            LLMDocstringGenerator(config)

        self.assertIn("No API key found", str(context.exception))

    def test_create_prompt_for_function(self) -> None:
        """Test prompt creation for a function."""
        element = CodeElement(
            name="test_function",
            element_type="function",
            line_number=5,
            end_line_number=10,
            signature="def test_function(param1, param2):",
            has_docstring=False,
            is_incomplete_docstring=False,
        )

        source_code = "def test_function(param1, param2):\n    return param1 + param2"

        prompt = self.generator._create_prompt(element, source_code)

        # Verify prompt contains expected elements
        self.assertIn("ElementType.FUNCTION", prompt)  # Enum value in prompt
        self.assertIn("Google-style", prompt)  # Default style
        self.assertIn("param1", prompt)
        self.assertIn("param2", prompt)

    def test_create_prompt_for_class(self) -> None:
        """Test prompt creation for a class."""
        element = CodeElement(
            name="TestClass",
            element_type="class",
            line_number=3,
            end_line_number=8,
            signature="class TestClass:",
            has_docstring=False,
            is_incomplete_docstring=False,
        )

        source_code = "class TestClass:\n    def __init__(self):\n        pass"

        prompt = self.generator._create_prompt(element, source_code)

        # Verify prompt contains expected elements
        self.assertIn("ElementType.CLASS", prompt)  # Enum value in prompt
        self.assertIn("__init__", prompt)

    def test_extract_docstring_clean_text(self) -> None:
        """Test docstring extraction from clean text."""
        clean_text = "This is a simple docstring."
        result = self.generator._extract_docstring(clean_text)

        self.assertEqual(result, "This is a simple docstring.")

    def test_extract_docstring_with_code_blocks(self) -> None:
        """Test docstring extraction from text with code blocks."""
        text_with_blocks = '```\n"""This is a docstring in a code block."""\n```'
        result = self.generator._extract_docstring(text_with_blocks)

        self.assertEqual(result, "This is a docstring in a code block.")

    def test_extract_docstring_with_triple_quotes(self) -> None:
        """Test docstring extraction removes triple quotes."""
        text_with_quotes = '"""This is a docstring with quotes."""'
        result = self.generator._extract_docstring(text_with_quotes)

        self.assertEqual(result, "This is a docstring with quotes.")

    def test_extract_context_simple_function(self) -> None:
        """Test context extraction for a simple function."""
        element = CodeElement(
            name="simple_func",
            element_type="function",
            line_number=5,  # 1-based, will be converted to 0-based
            end_line_number=7,
            signature="def simple_func():",
            has_docstring=False,
            is_incomplete_docstring=False,
        )

        source_code = (
            "import os\n\ndef simple_func():\n    return True\n\nprint('done')"
        )

        context = self.generator._extract_context(element, source_code)

        # Should include lines around the function (with some padding)
        self.assertIn("def simple_func():", context)
        self.assertIn("return True", context)

    @patch("src.llm_docs_hook.llm_client.llm_client.completion")
    def test_generate_single_docstring_success(
        self, mock_completion: MagicMock
    ) -> None:
        """Test successful docstring generation."""
        # Mock the completion response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = '"""This is a generated docstring."""'
        mock_completion.return_value = mock_response

        element = CodeElement(
            name="test_func",
            element_type="function",
            line_number=1,
            end_line_number=3,
            signature="def test_func():",
            has_docstring=False,
            is_incomplete_docstring=False,
        )

        source_code = "def test_func():\n    pass"

        result = self.generator._generate_single_docstring(element, source_code)

        self.assertEqual(result, "This is a generated docstring.")
        mock_completion.assert_called_once()

    @patch("src.llm_docs_hook.llm_client.llm_client.completion")
    def test_generate_single_docstring_api_error(
        self, mock_completion: MagicMock
    ) -> None:
        """Test docstring generation handles API errors gracefully."""
        mock_completion.side_effect = Exception("API Error")

        element = CodeElement(
            name="test_func",
            element_type="function",
            line_number=1,
            end_line_number=3,
            signature="def test_func():",
            has_docstring=False,
            is_incomplete_docstring=False,
        )

        source_code = "def test_func():\n    pass"

        result = self.generator._generate_single_docstring(element, source_code)

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
