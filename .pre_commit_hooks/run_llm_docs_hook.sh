#!/bin/bash
set -e

# Load .env file if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Correctly loaded .env file for LLM docstrings hook"
fi

# Run the actual hook
exec llm-docs-hook "$@"
