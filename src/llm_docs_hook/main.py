"""Main entry point for the LLM docs hook pre-commit tool."""

import argparse
import sys
from pathlib import Path
from typing import List

from src.llm_docs_hook.ast_parser.ast_parser import PythonASTParser
from src.llm_docs_hook.config.types import Config
from src.llm_docs_hook.config.utils import create_sample_config, load_config
from src.llm_docs_hook.docstring_processor.docstring_processor import DocstringProcessor
from src.llm_docs_hook.git_utils import GitModificationDetector


def create_sample_config_file() -> None:
    """Create a sample configuration file in the current directory."""
    create_sample_config()


def process_files(file_paths: List[str], config_path: str = None, verbose: bool = False) -> int:
    """Process specific files for docstring generation.

    Args:
        file_paths (List[str]): List of Python file paths to process.
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
            update_incomplete=config.processing.update_incomplete_docstrings
        )
        processor = DocstringProcessor(config)
        
        total_files_modified = 0
        total_docstrings_added = 0

        for file_path_str in file_paths:
            file_path = Path(file_path_str)
            
            if not file_path.exists():
                print(f"Warning: File not found: {file_path}")
                continue
                
            if not file_path.suffix == '.py':
                if verbose:
                    print(f"Skipping non-Python file: {file_path}")
                continue

            try:
                # Parse file for functions/classes needing docstrings
                elements = ast_parser.parse_file(file_path)
                elements_needing_docs = [e for e in elements if not e.has_docstring or e.is_incomplete_docstring]
                
                if elements_needing_docs:
                    if verbose:
                        print(f"Processing {file_path}: {len(elements_needing_docs)} elements need docstrings")
                    
                    # Process the file
                    was_modified = processor.process_file(file_path, elements_needing_docs)
                    
                    if was_modified:
                        total_files_modified += 1
                        total_docstrings_added += len(elements_needing_docs)
                        
                        # Validate syntax after modification
                        if not processor.validate_insertion(file_path):
                            print(f"Error: Syntax validation failed for {file_path}")
                            if config.backup_files:
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
            print(f"Summary: Modified {total_files_modified} files, added {total_docstrings_added} docstrings")

        return 0

    except Exception as error:
        print(f"Error: {error}")
        return 1


def run_pre_commit_hook(config_path: str = None, verbose: bool = False) -> int:
    """Run the pre-commit hook on staged files.

    Args:
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
        git_detector = GitModificationDetector()
        ast_parser = PythonASTParser(
            include_private=False,
            update_incomplete=config.processing.update_incomplete_docstrings
        )
        processor = DocstringProcessor(config)

        # Get staged files and their modifications
        file_modifications = git_detector.get_file_modifications()
        
        if not file_modifications:
            if verbose:
                print("No staged Python files found")
            return 0

        total_files_modified = 0
        files_processed = []

        for file_path, modified_lines in file_modifications.items():
            try:
                if verbose:
                    print(f"Checking {file_path} ({len(modified_lines)} modified lines)")

                # Get elements that are new or modified and need docstrings
                elements_needing_docs = ast_parser.get_modified_elements(file_path, modified_lines)
                
                if elements_needing_docs:
                    if verbose:
                        print(f"Found {len(elements_needing_docs)} elements needing docstrings")
                    
                    # Process the file
                    was_modified = processor.process_file(file_path, elements_needing_docs)
                    
                    if was_modified:
                        total_files_modified += 1
                        files_processed.append(file_path)
                        
                        # Validate syntax after modification
                        if not processor.validate_insertion(file_path):
                            print(f"Error: Syntax validation failed for {file_path}")
                            if config.backup_files:
                                processor.restore_backup(file_path)
                            return 1
                        
                        # Re-add the modified file to staging
                        if not git_detector.add_file_to_staging(file_path):
                            print(f"Warning: Could not re-add {file_path} to staging")
                else:
                    if verbose:
                        print(f"No docstrings needed for modified elements in {file_path}")

            except Exception as error:
                print(f"Error processing {file_path}: {error}")
                continue

        # Clean up backups if processing was successful
        if not config.backup_files:
            processor.cleanup_backups(files_processed)

        # Summary
        if verbose or total_files_modified > 0:
            print(f"Pre-commit hook: Modified {total_files_modified} files with generated docstrings")

        return 0

    except Exception as error:
        print(f"Pre-commit hook error: {error}")
        return 1


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Generate docstrings for Python functions and classes using LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run as pre-commit hook (processes staged files)
  llm-docs-hook

  # Process specific files
  llm-docs-hook --files module.py utils.py

  # Create sample configuration
  llm-docs-hook --create-config

  # Run with verbose output
  llm-docs-hook --verbose
        """
    )

    parser.add_argument(
        '--files',
        nargs='*',
        help='Specific Python files to process (instead of staged files)'
    )
    
    parser.add_argument(
        '--config',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--create-config',
        action='store_true',
        help='Create a sample configuration file and exit'
    )

    args = parser.parse_args()

    if args.create_config:
        create_sample_config_file()
        print("Sample configuration created: .docstring_config.yaml")
        print("Edit this file to customize your settings, then set your LLM API key in .env")
        sys.exit(0)

    # Determine mode
    if args.files:
        # Process specific files
        exit_code = process_files(args.files, args.config, args.verbose)
    else:
        # Run as pre-commit hook
        exit_code = run_pre_commit_hook(args.config, args.verbose)

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
