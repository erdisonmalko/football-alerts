#!/bin/sh
set -e

# SERVICE_TYPE is set per-service in railway.toml:
#   api        -> run migrations then start uvicorn
#   worker     -> start celery worker
#   beat       -> start celery beat

case "$SERVICE_TYPE" in
  api)
    echo "Running database migrations..."
    alembic upgrade head
    echo "Starting API server..."
    exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 2
    ;;
  worker)
    echo "Starting Celery worker..."
    exec celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2
    ;;
  beat)
    echo "Starting Celery beat..."
    exec celery -A app.tasks.celery_app beat --loglevel=info
    ;;
  *)
    echo "ERROR: SERVICE_TYPE must be api, worker, or beat. Got: '$SERVICE_TYPE'"
    exit 1
    ;;
esac