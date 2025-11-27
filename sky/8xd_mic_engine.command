#!/bin/bash
set -euo pipefail

DESKTOP="${HOME}/Desktop"
SKY_ROOT="${DESKTOP}/sky"
VENV_DIR="${SKY_ROOT}/.venv_8xd"
ENGINE_PY="${SKY_ROOT}/8xd_numpy_audiophile_engine.py"

echo "---------------------------------------------------"
echo "   MINECRAFT 8XD — GROUNDED MIC ENGINE LAUNCHER"
echo "---------------------------------------------------"
echo "Sky root : ${SKY_ROOT}"
echo "Venv     : ${VENV_DIR}"
echo "Engine   : ${ENGINE_PY}"
echo "State    : grounded / focused / present / stable"
echo "---------------------------------------------------"

mkdir -p "${SKY_ROOT}"
cd "${SKY_ROOT}"

if [ ! -d "${VENV_DIR}" ]; then
  echo "Creating local Python venv (.venv_8xd)..."
  python3 -m venv "${VENV_DIR}"
  source "${VENV_DIR}/bin/activate"
  python -m pip install --upgrade pip
  python -m pip install numpy sounddevice
else
  echo "Using existing venv (.venv_8xd)..."
  # shellcheck disable=SC1090
  source "${VENV_DIR}/bin/activate"
fi

if [ ! -f "${ENGINE_PY}" ]; then
  echo "Engine script missing at ${ENGINE_PY}"
  echo "Run create_project.command again to regenerate."
  exit 1
fi

echo
echo "---------------------------------------------------"
echo "  Starting 8XD Grounded NumPy Mic Engine now..."
echo "---------------------------------------------------"
echo "Mic → vec14 / vec8 → ${SKY_ROOT}/bpm_sync.json"
echo "Ctrl+C to stop."
echo "---------------------------------------------------"
echo

exec python "${ENGINE_PY}"
