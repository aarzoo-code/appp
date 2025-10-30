#!/usr/bin/env bash
set -euo pipefail

echo "Starting entrypoint: running migrations and launching app"

RETRIES=12
COUNT=0
until alembic -c backend/alembic.ini upgrade head; do
  COUNT=$((COUNT+1))
  if [ "$COUNT" -ge "$RETRIES" ]; then
    echo "Failed to run alembic migrations after $RETRIES attempts" >&2
    exit 1
  fi
  echo "Alembic upgrade failed or DB not ready, retrying in 3s (attempt $COUNT/$RETRIES)..."
  sleep 3
done

echo "Migrations applied. Starting Flask app..."
exec python -m backend.app
