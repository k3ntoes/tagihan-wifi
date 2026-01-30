#!/usr/bin/env sh
set -e

DB_PATH="${DATABASE_PATH:-./data/tagihan-wifi.db}"

if [ -f "$DB_PATH" ]; then
  echo "Database already exists at $DB_PATH. Skipping setup_db.py."
else
  echo "Database not found at $DB_PATH. Running setup_db.py..."
  # Default to non-interactive during container lifecycle unless explicitly disabled
  if [ -z "${SETUP_DB_NON_INTERACTIVE:-}" ]; then
    export SETUP_DB_NON_INTERACTIVE=1
  fi
  uv run python setup_db.py
fi

exec "$@"
