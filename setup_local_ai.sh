#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
. "${PROJECT_DIR}/ollama_local.sh"
start_hintos_ollama

MODEL="${HINTOS_LOCAL_MODEL:-qwen3.5:2b}"
echo "Downloading the local HintOS tutor model: ${MODEL}"
ollama pull "${MODEL}"
echo "The model is ready. HintOS can use it without internet after this download."
