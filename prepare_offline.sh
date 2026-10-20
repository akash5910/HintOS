#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WHEEL_FOLDER="${PROJECT_DIR}/offline_wheels"
PYTHON="${PYTHON:-python3}"

mkdir -p "${WHEEL_FOLDER}"
echo "Saving Python packages for this OS and CPU type to ${WHEEL_FOLDER}"
"${PYTHON}" -m pip download --no-cache-dir --only-binary=:all: --dest "${WHEEL_FOLDER}" -r "${PROJECT_DIR}/requirements.txt"
echo "Package cache ready. It is specific to this OS, CPU type, and Python version."
