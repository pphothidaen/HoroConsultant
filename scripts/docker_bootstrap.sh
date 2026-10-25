#!/usr/bin/env bash
# =============================================================
# scripts/docker_bootstrap.sh
# One-shot Docker deployment bootstrap for Ubuntu environments
# =============================================================
# Usage:
#   chmod +x scripts/docker_bootstrap.sh
#   ./scripts/docker_bootstrap.sh [--with-gpu]
# =============================================================

set -euo pipefail

WITH_GPU=false
for arg in "$@"; do
  [[ "$arg" == "--with-gpu" ]] && WITH_GPU=true
done

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "${GREEN}[bootstrap]${NC} $*"; }
warn() { echo -e "${YELLOW}[warning]${NC}  $*"; }
err()  { echo -e "${RED}[error]${NC}    $*" >&2; exit 1; }

log "=== Computational Metaphysics Engine — Docker Bootstrap ==="

# 1. Check .env
if [[ ! -f .env ]]; then
  cp .env.example .env
  warn ".env not found — copied from .env.example"
  warn "⚠️  Edit .env and set GOOGLE_AI_STUDIO_API_KEY before continuing!"
  exit 1
fi

if grep -q "REPLACE_WITH" .env; then
  warn "⚠️  .env still contains placeholder values."
  warn "    Edit .env and set your GOOGLE_AI_STUDIO_API_KEY."
  warn "    Continuing anyway (AI interpretation endpoints will fallback to Ollama)…"
fi

# 2. Check docker / docker compose
command -v docker      &>/dev/null || err "Docker not installed. See https://docs.docker.com/get-docker/"
command -v docker compose &>/dev/null 2>&1 || docker compose version &>/dev/null || \
  err "docker compose not available. Install Docker Desktop or the compose plugin."

# 3. Create model directory
mkdir -p project/models project/data/mlx_finetune project/data/vector_store

# 4. Check for GGUF
GGUF_PATH="project/models/qwen2.5-bazi.gguf"
if [[ -f "$GGUF_PATH" ]]; then
  log "Found GGUF model: $GGUF_PATH"
else
  warn "GGUF not found at $GGUF_PATH"
  warn "  → Ollama will pull qwen2.5:7b (base model) as fallback"
  warn "  → Place your fine-tuned GGUF there for domain-specific inference"
fi

# 5. Enable GPU in docker-compose.yml if requested
if $WITH_GPU; then
  log "GPU mode requested — enabling NVIDIA device in docker-compose.yml"
  sed -i 's|#   - driver: nvidia|- - driver: nvidia|' docker-compose.yml || true
  sed -i 's|#     count: all|    count: all|'          docker-compose.yml || true
  sed -i 's|#     capabilities: \[gpu\]|    capabilities: [gpu]|' docker-compose.yml || true
fi

# 6. Build images
log "Building Docker images…"
docker compose build --no-cache

# 7. Start services
log "Starting services…"
docker compose up -d

# 8. Wait for health
log "Waiting for services to become healthy…"
RETRIES=20; WAIT=5
for i in $(seq 1 $RETRIES); do
  APP_STATUS=$(docker inspect --format='{{.State.Health.Status}}' bazi-engine    2>/dev/null || echo "starting")
  OLL_STATUS=$(docker inspect --format='{{.State.Health.Status}}' bazi-ollama    2>/dev/null || echo "starting")
  log "  [${i}/${RETRIES}] app=${APP_STATUS} ollama=${OLL_STATUS}"
  if [[ "$APP_STATUS" == "healthy" && "$OLL_STATUS" == "healthy" ]]; then
    break
  fi
  sleep $WAIT
done

# 9. Run unit tests inside container
log "Running unit tests inside container…"
docker compose exec app python3 -m pytest tests/ -v --tb=short || warn "Some tests failed — check logs"

# 10. Load model
log "Triggering model loader…"
docker compose run --rm model-loader || warn "Model loader had issues — check GGUF path"

# 11. Final status
echo ""
log "=== Deployment Complete ==="
echo ""
echo "  App API:    http://localhost:${APP_PORT:-8000}"
echo "  API Docs:   http://localhost:${APP_PORT:-8000}/docs"
echo "  Ollama:     http://localhost:${OLLAMA_PORT:-11434}"
echo ""
echo "  Quick test:"
echo "    curl http://localhost:8000/health"
echo "    curl -X POST http://localhost:8000/api/v1/bazi/calculate \\"
echo "         -H 'Content-Type: application/json' \\"
echo "         -d '{\"birth_datetime\":\"1990-05-15 14:30:00\",\"longitude\":100.493,\"utc_offset_hours\":7.0}'"
echo ""
log "Done! 🎉"
