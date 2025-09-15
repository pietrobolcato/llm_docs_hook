"""LLM client for generating docstrings using any-llm."""

import asyncio
from typing import Optional

from any_llm import completion

from llm_docs_hook.ast_parser.types import CodeElement
from llm_docs_hook.config.types import Config
from llm_docs_hook.llm_client.base_prompt import base_prompt


class LLMDocstringGenerator:
    """Generates docstrings using LLM via any-llm library."""

    def __init__(self, config: Config):
        """Initialize the LLM docstring generator.

        Args:
            config (Config): Configuration object containing LLM settings.
        """
        self.config = config
        self.api_key = config.get_api_key()

        if not self.api_key:
            raise ValueError(
                f"No API key found for provider '{config.llm.provider}'. "
                f"Please set LLM_DOCS_HOOK_{config.llm.provider.upper()}_API_KEY environment variable."
            )

    def _generate_single_docstring(
        self, element: CodeElement, source_code: str
    ) -> Optional[str]:
        """Generate a docstring for a single code element (internal helper).

        Args:
            element (CodeElement): The code element to generate a docstring for.
            source_code (str): The full source code of the file for context.

        Returns:
            Optional[str]: Generated docstring or None if generation failed.
        """
        try:
            prompt = self._create_prompt(element, source_code)

            response = completion(
                model=self.config.llm.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
                api_key=self.api_key,
            )

            if response and response.choices and len(response.choices) > 0:
                generated_text = response.choices[0].message.content
                return self._extract_docstring(generated_text)

            return None

        except Exception as error:
            print(f"Error generating docstring for {element.name}: {error}")
            return None

    async def generate_docstrings(
        self, elements: list[CodeElement], source_code: str, max_parallel: int = 5
    ) -> dict[str, Optional[str]]:
        """Generate docstrings for one or more elements with configurable parallelism.

        Args:
            elements (list[CodeElement]): list of code elements to generate docstrings for.
            source_code (str): The full source code of the file for context.
            max_parallel (int): Maximum number of parallel requests. Defaults to 5.

        Returns:
            dict[str, Optional[str]]: Dictionary mapping element names to generated docstrings.
        """
        # Create a semaphore to limit concurrent requests (1 = sequential, >1 = parallel)
        semaphore = asyncio.Semaphore(max_parallel)

        async def generate_single(element: CodeElement) -> tuple[str, Optional[str]]:
            """Generate docstring for a single element with semaphore control."""
            async with semaphore:
                # Run the synchronous method in a thread pool
                loop = asyncio.get_event_loop()
                docstring = await loop.run_in_executor(
                    None, self._generate_single_docstring, element, source_code
                )
                return element.name, docstring

        # Create tasks for all elements
        tasks = [generate_single(element) for element in elements]

        # Wait for all tasks to complete
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert results to dictionary, handling exceptions
        results = {}
        for result in results_list:
            if isinstance(result, Exception):
                print(f"Error in parallel processing: {result}")
                continue
            element_name, docstring = result
            results[element_name] = docstring

        return results

    def _create_prompt(self, element: CodeElement, source_code: str) -> str:
        """Create a prompt for the LLM to generate a docstring.

        Args:
            element (CodeElement): The code element to document.
            source_code (str): The full source code for context.

        Returns:
            str: The formatted prompt string.
        """
        style = self.config.docstring.style.lower()
        include_types = self.config.docstring.include_types
        include_examples = self.config.docstring.include_examples

        # Extract relevant context around the function/class
        context = self._extract_context(element, source_code)

        # Check if we're updating an existing docstring
        if element.has_docstring and element.is_incomplete_docstring:
            task_description = f"Update and improve the existing docstring for the following Python {element.element_type}"
            existing_note = "\nThe current docstring is incomplete or incorrect. Fix sections so they match the signature exactly."
        else:
            task_description = f"Generate a {style}-style docstring for the following Python {element.element_type}"
            existing_note = ""

        # Build strict requirements about parameters/returns to avoid churn
        # Determine argument names excluding 'self'
        arg_names = [arg for arg in (element.arguments or []) if arg != "self"]
        has_params = len(arg_names) > 0

        param_rules = []
        if element.element_type.value == "function":
            if has_params:
                param_rules.append(
                    f"Only include an Args section listing exactly these parameters, in order: {', '.join(arg_names)}."
                )
                param_rules.append(
                    "Do not add, rename, or omit parameters. Use the exact parameter names from the signature."
                )
            else:
                param_rules.append("Do not include an Args section (no parameters).")

            if element.name == "__init__":
                param_rules.append("Do not include a Returns section for __init__.")

        # Class docstring rules
        if element.element_type.value == "class":
            param_rules.append(
                "Do not include an Args section in the class docstring. Document attributes succinctly."
            )
            param_rules.append(
                "Avoid a Methods section unless explicitly required by config; prefer concise class summary."
            )

        # Combine requirements
        strict_requirements = "\n".join(param_rules)
        if strict_requirements:
            strict_requirements = (
                f"\nStrict rules based on the signature:\n"
                f"- Signature: {element.signature}\n"
                f"{strict_requirements}"
            )

        formatted_base_prompt = base_prompt.format(
            task_description=task_description,
            context=context,
            existing_note=existing_note + strict_requirements,
            requirements=self._get_requirements_text(
                style, include_types, include_examples
            ),
            element=element,
        )

        return formatted_base_prompt

    def _get_requirements_text(
        self, style: str, include_types: bool, include_examples: bool
    ) -> str:
        """Get the requirements text for docstring generation.

        Args:
            style (str): The docstring style (google/numpy).
            include_types (bool): Whether to include type information.
            include_examples (bool): Whether to include examples.

        Returns:
            str: Requirements text for the prompt.
        """
        # Always start with the style requirement (from config)
        base_requirements = [f"- Use {style.title()}-style docstring format"]

        # Add custom requirements if provided, otherwise use defaults
        if self.config.llm.custom_requirements:
            base_requirements.append(self.config.llm.custom_requirements)
        else:
            # Default requirements
            base_requirements.extend([
                "- Be concise but comprehensive",
                "- Include proper descriptions for all parameters and return values",
            ])

        # Add conditional requirements from config
        if include_types:
            base_requirements.append("- Include type information in the docstring")

        if include_examples:
            base_requirements.append("- Include a brief usage example if helpful")

        return "\n".join(base_requirements)

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
        return "\n".join(context_lines)

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
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines if they're code block markers
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)

        # Remove any triple quotes that might have been included
        text = text.replace('"""', "").replace("'''", "")

        return text.strip()
