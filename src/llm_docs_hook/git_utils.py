"""Git utilities for detecting modified files and lines."""

import subprocess
from pathlib import Path
from typing import Dict, List, Set


class GitModificationDetector:
    """Detects Git modifications for pre-commit hook processing."""

    def __init__(self, repo_path: Path = None):
        """Initialize the Git modification detector.

        Args:
            repo_path (Path): Path to the Git repository. Optional, defaults to None 
                which uses current directory.
        """
        self.repo_path = repo_path or Path.cwd()

    def get_staged_python_files(self) -> List[Path]:
        """Get list of staged Python files.

        Returns:
            List[Path]: List of staged Python files ready for commit.
        """
        try:
            # Get staged files
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only', '--diff-filter=AM'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            staged_files = []
            for file_path in result.stdout.strip().split('\n'):
                if file_path and file_path.endswith('.py'):
                    full_path = self.repo_path / file_path
                    if full_path.exists():
                        staged_files.append(full_path)
            
            return staged_files
            
        except subprocess.CalledProcessError as error:
            print(f"Error getting staged files: {error}")
            return []

    def get_modified_lines(self, file_path: Path) -> Set[int]:
        """Get line numbers that have been modified in a staged file.

        Args:
            file_path (Path): Path to the file to check for modifications.

        Returns:
            Set[int]: Set of modified line numbers (1-based indexing).
        """
        try:
            # Get relative path from repo root
            relative_path = file_path.relative_to(self.repo_path)
            
            # Get staged diff for the file
            result = subprocess.run(
                ['git', 'diff', '--cached', '-U0', str(relative_path)],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            return self._parse_diff_for_modified_lines(result.stdout)
            
        except (subprocess.CalledProcessError, ValueError) as error:
            print(f"Error getting modified lines for {file_path}: {error}")
            # If we can't determine modified lines, assume the whole file is modified
            return self._get_all_lines(file_path)

    def _parse_diff_for_modified_lines(self, diff_output: str) -> Set[int]:
        """Parse git diff output to extract modified line numbers.

        Args:
            diff_output (str): Raw git diff output.

        Returns:
            Set[int]: Set of modified line numbers.
        """
        modified_lines = set()
        
        for line in diff_output.split('\n'):
            if line.startswith('@@'):
                # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
                try:
                    parts = line.split(' ')
                    new_info = parts[2]  # +new_start,new_count
                    new_start = int(new_info.split(',')[0][1:])  # Remove '+' and get start
                    
                    # For context, we'll mark a range around the change
                    # This is a simplified approach - in practice, you might want more sophisticated logic
                    if ',' in new_info:
                        new_count = int(new_info.split(',')[1])
                    else:
                        new_count = 1
                    
                    # Add the range of modified lines
                    for line_num in range(new_start, new_start + new_count):
                        modified_lines.add(line_num)
                        
                except (IndexError, ValueError):
                    continue
        
        return modified_lines

    def _get_all_lines(self, file_path: Path) -> Set[int]:
        """Get all line numbers in a file as fallback.

        Args:
            file_path (Path): Path to the file.

        Returns:
            Set[int]: Set of all line numbers in the file.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            return set(range(1, len(lines) + 1))
        except Exception:
            return set()

    def is_new_file(self, file_path: Path) -> bool:
        """Check if a file is newly added (not tracked by git).

        Args:
            file_path (Path): Path to the file to check.

        Returns:
            bool: True if the file is newly added, False otherwise.
        """
        try:
            relative_path = file_path.relative_to(self.repo_path)
            
            # Check if file is in git index
            result = subprocess.run(
                ['git', 'ls-files', '--error-unmatch', str(relative_path)],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            # If command succeeds, file is tracked
            return result.returncode != 0
            
        except (subprocess.CalledProcessError, ValueError):
            return True  # Assume new if we can't determine

    def add_file_to_staging(self, file_path: Path) -> bool:
        """Add a modified file back to the staging area.

        Args:
            file_path (Path): Path to the file to add to staging.

        Returns:
            bool: True if file was successfully added, False otherwise.
        """
        try:
            relative_path = file_path.relative_to(self.repo_path)
            
            subprocess.run(
                ['git', 'add', str(relative_path)],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            return True
            
        except (subprocess.CalledProcessError, ValueError) as error:
            print(f"Error adding {file_path} to staging: {error}")
            return False

    def get_file_modifications(self) -> Dict[Path, Set[int]]:
        """Get all staged Python files and their modified lines.

        Returns:
            Dict[Path, Set[int]]: Dictionary mapping file paths to sets of modified line numbers.
        """
        modifications = {}
        staged_files = self.get_staged_python_files()
        
        for file_path in staged_files:
            if self.is_new_file(file_path):
                # For new files, consider all lines as modified
                modifications[file_path] = self._get_all_lines(file_path)
            else:
                # For existing files, get actually modified lines
                modifications[file_path] = self.get_modified_lines(file_path)
        
        return modifications
