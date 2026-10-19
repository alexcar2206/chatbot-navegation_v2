#!/usr/bin/env bash
# Hot-fix only: patches a running open-webui container's built index.html / custom.css.
# Canonical branding is src/app.html + static/*/custom.css (rebuild the image for permanence).
# Palette: #0b4f6c / #e8f1f5 / #042a3a
set -euo pipefail
CONTAINER="${CONTAINER:-open-webui}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="/tmp/owui-live-patch-$$"
LOG="$REPO_ROOT/scripts/_live_patch_verify.log"
mkdir -p "$TMP"
exec > >(tee "$LOG") 2>&1
echo "=== live splash/theme patch (hot-fix; not source of truth) ==="
docker exec "$CONTAINER" sh -c 'grep -rl "splash-screen\|theme-color" /app/build --include="*.html" 2>/dev/null | head -20' || true
docker cp "$CONTAINER:/app/build/index.html" "$TMP/index.html"
python3 "$REPO_ROOT/scripts/patch_owui_live_theme.py" "$TMP/index.html"
docker cp "$TMP/index.html" "$CONTAINER:/app/build/index.html"
SPLASH=$'/* Brand splash overrides (Chatbot Navegation / Miño-Sil) */\n#splash-screen { background: #e8f1f5 !important; }\nhtml.dark #splash-screen { background: #042a3a !important; }\n'
for f in "$REPO_ROOT/static/static/custom.css" "$REPO_ROOT/backend/open_webui/static/custom.css"; do
  mkdir -p "$(dirname "$f")"
  if [ ! -f "$f" ] || ! grep -q "Brand splash overrides" "$f" 2>/dev/null; then
    printf '%s\n' "$SPLASH" > "$f"
  elif ! grep -q "#e8f1f5" "$f" 2>/dev/null; then
    printf '%s\n' "$SPLASH" > "$f"
  fi
done
for cpath in /app/backend/open_webui/static/custom.css /app/build/static/custom.css; do
  docker exec "$CONTAINER" sh -c "mkdir -p \$(dirname '$cpath') && touch '$cpath'"
  docker cp "$REPO_ROOT/backend/open_webui/static/custom.css" "$CONTAINER:$cpath"
done
docker exec "$CONTAINER" sh -c 'grep -E "#0b4f6c|#e8f1f5|#042a3a" /app/build/index.html | head -20' || true
docker exec "$CONTAINER" sh -c 'grep -E "#e8f1f5|#042a3a" /app/backend/open_webui/static/custom.css /app/build/static/custom.css' || true
curl -sI http://localhost:3000/static/custom.css | head -5 || true
curl -s http://localhost:3000/static/custom.css | head -15 || true
rm -rf "$TMP"
