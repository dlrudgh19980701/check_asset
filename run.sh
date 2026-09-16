#!/usr/bin/env bash
# Run the app loading environment variables from a local `.env` file (if present).
# Usage: ./run.sh

set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$DIR/.env"
if [ -f "$ENV_FILE" ]; then
  # export non-comment, non-empty lines of KEY=VALUE
  while IFS= read -r line || [ -n "$line" ]; do
    # skip comments and empty lines
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    key="${line%%=*}"
    value="${line#*=}"
    # strip surrounding single/double quotes
    value="${value%"}"; value="${value#"}"
    value="${value%\'}"; value="${value#\'}"
    export "$key=$value"
  done < "$ENV_FILE"
fi

python3 app.py
