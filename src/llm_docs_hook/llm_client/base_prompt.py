"""Base prompt for LLM docstring generation."""

base_prompt = """{task_description}:

```python
{context}
```{existing_note}

Requirements:
{requirements}

- Only return the docstring content (without triple quotes)
- The docstring should start immediately after the {element.element_type} definition
- Follow Python documentation best practices

Return only the docstring content, nothing else."""