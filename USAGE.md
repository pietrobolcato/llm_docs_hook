# Usage Guide

This guide provides detailed instructions for using llm-docs-hook in various scenarios.

## Quick Setup

### 1. Install the package

```bash
pip install llm-docs-hook
```

### 2. Set up API credentials

Create a `.env` file in your project root:

```bash
# For OpenAI (default)
LLM_DOCS_HOOK_OPENAI_API_KEY=your_openai_api_key_here

# Or for other providers
LLM_DOCS_HOOK_ANTHROPIC_API_KEY=your_anthropic_api_key_here
LLM_DOCS_HOOK_MISTRAL_API_KEY=your_mistral_api_key_here
```

### 3. Add to pre-commit

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pbolcato/llm-docs-hook
    rev: v0.1.0
    hooks:
      - id: llm-docs-hook
```

Install and test:

```bash
pre-commit install
pre-commit run llm-docs-hook --all-files
```

## Configuration Examples

### Basic Usage (No Config File)

The tool works out of the box with sensible defaults:
- Provider: OpenAI
- Model: gpt-4o-mini
- Style: Google
- Parallel processing: 5 concurrent requests

### Custom Configuration

Create `.docstring_config.yaml`:

```yaml
llm:
  provider: "openai"
  model: "openai/gpt-4o-mini"
  temperature: 0.1

docstring:
  style: "google"  # or "numpy"
  include_types: true

processing:
  parallel_count: 5
  update_incomplete_docstrings: true
```

## Advanced Scenarios

### Scientific Computing (NumPy Style)

For projects using scientific computing:

```yaml
llm:
  provider: "openai"
  model: "openai/gpt-4o"
  custom_requirements: |
    - Use NumPy-style docstrings with proper sections
    - Include array shapes and dtypes for numpy parameters
    - Reference mathematical concepts when applicable
    - Include algorithm complexity when relevant

docstring:
  style: "numpy"
  include_types: true
  include_examples: true

processing:
  parallel_count: 3  # Slower but more thorough
```

### Large Codebase (Performance Optimized)

For large projects where speed matters:

```yaml
llm:
  provider: "openai"
  model: "openai/gpt-4o-mini"  # Fast and cost-effective
  temperature: 0.0  # Deterministic
  max_tokens: 800   # Shorter, focused docstrings

processing:
  parallel_count: 10  # Aggressive parallelization
  skip_existing_docstrings: true
  backup_files: false
  verbose: false

files:
  exclude_patterns:
    - "**/test_*.py"
    - "**/migrations/**"
    - "**/vendor/**"
```

### Enterprise/Team Settings

For team consistency and safety:

```yaml
llm:
  provider: "anthropic"  # Often preferred in enterprise
  model: "anthropic/claude-3-sonnet-20240229"
  custom_requirements: |
    - Follow our company documentation standards
    - Include security considerations when applicable
    - Use professional, clear language
    - Reference internal APIs and conventions

processing:
  parallel_count: 3      # Conservative for rate limits
  backup_files: true     # Safety first
  verbose: true          # Detailed logging
  update_incomplete_docstrings: true
```

## Provider-Specific Setup

### OpenAI (Default)

```bash
# .env
LLM_DOCS_HOOK_OPENAI_API_KEY=sk-...
```

```yaml
# .docstring_config.yaml
llm:
  provider: "openai"
  model: "openai/gpt-4o-mini"  # or gpt-4o for better quality
```

### Anthropic Claude

```bash
# .env
LLM_DOCS_HOOK_ANTHROPIC_API_KEY=sk-ant-...
```

```yaml
# .docstring_config.yaml
llm:
  provider: "anthropic"
  model: "anthropic/claude-3-haiku-20240307"  # Fast
  # model: "anthropic/claude-3-sonnet-20240229"  # Balanced
  # model: "anthropic/claude-3-opus-20240229"    # Best quality
```

### Local Models (Ollama)

First, install and run Ollama with a model:

```bash
ollama pull codellama
ollama serve
```

```yaml
# .docstring_config.yaml
llm:
  provider: "ollama"
  model: "ollama/codellama"
  # model: "ollama/llama3"
```

## CLI Usage Examples

### Process Specific Files

```bash
# Single file
llm-docs-hook src/main.py

