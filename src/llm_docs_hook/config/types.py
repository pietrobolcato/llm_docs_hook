"""Configuration management for LLM docs hook using Pydantic models.

This module provides Pydantic models for type-safe configuration management
and YAML file loading with validation.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator


class LLMConfig(BaseModel):
    """LLM provider and model configuration."""
    
    provider: str = Field(
        default="openai",
        description="LLM provider name (e.g., 'openai', 'anthropic', 'mistral')"
    )
    model: str = Field(
        default="openai/gpt-4o-mini",
        description="Model identifier in 'provider/model' format"
    )
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Generation temperature (0.0 to 2.0)"
    )
    max_tokens: int = Field(
        default=1000,
        gt=0,
        description="Maximum tokens to generate"
    )
    custom_requirements: Optional[str] = Field(
        default=None,
        description="Custom requirements for docstring generation (multiline YAML string)"
    )

    @validator("model")
    def validate_model_format(cls, model_value: str) -> str:
        """Validate that model follows 'provider/model' format.

        Args:
            model_value (str): The model string to validate.

        Returns:
            str: The validated model string.

        Raises:
            ValueError: If model format is invalid.
        """
        if "/" not in model_value:
            raise ValueError("Model must be in format 'provider/model' (e.g., 'openai/gpt-4o-mini')")
        return model_value


class DocstringConfig(BaseModel):
    """Docstring generation preferences."""
    
    style: Literal["google", "numpy"] = Field(
        default="google",
        description="Docstring style format"
    )
    include_types: bool = Field(
        default=True,
        description="Include type annotations in docstrings"
    )
    include_examples: bool = Field(
        default=False,
        description="Include usage examples in docstrings"
    )


class FileConfig(BaseModel):
    """File processing patterns."""
    
    include_patterns: List[str] = Field(
        default=["**/*.py"],
        description="Glob patterns for files to include"
    )
    exclude_patterns: List[str] = Field(
        default=[
            "**/test_*.py",
            "**/tests/**/*.py",
            "**/*_test.py",
            "**/conftest.py",
            "**/__pycache__/**",
            "**/venv/**",
            "**/env/**",
            "**/.venv/**",
        ],
        description="Glob patterns for files to exclude"
    )


class ProcessingConfig(BaseModel):
    """Processing behavior configuration."""
    
    skip_existing_docstrings: bool = Field(
        default=True,
        description="Skip functions/classes that already have complete docstrings"
    )
    update_incomplete_docstrings: bool = Field(
        default=False,
        description="Update docstrings that lack Args/Returns sections"
    )
    backup_files: bool = Field(
        default=False,
        description="Create backup files before modification"
    )
    verbose: bool = Field(
        default=False,
        description="Enable verbose output"
    )
    parallel_count: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of parallel LLM requests (1 for sequential processing)"
    )


class Config(BaseModel):
    """Main configuration for LLM docs hook."""
    
    llm: LLMConfig = Field(
        default_factory=LLMConfig,
        description="LLM provider and model configuration"
    )
    docstring: DocstringConfig = Field(
        default_factory=DocstringConfig,
        description="Docstring generation preferences"
    )
    files: FileConfig = Field(
        default_factory=FileConfig,
        description="File processing patterns"
    )
    processing: ProcessingConfig = Field(
        default_factory=ProcessingConfig,
        description="Processing behavior configuration"
    )

    def get_api_key(self) -> Optional[str]:
        """Get the API key for the configured LLM provider from environment variables.

        Returns:
            Optional[str]: The API key if found in environment variables, None otherwise.
        """
        # Load environment variables
        load_dotenv()
        
        provider = self.llm.provider.upper()
        
        # Common API key environment variable names
        possible_keys = [
            f"{provider}_API_KEY",
            f"{provider}API_KEY",
            "OPENAI_API_KEY",  # fallback for OpenAI-compatible providers
            "API_KEY",
        ]
        
        for key in possible_keys:
            api_key = os.getenv(key)
            if api_key:
                return api_key
                
        return None
