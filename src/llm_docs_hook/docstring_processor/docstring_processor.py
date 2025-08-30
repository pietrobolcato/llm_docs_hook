"""Docstring processor for inserting generated docstrings into Python files."""

import shutil
from pathlib import Path
from typing import List, Optional, Tuple

from src.llm_docs_hook.ast_parser.types import CodeElement
from src.llm_docs_hook.config.types import Config
from src.llm_docs_hook.llm_client.llm_client import LLMDocstringGenerator


class DocstringProcessor:
    """Processes Python files to add missing docstrings."""

    def __init__(self, config: Config):
        """Initialize the docstring processor.

        Args:
            config (Config): Configuration object for processing settings.
        """
        self.config = config
        self.llm_generator = LLMDocstringGenerator(config)

    def process_file(self, file_path: Path, elements: List[CodeElement]) -> bool:
        """Process a Python file to add docstrings to specified elements.

        Args:
            file_path (Path): Path to the Python file to process.
            elements (List[CodeElement]): List of code elements that need docstrings.

        Returns:
            bool: True if the file was modified, False otherwise.
        """
        if not elements:
            return False

        try:
            # Read the original file
            with open(file_path, 'r', encoding='utf-8') as file:
                original_content = file.read()

            # Create backup if configured
            if self.config.processing.backup_files:
                self._create_backup(file_path)

            # Process elements in reverse order (by line number) to avoid offset issues
            elements_sorted = sorted(elements, key=lambda x: x.line_number, reverse=True)
            
            modified_content = original_content
            modifications_made = False

            for element in elements_sorted:
                docstring = self.llm_generator.generate_docstring(element, original_content)
                
                if docstring:
                    if element.has_docstring and element.is_incomplete_docstring:
                        # Replace existing incomplete docstring
                        modified_content = self._replace_docstring(
                            modified_content, element, docstring
                        )
                        action = "Updated"
                    else:
                        # Insert new docstring
                        modified_content = self._insert_docstring(
                            modified_content, element, docstring
                        )
                        action = "Added"
                        
                    modifications_made = True
                    
                    if self.config.processing.verbose:
                        print(f"{action} docstring for {element.element_type} '{element.name}' in {file_path}")
                else:
                    print(f"Warning: Could not generate docstring for {element.element_type} '{element.name}' in {file_path}")

            # Write the modified content back if changes were made
            if modifications_made:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(modified_content)
                
                if self.config.processing.verbose:
                    print(f"Updated file: {file_path}")

            return modifications_made

        except Exception as error:
            print(f"Error processing file {file_path}: {error}")
            return False

    def _create_backup(self, file_path: Path) -> None:
        """Create a backup of the original file.

        Args:
            file_path (Path): Path to the file to backup.
        """
        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
        try:
            shutil.copy2(file_path, backup_path)
            if self.config.processing.verbose:
                print(f"Created backup: {backup_path}")
        except Exception as error:
            print(f"Warning: Could not create backup for {file_path}: {error}")

    def _insert_docstring(self, content: str, element: CodeElement, docstring: str) -> str:
        """Insert a docstring into the file content.

        Args:
            content (str): The file content.
            element (CodeElement): The code element to add the docstring to.
            docstring (str): The generated docstring content.

        Returns:
            str: Modified content with the docstring inserted.
        """
        lines = content.splitlines(keepends=True)
        
        # Find the insertion point (after the function/class definition)
        insertion_line = self._find_insertion_point(lines, element)
        
        if insertion_line is None:
            print(f"Warning: Could not find insertion point for {element.name}")
            return content

        # Format the docstring with proper indentation
        indentation = self._get_indentation(lines, element)
        formatted_docstring = self._format_docstring(docstring, indentation)

        # Insert the docstring
        lines.insert(insertion_line, formatted_docstring)
        
        return ''.join(lines)

    def _replace_docstring(self, content: str, element: CodeElement, new_docstring: str) -> str:
        """Replace an existing docstring with a new one.

        Args:
            content (str): The file content.
            element (CodeElement): The code element with the docstring to replace.
            new_docstring (str): The new docstring content.

        Returns:
            str: Modified content with the docstring replaced.
        """
        lines = content.splitlines(keepends=True)
        
        # Find the existing docstring location
        docstring_start, docstring_end = self._find_existing_docstring_range(lines, element)
        
        if docstring_start is None or docstring_end is None:
            print(f"Warning: Could not find existing docstring for {element.name}")
            return content

        # Format the new docstring with proper indentation
        indentation = self._get_indentation(lines, element)
        formatted_docstring = self._format_docstring(new_docstring, indentation)

        # Replace the existing docstring
        # Remove old docstring lines
        del lines[docstring_start:docstring_end + 1]
        
        # Insert new docstring
        lines.insert(docstring_start, formatted_docstring)
        
        return ''.join(lines)

    def _find_existing_docstring_range(self, lines: List[str], element: CodeElement) -> Tuple[Optional[int], Optional[int]]:
        """Find the line range of an existing docstring.

        Args:
            lines (List[str]): Lines of the file content.
            element (CodeElement): The code element to find the docstring for.

        Returns:
            Tuple[Optional[int], Optional[int]]: Start and end line indices of the docstring, or (None, None) if not found.
        """
        # Find the function/class definition line
        definition_line = element.line_number - 1  # Convert to 0-based
        
        # Look for the docstring after the definition
        for index in range(definition_line, min(len(lines), definition_line + 10)):
            line = lines[index].strip()
            if '"""' in line or "'''" in line:
                docstring_start = index
                
                # Find the end of the docstring
                quote_type = '"""' if '"""' in line else "'''"
                
                # Check if it's a single-line docstring
                if line.count(quote_type) >= 2:
                    return docstring_start, docstring_start
                
                # Multi-line docstring - find the closing quotes
                for end_index in range(docstring_start + 1, len(lines)):
                    if quote_type in lines[end_index]:
                        return docstring_start, end_index
                
                # If we couldn't find the end, something's wrong
                break
        
        return None, None

    def _find_insertion_point(self, lines: List[str], element: CodeElement) -> Optional[int]:
        """Find where to insert the docstring in the file.

        Args:
            lines (List[str]): Lines of the file content.
            element (CodeElement): The code element to find insertion point for.

        Returns:
            Optional[int]: Line index where to insert the docstring, or None if not found.
        """
        # Convert to 0-based indexing
        start_line = element.line_number - 1
        
        # Look for the colon that ends the function/class definition
        for index in range(start_line, min(len(lines), start_line + 10)):
            line = lines[index]
            if ':' in line:
                # Insert after this line
                return index + 1
        
        # Fallback: insert after the start line
        return start_line + 1

    def _get_indentation(self, lines: List[str], element: CodeElement) -> str:
        """Get the proper indentation for the docstring.

        Args:
            lines (List[str]): Lines of the file content.
            element (CodeElement): The code element to get indentation for.

        Returns:
            str: The indentation string to use.
        """
        # Get the line with the function/class definition
        definition_line_index = element.line_number - 1  # Convert to 0-based
        
        if definition_line_index < len(lines):
            definition_line = lines[definition_line_index]
            
            # Get base indentation from the definition line
            base_indent = len(definition_line) - len(definition_line.lstrip())
            
            # Add one level of indentation for the docstring content
            return ' ' * (base_indent + 4)
        
        return '    '  # Default 4-space indentation

    def _format_docstring(self, docstring: str, indentation: str) -> str:
        """Format a docstring with proper indentation and quotes.

        Args:
            docstring (str): The raw docstring content.
            indentation (str): The indentation string to use.

        Returns:
            str: Properly formatted docstring with quotes and indentation.
        """
        if not docstring:
            return ""
        
        # Split into lines for proper formatting
        lines = docstring.split('\n')
        
        # Build the formatted docstring
        formatted_lines = []
        
        # Opening triple quotes
        formatted_lines.append(f'{indentation}"""{lines[0] if lines else ""}\n')
        
        # Middle lines (if any)
        for line in lines[1:]:
            if line.strip():
                formatted_lines.append(f'{indentation}{line}\n')
            else:
                formatted_lines.append('\n')
        
        # Closing triple quotes (only if we have multiple lines)
        if len(lines) > 1:
            formatted_lines.append(f'{indentation}"""\n')
        else:
            # Single line docstring - close on the same line
            if formatted_lines:
                formatted_lines[0] = formatted_lines[0].rstrip('\n') + '"""\n'
        
        return ''.join(formatted_lines)

    def validate_insertion(self, file_path: Path) -> bool:
        """Validate that docstring insertions didn't break the Python syntax.

        Args:
            file_path (Path): Path to the Python file to validate.

        Returns:
            bool: True if the file is syntactically valid, False otherwise.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Try to parse the file as Python
            compile(content, str(file_path), 'exec')
            return True
            
        except SyntaxError as error:
            print(f"Syntax error in {file_path} after docstring insertion: {error}")
            return False
        except Exception as error:
            print(f"Error validating {file_path}: {error}")
            return False

    def restore_backup(self, file_path: Path) -> bool:
        """Restore a file from its backup.

        Args:
            file_path (Path): Path to the original file to restore.

        Returns:
            bool: True if backup was restored successfully, False otherwise.
        """
        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
        
        if not backup_path.exists():
            print(f"No backup found for {file_path}")
            return False
        
        try:
            shutil.copy2(backup_path, file_path)
            print(f"Restored {file_path} from backup")
            return True
        except Exception as error:
            print(f"Error restoring backup for {file_path}: {error}")
            return False

    def cleanup_backups(self, file_paths: List[Path]) -> None:
        """Clean up backup files.

        Args:
            file_paths (List[Path]): List of original file paths to clean backups for.
        """
        for file_path in file_paths:
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
            if backup_path.exists():
                try:
                    backup_path.unlink()
                    if self.config.processing.verbose:
                        print(f"Cleaned up backup: {backup_path}")
                except Exception as error:
                    print(f"Warning: Could not clean up backup {backup_path}: {error}")
