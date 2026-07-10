#!/bin/bash
# SessionStart hook for Tabilogy (Streamlit + Supabase app).
# Installs Python dependencies into a local virtualenv so that Claude Code on
# the web can run `streamlit`, import the app, and run checks out of the box.
set -euo pipefail

# Only run in Claude Code on the web (remote) sessions.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$PROJECT_DIR"

VENV_DIR="$PROJECT_DIR/.venv"

# Create the virtualenv once. We use a venv (not system pip) because the base
# image ships some Debian-managed packages (e.g. PyJWT) without RECORD files,
# which makes `supabase`'s dependency upgrades fail against system Python.
if [ ! -x "$VENV_DIR/bin/python" ]; then
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install --quiet --upgrade pip
fi

# Install/refresh project dependencies (idempotent; fast on a warm cache).
"$VENV_DIR/bin/pip" install --quiet -r requirements.txt

# Make the venv's python/streamlit the default for the rest of the session.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "export PATH=\"$VENV_DIR/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
fi

echo "Tabilogy dependencies installed into $VENV_DIR"
