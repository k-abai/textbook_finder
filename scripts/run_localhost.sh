#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-5173}"

if [ -d "$ROOT_DIR/frontend/node_modules" ]; then
  echo "Starting Vite dev server on port $PORT..."
  cd "$ROOT_DIR/frontend"
  npm run dev -- --host 0.0.0.0 --port "$PORT"
else
  echo "frontend/node_modules not found. Starting dependency-free fallback site on port $PORT..."
  cd "$ROOT_DIR/offline_site"
  python -m http.server "$PORT"
fi
