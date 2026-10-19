#!/usr/bin/env bash
set -euo pipefail

# Start the development stack (Vite HMR + uvicorn --reload).
# --profile must be a docker-compose flag (before `up`), not an `up` flag.
# Examples:
#   ./scripts/dev-up.sh -d
#   ./scripts/dev-up.sh --build
#   ./scripts/dev-up.sh --profile seed
#   ./scripts/dev-up.sh --build --profile seed --profile ollama
#   ENABLE_OLLAMA_API=true ./scripts/dev-up.sh --profile ollama

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ENV_FILE="${ENV_FILE:-.env.dev}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing ${ENV_FILE}. Create it from the template:" >&2
  echo "  cp .env.dev.example .env.dev" >&2
  echo "Then set WEBUI_SECRET_KEY and OPENAI_API_KEY." >&2
  exit 1
fi

if ! grep -qE '^WEBUI_SECRET_KEY=.+' "$ENV_FILE" 2>/dev/null; then
  echo "Warning: WEBUI_SECRET_KEY looks empty in ${ENV_FILE}." >&2
  echo "Generate one: python3 -c \"import secrets; print(secrets.token_urlsafe(48))\"" >&2
fi

COMPOSE_ARGS=()
UP_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      if [[ $# -lt 2 ]]; then
        echo "Error: --profile requires a value (seed|ollama)." >&2
        exit 1
      fi
      COMPOSE_ARGS+=(--profile "$2")
      shift 2
      ;;
    --profile=*)
      COMPOSE_ARGS+=("$1")
      shift
      ;;
    *)
      UP_ARGS+=("$1")
      shift
      ;;
  esac
done

exec docker compose -f docker-compose.dev.yaml --env-file "$ENV_FILE" \
  "${COMPOSE_ARGS[@]}" up "${UP_ARGS[@]}"
