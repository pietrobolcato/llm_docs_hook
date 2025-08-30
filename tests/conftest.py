"""Test configuration and fixtures for the llm_docs_hook package."""

import tempfile
from pathlib import Path


class BaseTestCase:
    """Base test case with common setup and teardown methods."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_temp_file(self, content: str, suffix: str = ".py") -> Path:
        """Create a temporary file with the given content.

        Args:
            content (str): File content.
            suffix (str): File extension. Optional, defaults to ".py".

        Returns:
            Path: Path to the created temporary file.
        """
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
        temp_file.write(content)
        temp_file.close()
        return Path(temp_file.name)
