
# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

#!/usr/bin/env bash
set -euo pipefail

MODELS=${OLLAMA_MODELS:-"llama3:latest"}

echo "[ollama] starting Ollama server..."
ollama serve &
SERVE_PID=$!

# Wait for Ollama API to be ready
echo "[ollama] waiting for API to become ready..."
for i in {1..60}; do
  if command -v curl >/dev/null 2>&1 && curl -sf http://localhost:11434/api/tags >/dev/null; then
    echo "[ollama] API ready."
    break
  fi
  sleep 1
  if ! kill -0 "$SERVE_PID" 2>/dev/null; then
    echo "[ollama] ERROR: Ollama server exited unexpectedly."
    exit 1
  fi
done

# Check and pull missing models
for m in $MODELS; do
  echo "[ollama] checking model: $m"
  if ollama list | grep -q "$m"; then
    echo "[ollama] model '$m' already exists — skipping pull."
  else
    echo "[ollama] pulling model '$m'..."
    ollama pull "$m" || echo "[ollama] WARNING: failed to pull $m (will continue)"
  fi
done

echo "[ollama] all models ready. following server logs..."
wait "$SERVE_PID"
