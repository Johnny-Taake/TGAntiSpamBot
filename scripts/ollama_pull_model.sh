#!/usr/bin/env bash

# USE WITH: ./scripts/ollama_pull_model.sh qwen2.5:7b-instruct
# Or the model you want to install

set -euo pipefail

MODEL="${1:-qwen2.5:7b-instruct}"

# Ensure service is up
docker compose up -d ollama

echo "Waiting for Ollama on host port 11434..."
for i in $(seq 1 60); do
  if curl -fsS "http://localhost:11434/api/tags" >/dev/null 2>&1; then
    echo "Ollama is up."
    break
  fi
  sleep 1
  if [ "$i" -eq 60 ]; then
    echo "Ollama did not become ready in time."
    docker compose logs --tail=200 ollama
    exit 1
  fi
done

echo "Pulling model inside container: ${MODEL}"
docker compose exec -T ollama ollama pull "${MODEL}"

echo "Done. Installed models:"
docker compose exec -T ollama ollama list
