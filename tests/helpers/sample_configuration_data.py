"""Common configuration data for tests."""

SAMPLE_CONFIG_MINIMAL = {"llm": {"provider": "openai", "model": "openai/gpt-4o-mini"}}

SAMPLE_CONFIG_FULL = {
    "llm": {
        "provider": "anthropic",
        "model": "anthropic/claude-3-haiku-20240307",
        "temperature": 0.2,
        "max_tokens": 1500,
    },
    "docstring": {"style": "numpy", "include_types": True, "include_examples": True},
    "files": {
        "include_patterns": ["**/*.py", "**/*.js"],
        "exclude_patterns": ["**/test_*.py", "**/__pycache__/**"],
    },
    "processing": {
        "skip_existing_docstrings": False,
        "backup_files": True,
        "verbose": True,
        "parallel_count": 3,
    },
}

SAMPLE_CONFIG_INVALID = {
    "llm": {"provider": "invalid_provider", "model": "invalid-model-format"}
}
