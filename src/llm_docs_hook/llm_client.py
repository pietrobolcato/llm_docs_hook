"""LLM client for generating docstrings using any-llm."""

import os
from typing import Optional

from any_llm import completion

from .ast_parser import CodeElement
from .config import DocstringConfig


class LLMDocstringGenerator:
    """Generates docstrings using LLM via any-llm library."""

    def __init__(self, config: DocstringConfig):
        """Initialize the LLM docstring generator.

        Args:
            config (DocstringConfig): Configuration object containing LLM settings.
        """
        self.config = config
        self.api_key = config.get_api_key()
        
        if not self.api_key:
            raise ValueError(
                f"No API key found for provider '{config.llm_provider}'. "
                f"Please set {config.llm_provider.upper()}_API_KEY environment variable."
            )

    def generate_docstring(self, element: CodeElement, source_code: str) -> Optional[str]:
        """Generate a docstring for a code element.

        Args:
            element (CodeElement): The code element to generate a docstring for.
            source_code (str): The full source code of the file for context.

        Returns:
            Optional[str]: Generated docstring or None if generation failed.
        """
        try:
            prompt = self._create_prompt(element, source_code)
            
            response = completion(
                model=self.config.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens,
            )
            
            if response and response.choices and len(response.choices) > 0:
                generated_text = response.choices[0].message.content
                return self._extract_docstring(generated_text)
            
            return None
            
        except Exception as error:
            print(f"Error generating docstring for {element.name}: {error}")
            return None

    def _create_prompt(self, element: CodeElement, source_code: str) -> str:
        """Create a prompt for the LLM to generate a docstring.

        Args:
            element (CodeElement): The code element to document.
            source_code (str): The full source code for context.

        Returns:
            str: The formatted prompt string.
        """
        style = self.config.docstring_style.lower()
        include_types = self.config.include_types
        include_examples = self.config.include_examples
        
        # Extract relevant context around the function/class
        context = self._extract_context(element, source_code)
        
        # Check if we're updating an existing docstring
        if element.has_docstring and element.is_incomplete_docstring:
            task_description = f"Update and improve the existing docstring for the following Python {element.element_type}"
            existing_note = f"\nThe current docstring is incomplete and needs proper Args/Returns sections added."
        else:
            task_description = f"Generate a {style}-style docstring for the following Python {element.element_type}"
            existing_note = ""

        base_prompt = f"""{task_description}:

```python
{context}
```{existing_note}

Requirements:
- Use {style.title()}-style docstring format
- Be concise but comprehensive
- Include proper descriptions for all parameters and return values
"""

        if include_types:
            base_prompt += "- Include type information in the docstring\n"
        
        if include_examples:
            base_prompt += "- Include a brief usage example if helpful\n"
            
        base_prompt += f"""
- Only return the docstring content (without triple quotes)
- The docstring should start immediately after the {element.element_type} definition
- Follow Python documentation best practices

Return only the docstring content, nothing else."""

        return base_prompt

    def _extract_context(self, element: CodeElement, source_code: str) -> str:
        """Extract relevant context around a code element.

        Args:
            element (CodeElement): The code element.
            source_code (str): The full source code.

        Returns:
            str: Relevant context for the element.
        """
        lines = source_code.splitlines()
        start_line = max(0, element.line_number - 1)  # Convert to 0-based
        
        # Include a few lines before for context (decorators, etc.)
        context_start = max(0, start_line - 3)
        
        # Find the end of the function/class (look for next function/class or end of file)
        context_end = min(len(lines), element.end_line_number + 5)
        
        # If we don't have end_line_number, estimate based on indentation
        if element.end_line_number == element.line_number:
            context_end = self._find_element_end(lines, start_line)
        
        context_lines = lines[context_start:context_end]
        return '\n'.join(context_lines)

    def _find_element_end(self, lines: list[str], start_line: int) -> int:
        """Find the end of a function or class based on indentation.

        Args:
            lines (list[str]): All lines in the source file.
            start_line (int): Starting line of the element (0-based).

        Returns:
            int: Estimated end line of the element.
        """
        if start_line >= len(lines):
            return len(lines)
            
        # Get the indentation level of the definition line
        definition_line = lines[start_line]
        base_indent = len(definition_line) - len(definition_line.lstrip())
        
        # Look for the next line with the same or lower indentation
        for index in range(start_line + 1, len(lines)):
            line = lines[index]
            if line.strip():  # Skip empty lines
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= base_indent:
                    return index
        
        return len(lines)

    def _extract_docstring(self, generated_text: str) -> str:
        """Extract and clean the docstring from generated text.

        Args:
            generated_text (str): Raw text generated by the LLM.

        Returns:
            str: Cleaned docstring content.
        """
        # Remove any markdown code blocks
        text = generated_text.strip()
        
        # Remove code block markers if present
        if text.startswith('```'):
            lines = text.split('\n')
            # Remove first and last lines if they're code block markers
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            text = '\n'.join(lines)
        
        # Remove any triple quotes that might have been included
        text = text.strip('"""').strip("'''")
        
        return text.strip()

    def _format_docstring(self, docstring: str, indent_level: int = 4) -> str:
        """Format a docstring with proper indentation and quotes.

        Args:
            docstring (str): The raw docstring content.
            indent_level (int): Number of spaces to indent. Optional, defaults to 4.

        Returns:
            str: Properly formatted docstring with quotes and indentation.
        """
        if not docstring:
            return ""
            
        # Split into lines and add proper indentation
        lines = docstring.split('\n')
        indent = ' ' * indent_level
        
        # Format as triple-quoted docstring
        formatted_lines = [f'{indent}"""']
        
        for line in lines:
            if line.strip():
                formatted_lines.append(f'{indent}{line}')
            else:
                formatted_lines.append('')
        
        formatted_lines.append(f'{indent}"""')
        
        return '\n'.join(formatted_lines)