# Multiple files
llm-docs-hook src/utils.py src/models.py

# All Python files in directory
llm-docs-hook src/**/*.py
```

### Configuration Management

```bash
# Create sample configuration
llm-docs-hook --create-config

# Use custom config file
llm-docs-hook --config team_config.yaml

# Verbose output for debugging
llm-docs-hook --verbose
```

### Integration Examples

#### GitHub Actions

```yaml
name: Generate Docstrings
on: [push, pull_request]

jobs:
  docstrings:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install llm-docs-hook

      - name: Generate docstrings
        run: llm-docs-hook --files $(find . -name "*.py" -not -path "./tests/*")
        env:
          LLM_DOCS_HOOK_OPENAI_API_KEY: ${{ secrets.LLM_DOCS_HOOK_OPENAI_API_KEY }}

      - name: Commit changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add -A
          git diff --staged --quiet || git commit -m "Auto-generate docstrings"
          git push
```

#### Pre-commit CI

```yaml
# .pre-commit-config.yaml
ci:
  autofix_commit_msg: 'fix: auto-generate docstrings [pre-commit.ci]'

repos:
  - repo: https://github.com/pbolcato/llm-docs-hook
    rev: v0.1.0
    hooks:
      - id: llm-docs-hook
        # Only run on Python files in src/
        files: ^src/.*\.py$
```

## Performance Tuning

### Parallel Processing

Adjust `parallel_count` based on:

```yaml
processing:
  parallel_count: 1   # Sequential (slowest, least API usage)
  parallel_count: 3   # Conservative (good for most cases)
  parallel_count: 5   # Default (balanced)
  parallel_count: 10  # Aggressive (fastest, highest API usage)
  parallel_count: 20  # Maximum (only for high rate limits)
```

**Guidelines:**
- Start with 5 (default)
- Increase if you have high rate limits
- Decrease if you hit rate limits
- Use 1 for debugging or very limited APIs

### Model Selection

**Speed vs Quality:**

```yaml
# Fastest, cheapest
llm:
  model: "openai/gpt-4o-mini"

# Balanced
llm:
  model: "anthropic/claude-3-haiku-20240307"

# Best quality, slower
llm:
  model: "openai/gpt-4o"
  model: "anthropic/claude-3-sonnet-20240229"
```

## Troubleshooting

### Common Issues

**"No API key found"**
- Check your `.env` file exists and has the right variable name
- Ensure `.env` is in your project root, not in subdirectories

**"Rate limit exceeded"**
- Reduce `parallel_count` in configuration
- Switch to a faster/cheaper model
- Add delays between requests (model-dependent)

**"Syntax errors after processing"**
- Enable `backup_files: true` for safety
- Check `verbose: true` output for details
- Verify your Python files were valid before processing

**"No docstrings generated"**
- Verify functions don't already have docstrings (unless `update_incomplete_docstrings: true`)
- Check file inclusion/exclusion patterns
- Ensure files are valid Python syntax

### Debug Mode

Enable verbose output to see what's happening:

```yaml
processing:
  verbose: true
  backup_files: true  # Safety during debugging
```

Run with:
```bash
llm-docs-hook --verbose your_file.py
```

This shows:
- Which functions are being processed
- LLM requests and responses
- File modifications
- Any errors or warnings

### Recovery

If something goes wrong:

```python
# Manual backup restoration
from pathlib import Path
import shutil

# If backup files exist (.py.backup)
original = Path("your_file.py")
backup = Path("your_file.py.backup")

if backup.exists():
    shutil.copy2(backup, original)
    print(f"Restored {original} from backup")
```

## Best Practices

### 1. Start Small
- Test on a few files first
- Use `backup_files: true` initially
- Start with `parallel_count: 1` for debugging

### 2. Gradual Rollout
- Configure exclude patterns for sensitive files
- Process one module at a time
- Review generated docstrings before committing

### 3. Team Consistency
- Share configuration files in your repository
- Use consistent custom requirements
- Set up pre-commit for automatic processing

### 4. Cost Management
- Use cheaper models for bulk processing
- Optimize `parallel_count` for your API limits
- Consider exclude patterns for test files

### 5. Quality Control
- Enable `verbose` mode during setup
- Review a sample of generated docstrings
- Use `update_incomplete_docstrings` to improve existing docs
