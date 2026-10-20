#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
. "${PROJECT_DIR}/ollama_local.sh"
PYTHON=""
for candidate in "${PROJECT_DIR}/.venv/bin/python" "${PROJECT_DIR}/.venv312/bin/python"; do
  if [ -x "${candidate}" ]; then
    PYTHON="${candidate}"
    break
  fi
done

if [ -z "${PYTHON}" ]; then
  echo "Python environment not found. Follow the setup steps in README.md first."
  exit 1
fi

start_hintos_ollama
warm_hintos_ollama

export HINTOS_OFFLINE=1
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
cd "${PROJECT_DIR}"
exec "${PYTHON}" -m uvicorn app:app --host "${HINTOS_BIND_HOST:-127.0.0.1}" --port 8000
