#!/usr/bin/env bash
set -euo pipefail

# Stop the development stack (includes profile services seed/ollama if running).
# Does not remove volumes (pass -v to wipe data).
#   ./scripts/dev-down.sh
#   ./scripts/dev-down.sh -v

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ENV_FILE="${ENV_FILE:-.env.dev}"
COMPOSE=(docker compose -f docker-compose.dev.yaml --profile seed --profile ollama)

if [[ -f "$ENV_FILE" ]]; then
  COMPOSE+=(--env-file "$ENV_FILE")
fi

exec "${COMPOSE[@]}" down "$@"
