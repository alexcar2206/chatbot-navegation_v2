#!/usr/bin/env bash
set -euo pipefail

# Start the production / demo stack (docker-compose.yaml).
# --profile must be a docker-compose flag (before `up`), not an `up` flag.
# Examples:
#   ./scripts/prod-up.sh -d
#   ./scripts/prod-up.sh --build
#   ./scripts/prod-up.sh --profile seed
#   ./scripts/prod-up.sh --build --profile seed --profile ollama
#   ENABLE_OLLAMA_API=true ./scripts/prod-up.sh --profile ollama

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ENV_FILE="${ENV_FILE:-.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing ${ENV_FILE}. Create it from the template:" >&2
  echo "  cp .env.example .env" >&2
  exit 1
fi

# Refuse to start with empty secrets (WEBUI_SECRET_KEY ships blank in the template).
for var in WEBUI_SECRET_KEY WEBUI_ADMIN_PASSWORD; do
  if ! grep -qE "^${var}=.+" "$ENV_FILE"; then
    echo "Error: ${var} is empty in ${ENV_FILE}." >&2
    if [[ "$var" == "WEBUI_SECRET_KEY" ]]; then
      echo "Generate one: python3 -c \"import secrets; print(secrets.token_urlsafe(48))\"" >&2
    fi
    exit 1
  fi
done

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

exec docker compose -f docker-compose.yaml --env-file "$ENV_FILE" \
  "${COMPOSE_ARGS[@]}" up "${UP_ARGS[@]}"
