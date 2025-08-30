# LLM Docs Hook

A pre-commit hook that automatically generates docstrings for Python functions and classes using Large Language Models (LLM). This tool uses the [any-llm](https://github.com/mozilla-ai/any-llm) library to support multiple LLM providers with a unified interface.

## Features

- **Automatic docstring generation** for Python functions and classes
- **Multiple LLM providers** supported (OpenAI, Anthropic, Mistral, Google, Ollama, etc.)
- **Multiple docstring styles** (Google-style and NumPy-style)
- **Parallel processing** for faster generation when processing multiple functions
- **Smart processing** - only processes new/modified functions and classes
- **Configurable** via YAML configuration file
- **Pre-commit integration** for seamless workflow
- **Environment variable support** for API keys
- **Dynamic indentation detection** - adapts to your project's style
- **Backup and validation** to ensure code integrity

## Quick Start

### 1. Installation

```bash
pip install llm-docs-hook
```

### 2. Set up API credentials

Copy the example environment file and add your API key:

```bash
cp env.example .env
# Edit .env and add your LLM provider API key
```

Example `.env` file:
```bash
LLM_DOCS_HOOK_OPENAI_API_KEY=your_openai_api_key_here
# or
LLM_DOCS_HOOK_ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 3. Create configuration (optional)

Generate a sample configuration file:

```bash
llm-docs-hook --create-config
```

This creates `.docstring_config.yaml` with default settings that you can customize.

### 4. Set up pre-commit hook

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pbolcato/llm-docs-hook
    rev: v0.1.0  # Use the latest version
    hooks:
      - id: llm-docs-hook
```

Then install pre-commit:

```bash
pre-commit install
```

### 5. Usage

The hook will automatically run when you commit Python files:

```bash
git add your_file.py
git commit -m "Add new function"
# Hook runs automatically and generates docstrings
```

You can also run it manually on specific files:

```bash
llm-docs-hook --files your_file.py another_file.py
```

## Configuration

### Default Configuration

The tool works out of the box with sensible defaults, but you can customize it by creating a `.docstring_config.yaml` file:

```yaml
llm:
  provider: "openai"
  model: "openai/gpt-4o-mini"
  temperature: 0.1
  max_tokens: 1000

docstring:
  style: "google"  # or "numpy"
  include_types: true
  include_examples: false

files:
  include_patterns:
    - "**/*.py"
  exclude_patterns:
    - "**/test_*.py"
    - "**/tests/**/*.py"
    - "**/*_test.py"
    - "**/conftest.py"

processing:
  skip_existing_docstrings: true
  update_incomplete_docstrings: false
  backup_files: false
  verbose: false
  parallel_count: 5  # Number of parallel LLM requests (1 for sequential)
```

### Supported LLM Providers

Thanks to [any-llm](https://github.com/mozilla-ai/any-llm), this tool supports multiple providers:

- **OpenAI**: `openai/gpt-4o-mini`, `openai/gpt-4o`, etc.
- **Anthropic**: `anthropic/claude-3-haiku-20240307`, `anthropic/claude-3-sonnet-20240229`
- **Mistral**: `mistral/mistral-small-latest`, `mistral/mistral-large-latest`
- **Google**: `google/gemini-pro`, `google/gemini-1.5-flash`
- **Ollama**: `ollama/llama3`, `ollama/codellama`
- **And more!**

### Environment Variables

Set your API key based on your chosen provider:

```bash
# OpenAI
export LLM_DOCS_HOOK_OPENAI_API_KEY="your_key_here"

# Anthropic
export LLM_DOCS_HOOK_ANTHROPIC_API_KEY="your_key_here"

# Mistral
export LLM_DOCS_HOOK_MISTRAL_API_KEY="your_key_here"

# Google
export LLM_DOCS_HOOK_GOOGLE_API_KEY="your_key_here"
```

## How It Works

1. **Git Integration**: Detects staged Python files and their modifications
2. **AST Parsing**: Analyzes Python files to find functions/classes without docstrings
3. **Smart Filtering**: Only processes new or modified functions/classes
4. **LLM Generation**: Uses configured LLM to generate appropriate docstrings
5. **Insertion**: Adds generated docstrings with proper formatting and indentation
6. **Validation**: Ensures the modified code is syntactically valid
7. **Re-staging**: Adds the updated files back to the Git staging area

## Examples

### Before

```python
def calculate_fibonacci(n, memo=None):
    if memo is None:
        memo = {}

    if n in memo:
        return memo[n]

    if n <= 1:
        return n

    memo[n] = calculate_fibonacci(n-1, memo) + calculate_fibonacci(n-2, memo)
    return memo[n]
```

### After (Google style)

```python
def calculate_fibonacci(n, memo=None):
    """Calculate the nth Fibonacci number using memoization.

    Args:
        n (int): The position in the Fibonacci sequence to calculate.
        memo (dict, optional): Memoization dictionary to store previously
            calculated values. Defaults to None.

    Returns:
        int: The nth Fibonacci number.
    """
    if memo is None:
        memo = {}

    if n in memo:
        return memo[n]

    if n <= 1:
        return n

    memo[n] = calculate_fibonacci(n-1, memo) + calculate_fibonacci(n-2, memo)
    return memo[n]
```

## CLI Usage

```bash
# Run as pre-commit hook (processes staged files)
llm-docs-hook

# Process specific files
llm-docs-hook --files module.py utils.py

# Create sample configuration
llm-docs-hook --create-config

# Run with verbose output
llm-docs-hook --verbose

# Use custom config file
llm-docs-hook --config my_config.yaml
```

## Advanced Usage

### Parallel Processing

For better performance when processing multiple functions, the tool supports parallel LLM requests:

```yaml
processing:
  parallel_count: 5  # Process up to 5 functions simultaneously
  # parallel_count: 1  # Sequential processing (slower but uses fewer API calls)
  # parallel_count: 10 # More aggressive parallelization
```

- **Performance**: 5 functions can be processed ~5x faster than sequential
- **API Limits**: Adjust based on your provider's rate limits
- **Cost**: More parallel requests = higher API usage

### Custom Requirements

Customize the docstring generation with specific requirements:

```yaml
llm:
  provider: "openai"
  model: "openai/gpt-4o-mini"
  custom_requirements: |
    - Use clear, concise language
    - Include parameter units when applicable
    - Add warnings for potential exceptions
    - Reference related functions when helpful
```

### Custom Prompts

The tool generates context-aware prompts based on your configuration and the code structure. The LLM receives:

- Function/class signature
- Surrounding code context
- Parameter information
- Return type annotations (if present)
- Existing decorators
- Custom requirements from configuration

### Integration with CI/CD

You can run the tool in CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Generate docstrings
  run: |
    pip install llm-docs-hook
    llm-docs-hook --files $(git diff --name-only HEAD~1 HEAD | grep '\.py$')
  env:
    LLM_DOCS_HOOK_OPENAI_API_KEY: ${{ secrets.LLM_DOCS_HOOK_OPENAI_API_KEY }}
```

### Custom File Patterns

Configure which files to process:

```yaml
files:
  include_patterns:
    - "src/**/*.py"
    - "lib/**/*.py"
  exclude_patterns:
    - "**/migrations/**"
    - "**/vendor/**"
    - "**/third_party/**"
```

## Troubleshooting

### Common Issues

1. **No API key found**
   - Ensure your `.env` file is in the project root
   - Check that the environment variable name matches your provider
   - Verify the API key is valid

2. **Syntax errors after processing**
   - The tool validates syntax automatically
   - If backup is enabled, files are restored on error
   - Check the verbose output for details

3. **No docstrings generated**
   - Verify the functions/classes don't already have docstrings
   - Check if files match your include/exclude patterns
   - Ensure the LLM API is accessible

### Debug Mode

Run with verbose output to see detailed processing information:

```bash
llm-docs-hook --verbose
```

### Manual Recovery

If something goes wrong and you have backups enabled:

```python
from llm_docs_hook.docstring_processor import DocstringProcessor
from llm_docs_hook.config import DocstringConfig

config = DocstringConfig()
processor = DocstringProcessor(config)
processor.restore_backup(Path("your_file.py"))
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.

## Acknowledgments

- [any-llm](https://github.com/mozilla-ai/any-llm) for the unified LLM interface
- [pre-commit](https://pre-commit.com/) for the hooks framework
