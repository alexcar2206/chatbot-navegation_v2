#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Pull the default Ollama models into the running ollama container.
# Same list as ollama-init (OLLAMA_PULL_MODELS), for manual / recovery use.
# ---------------------------------------------------------------------------

readonly CONTAINER="${OLLAMA_CONTAINER:-ollama}"
readonly MODELS_RAW="${OLLAMA_PULL_MODELS:-llama3.2:3b}"
MODELS=$(echo "$MODELS_RAW" | tr ',' ' ')

echo "Pulling default models into '${CONTAINER}': ${MODELS}"

if ! docker exec "$CONTAINER" ollama list >/dev/null 2>&1; then
  echo "Container '${CONTAINER}' is not ready (ollama list failed)." >&2
  exit 1
fi

for model in $MODELS; do
  [ -z "$model" ] && continue
  echo "=== ollama pull ${model} ==="
  docker exec "$CONTAINER" ollama pull "$model"
done

echo "Done. Installed models:"
docker exec "$CONTAINER" ollama list
