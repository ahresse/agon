#!/usr/bin/env bash
# One-command setup + run for Agon.
#
# Creates a virtualenv (if missing), installs the app, seeds the database on
# first run, and starts the server. Re-running is fast: it reuses the venv and
# skips seeding once the database exists.
#
# Usage:
#   ./run.sh                 # setup + run on 127.0.0.1:8000
#   HOST=0.0.0.0 PORT=9000 ./run.sh
#   AGON_USE_LOCAL_RUNNER=1 ./run.sh   # dev fallback without LXD (non-isolating)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${SCRIPT_DIR}/app"
VENV_DIR="${SCRIPT_DIR}/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

cd "${APP_DIR}"

# 1. Virtualenv
if [ ! -x "${VENV_DIR}/bin/python" ]; then
  echo "==> Creating virtualenv at ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi
VENV_PY="${VENV_DIR}/bin/python"

# 2. Dependencies (install once; refresh only if pyproject changed)
STAMP="${VENV_DIR}/.agon-installed"
if [ ! -f "${STAMP}" ] || [ "${APP_DIR}/pyproject.toml" -nt "${STAMP}" ]; then
  echo "==> Installing Agon and dependencies"
  "${VENV_PY}" -m pip install --quiet --upgrade pip
  "${VENV_PY}" -m pip install --quiet -e "${APP_DIR}"
  touch "${STAMP}"
fi

# 3. Seed the database on first run (idempotent; skipped once agon.db exists)
DB_PATH="${APP_DIR}/agon.db"
if [ ! -f "${DB_PATH}" ]; then
  echo "==> Seeding database (default users: admin/admin, reviewer/reviewer)"
  "${VENV_PY}" -m src.seed
fi

# 4. Run
echo "==> Agon running at http://${HOST}:${PORT}/  (Ctrl+C to stop)"
exec "${VENV_PY}" -m uvicorn src.api.main:app --host "${HOST}" --port "${PORT}"
