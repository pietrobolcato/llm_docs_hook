"""Docstring formatters for different styles."""

from abc import ABC, abstractmethod

from src.llm_docs_hook.docstring_processor.types import DocstringStyle


class DocstringFormatter(ABC):
    """Abstract base class for docstring formatters."""

    @abstractmethod
    def format_docstring(self, docstring: str, indentation: str) -> str:
        """Format a docstring with proper indentation and style-specific formatting.

        Args:
            docstring (str): The raw docstring content.
            indentation (str): The base indentation string to use.

        Returns:
            str: Properly formatted docstring with quotes and indentation.
        """
        pass


class GoogleFormatter(DocstringFormatter):
    """Formatter for Google-style docstrings."""

    def format_docstring(self, docstring: str, indentation: str) -> str:
        """Format a Google-style docstring with proper indentation and quotes.

        Args:
            docstring (str): The raw docstring content.
            indentation (str): The base indentation string to use.

        Returns:
            str: Properly formatted Google-style docstring.
        """
        if not docstring:
            return ""

        lines = docstring.split("\n")
        formatted_lines = []

        # Opening triple quotes with first line
        if lines and lines[0].strip():
            formatted_lines.append(f'{indentation}"""{lines[0].strip()}\n')
            start_index = 1
        else:
            formatted_lines.append(f'{indentation}"""\n')
            start_index = 1

        # Process remaining lines while preserving relative indentation
        for line in lines[start_index:]:
            if not line.strip():
                # Empty line
                formatted_lines.append("\n")
            else:
                stripped_line = line.strip()

                # Google-style specific formatting
                if self._should_indent_line_google(stripped_line):
                    # Add extra indentation for parameter descriptions
                    formatted_lines.append(f"{indentation}    {stripped_line}\n")
                else:
                    # Regular docstring line or section header
                    formatted_lines.append(f"{indentation}{stripped_line}\n")

        # Closing triple quotes
        if len(lines) > 1:
            formatted_lines.append(f'{indentation}"""\n')
        else:
            # Single line docstring - close on the same line
            if formatted_lines:
                formatted_lines[0] = formatted_lines[0].rstrip("\n") + '"""\n'

        return "".join(formatted_lines)

    def _should_indent_line_google(self, line: str) -> bool:
        """Check if a line should get extra indentation in Google style.

        Args:
            line (str): The stripped line content.

        Returns:
            bool: True if the line should be indented further.
        """
        # Section headers should not be indented
        google_sections = [
            "Args:",
            "Arguments:",
            "Parameters:",
            "Returns:",
            "Return:",
            "Yields:",
            "Raises:",
            "Note:",
            "Notes:",
            "Example:",
            "Examples:",
            "See Also:",
            "Attributes:",
        ]

        if line.endswith(":") and line in google_sections:
            return False

        # Only indent lines that look like parameter definitions
        # Parameter format: "param_name (type): description" or "param_name: description"
        if ":" in line:
            # Check if this looks like a parameter definition
            # Usually starts with a word, may have (type), then has colon
            parts = line.split(":", 1)
            if len(parts) == 2:
                param_part = parts[0].strip()
                # Simple heuristic: if it has parentheses or looks like param name
                if ("(" in param_part and ")" in param_part) or (
                    param_part.replace("_", "").replace("-", "").isalnum()
                    and len(param_part.split()) <= 3
                ):  # Simple param name pattern
                    return True

        return False


class NumpyFormatter(DocstringFormatter):
    """Formatter for NumPy-style docstrings."""

    def format_docstring(self, docstring: str, indentation: str) -> str:
        """Format a NumPy-style docstring with proper indentation and quotes.

        Args:
            docstring (str): The raw docstring content.
            indentation (str): The base indentation string to use.

        Returns:
            str: Properly formatted NumPy-style docstring.
        """
        if not docstring:
            return ""

        lines = docstring.split("\n")
        formatted_lines = []

        # Opening triple quotes with first line
        if lines and lines[0].strip():
            formatted_lines.append(f'{indentation}"""{lines[0].strip()}\n')
            start_index = 1
        else:
            formatted_lines.append(f'{indentation}"""\n')
            start_index = 1

        # Process remaining lines for NumPy style
        i = start_index
        while i < len(lines):
            line = lines[i]

            if not line.strip():
                formatted_lines.append("\n")
                i += 1
                continue

            stripped_line = line.strip()

            # Check if this is a NumPy section header
            if self._is_numpy_section_header(stripped_line, lines, i):
                # Add section header
                formatted_lines.append(f"{indentation}{stripped_line}\n")
                i += 1

                # Add underline dashes if next line has them
                if (
                    i < len(lines)
                    and lines[i].strip()
                    and all(c == "-" for c in lines[i].strip())
                ):
                    formatted_lines.append(f"{indentation}{lines[i].strip()}\n")
                    i += 1
            else:
                # Regular content line - apply appropriate indentation
                if self._should_indent_line_numpy(stripped_line):
                    formatted_lines.append(f"{indentation}    {stripped_line}\n")
                else:
                    formatted_lines.append(f"{indentation}{stripped_line}\n")
                i += 1

        # Closing triple quotes
        if len(lines) > 1:
            formatted_lines.append(f'{indentation}"""\n')
        else:
            if formatted_lines:
                formatted_lines[0] = formatted_lines[0].rstrip("\n") + '"""\n'

        return "".join(formatted_lines)

    def _is_numpy_section_header(self, line: str, lines: list[str], index: int) -> bool:
        """Check if a line is a NumPy section header.

        Args:
            line (str): The current line content.
            lines (list[str]): All lines in the docstring.
            index (int): Current line index.

        Returns:
            bool: True if this is a NumPy section header.
        """
        numpy_sections = [
            "Parameters",
            "Returns",
            "Yields",
            "Raises",
            "See Also",
            "Notes",
            "Examples",
            "Attributes",
            "Methods",
        ]

        # Check if line is a section name
        if line in numpy_sections:
            return True

        # Check if next line is dashes (NumPy style underline)
        if (
            index + 1 < len(lines)
            and lines[index + 1].strip()
            and all(c == "-" for c in lines[index + 1].strip())
        ):
            return True

        return False

    def _should_indent_line_numpy(self, line: str) -> bool:
        """Check if a line should get extra indentation in NumPy style.

        Args:
            line (str): The stripped line content.

        Returns:
            bool: True if the line should be indented further.
        """
        # Lines that are parameter descriptions should be indented
        # But not section headers or dash lines
        if all(c == "-" for c in line):  # Dash underline
            return False

        numpy_sections = [
            "Parameters",
            "Returns",
            "Yields",
            "Raises",
            "See Also",
            "Notes",
            "Examples",
            "Attributes",
            "Methods",
        ]

        if line in numpy_sections:
            return False

        # Parameter lines and descriptions should be indented
        return True


def get_formatter(style: str) -> DocstringFormatter:
    """Get the appropriate formatter for a docstring style.

    Args:
        style (str): The docstring style ('google' or 'numpy').

    Returns:
        DocstringFormatter: The appropriate formatter instance.

    Raises:
        ValueError: If the style is not supported.
    """
    # Convert string to enum for validation
    docstring_style = DocstringStyle.from_string(style)

    if docstring_style == DocstringStyle.GOOGLE:
        return GoogleFormatter()
    elif docstring_style == DocstringStyle.NUMPY:
        return NumpyFormatter()
    else:
        # This should never happen due to enum validation, but keeping for safety
        raise ValueError(
            f"Unsupported docstring style: '{style}'. "
            f"Supported styles: {[s.value for s in DocstringStyle]}"
        )
