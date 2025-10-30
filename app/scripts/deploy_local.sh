#!/usr/bin/env bash
set -euo pipefail

# Simple local deploy script using docker-compose
# Usage: ./scripts/deploy_local.sh [up|down|build]
CMD=${1:-up}
APP_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$APP_DIR"

case "$CMD" in
  build)
    docker-compose build --pull
    ;;
  up)
    docker-compose up -d --build
    ;;
  down)
    docker-compose down
    ;;
  *)
    echo "Usage: $0 [up|down|build]"
    exit 1
    ;;
esac

echo "Done: $CMD"
