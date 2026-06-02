#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h postgres -p 5432 -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-timesheet_db}"; do
  sleep 2
done

echo "Running migrations..."
alembic upgrade head

echo "Starting API..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
