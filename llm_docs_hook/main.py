"""Main entry point for the LLM docs hook pre-commit tool."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from llm_docs_hook.ast_parser.ast_parser import PythonASTParser
from llm_docs_hook.config.utils import create_sample_config, load_config
from llm_docs_hook.docstring_processor.docstring_processor import DocstringProcessor


def create_sample_config_file() -> None:
    """Create a sample configuration file in the current directory."""
    create_sample_config()


def process_files(
    file_paths: list[str], config_path: Optional[str] = None, verbose: bool = False
) -> int:
    """Process files for docstring generation.

    Args:
        file_paths (list[str]): list of Python file paths to process.
        config_path (str): Path to configuration file. Optional, defaults to None.
        verbose (bool): Enable verbose output. Optional, defaults to False.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    try:
        # Load configuration
        config_file_path = Path(config_path) if config_path else None
        config = load_config(config_file_path)
        if verbose:
            config.processing.verbose = True

        # Initialize components
        ast_parser = PythonASTParser(
            include_private=False,
            update_incomplete=config.processing.update_incomplete_docstrings,
        )
        processor = DocstringProcessor(config)

        total_files_modified = 0
        total_docstrings_added = 0

        for file_path_str in file_paths:
            file_path = Path(file_path_str)

            if not file_path.exists():
                print(f"Warning: File not found: {file_path}")
                continue

            if file_path.suffix != ".py":
                if verbose:
                    print(f"Skipping non-Python file: {file_path}")
                continue

            try:
                # Parse file for functions/classes needing docstrings
                elements = ast_parser.parse_file(file_path)
                elements_needing_docs = [
                    e
                    for e in elements
                    if not e.has_docstring or e.is_incomplete_docstring
                ]

                if elements_needing_docs:
                    if verbose:
                        print(
                            f"Processing {file_path}: {len(elements_needing_docs)} elements need docstrings"
                        )

                    # Process the file
                    was_modified = processor.process_file(
                        file_path, elements_needing_docs
                    )

                    if was_modified:
                        total_files_modified += 1
                        total_docstrings_added += len(elements_needing_docs)

                        # Validate syntax after modification
                        if not processor.validate_insertion(file_path):
                            print(f"Error: Syntax validation failed for {file_path}")
                            if config.processing.backup_files:
                                processor.restore_backup(file_path)
                            return 1
                else:
                    if verbose:
                        print(f"No docstrings needed for {file_path}")

            except Exception as error:
                print(f"Error processing {file_path}: {error}")
                continue

        # Summary
        if verbose or total_files_modified > 0:
            print(
                f"Summary: Modified {total_files_modified} files, added {total_docstrings_added} docstrings"
            )

        return 0

    except Exception as error:
        print(f"Error: {error}")
        return 1


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Generate docstrings for Python functions and classes using LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process files (typically called by pre-commit)
  llm-docs-hook file1.py file2.py

  # Process specific files manually
  llm-docs-hook module.py utils.py

  # Create sample configuration
  llm-docs-hook --create-config

  # Run with verbose output
  llm-docs-hook --verbose file1.py
        """,
    )

    parser.add_argument("files", nargs="*", help="Python files to process")

    parser.add_argument("--config", help="Path to configuration file")

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--create-config",
        action="store_true",
        help="Create a sample configuration file and exit",
    )

    args = parser.parse_args()

    if args.create_config:
        create_sample_config_file()
        print("Sample configuration created: .docstring_config.yaml")
        print(
            "Edit this file to customize your settings, then set your LLM API key with LLM_DOCS_HOOK_ prefix in .env"
        )
        sys.exit(0)

    # Process files (passed as positional arguments)
    if not args.files:
        print("No files specified to process")
        sys.exit(0)

    exit_code = process_files(args.files, args.config, args.verbose)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
