# Using LLM Docs Hook in Your Repository

## Quick Setup

1. **Add to your `.pre-commit-config.yaml`:**

```yaml
repos:
  - repo: https://github.com/yourusername/llm-docs-hook
    rev: v0.1.0  # Use the latest version
    hooks:
      - id: llm-docs-hook
```

2. **Set up your API key:**

Create a `.env` file in your project root:
```bash
OPENAI_API_KEY=your_openai_api_key_here
# or
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

3. **Install pre-commit (if not already installed):**

```bash
pip install pre-commit
pre-commit install
```

4. **Optional: Create configuration file:**

```bash
# Generate default config
touch .docstring_config.yaml
```

Example `.docstring_config.yaml`:
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

processing:
  skip_existing_docstrings: true
  update_incomplete_docstrings: true  # Update docstrings missing Args/Returns
  verbose: true
```

## How It Works

- **Automatic**: Runs on every `git commit`
- **Smart**: Only processes functions/classes without docstrings (or with incomplete ones if configured)
- **Safe**: Validates syntax after changes
- **Configurable**: Support for multiple LLM providers and docstring styles

## Example

**Before commit:**
```python
def calculate_area(length, width):
    return length * width

class Rectangle:
    def __init__(self, length, width):
        self.length = length
        self.width = width
```

**After commit:**
```python
def calculate_area(length, width):
    """Calculate the area of a rectangle.

    Args:
        length (float): The length of the rectangle.
        width (float): The width of the rectangle.

    Returns:
        float: The area of the rectangle.
    """
    return length * width

class Rectangle:
    """A rectangle with length and width dimensions."""

    def __init__(self, length, width):
        """Initialize a new Rectangle.

        Args:
            length (float): The length of the rectangle.
            width (float): The width of the rectangle.
        """
        self.length = length
        self.width = width
```

## Supported LLM Providers

- **OpenAI**: `openai/gpt-4o-mini`, `openai/gpt-4o`
- **Anthropic**: `anthropic/claude-3-haiku-20240307`
- **Mistral**: `mistral/mistral-small-latest`
- **Google**: `google/gemini-pro`
- **Ollama**: `ollama/llama3` (local)
- And more via [any-llm](https://github.com/mozilla-ai/any-llm)

## Configuration Options

### LLM Settings
- `provider`: LLM provider name
- `model`: Model identifier in "provider/model" format
- `temperature`: Generation randomness (0.0-2.0)
- `max_tokens`: Maximum tokens to generate

### Docstring Settings
- `style`: "google" or "numpy"
- `include_types`: Include type annotations
- `include_examples`: Include usage examples

### Processing Settings
- `skip_existing_docstrings`: Don't modify existing docstrings
- `update_incomplete_docstrings`: Update docstrings lacking Args/Returns
- `verbose`: Show detailed output

## Troubleshooting

### No API Key Error
```
ValueError: No API key found for provider 'openai'
```
**Solution**: Add your API key to `.env` file

### Import Errors
**Solution**: Make sure the package is installed in your environment

### Slow Performance
**Solution**: Use faster models like `gpt-4o-mini` or `claude-3-haiku`
