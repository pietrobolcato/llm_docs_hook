#!/bin/bash
set -e

# Load .env file if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "Loaded .env file"
fi

# Run the actual hook
exec llm-docs-hook "$@"
