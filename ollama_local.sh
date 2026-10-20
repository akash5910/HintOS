#!/usr/bin/env bash

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
OLLAMA_MODELS="${PROJECT_DIR}/ollama/models"
OLLAMA_HOST="127.0.0.1:11435"
OLLAMA_BASE_URL="http://127.0.0.1:11435"
OLLAMA_NO_CLOUD=1
NO_PROXY="127.0.0.1,localhost"
no_proxy="${NO_PROXY}"
HF_HOME="${PROJECT_DIR}/.cache/huggingface"
HF_HUB_CACHE="${HF_HOME}/hub"
TRANSFORMERS_CACHE="${HF_HUB_CACHE}"
export OLLAMA_MODELS OLLAMA_HOST OLLAMA_BASE_URL OLLAMA_NO_CLOUD NO_PROXY no_proxy
export HF_HOME HF_HUB_CACHE TRANSFORMERS_CACHE
mkdir -p "${OLLAMA_MODELS}"

hintos_ollama_ready() {
  curl --silent --fail --max-time 1 "${OLLAMA_BASE_URL}/api/tags" >/dev/null 2>&1
}

start_hintos_ollama() {
  if hintos_ollama_ready; then return; fi
  local ollama_bin
  ollama_bin="$(command -v ollama || true)"
  if [ -z "${ollama_bin}" ]; then
    echo "Ollama is not installed. Install the native Ollama app, then run this script again."
    return 1
  fi
  echo "Starting HintOS Ollama with its model store at ${OLLAMA_MODELS}"
  nohup "${ollama_bin}" serve >"${PROJECT_DIR}/.hintos_ollama.log" 2>&1 &
  echo "$!" >"${PROJECT_DIR}/.hintos_ollama.pid"
  for _ in $(seq 1 90); do
    if hintos_ollama_ready; then return; fi
    sleep 0.5
  done
  echo "HintOS could not start Ollama on 127.0.0.1:11435. Check whether that port is in use."
  return 1
}

warm_hintos_ollama() {
  local model tags body
  model="${HINTOS_LOCAL_MODEL:-qwen3.5:2b}"
  tags="$(curl --silent --fail --max-time 2 "${OLLAMA_BASE_URL}/api/tags" || true)"
  if ! printf '%s' "${tags}" | tr -d '[:space:]' | grep -Fq "\"name\":\"${model}\""; then return; fi
  echo "Loading ${model} into memory for quicker first replies..."
  body="{\"model\":\"${model}\",\"keep_alive\":\"30m\"}"
  if curl --silent --show-error --fail --max-time 240 \
    -H 'Content-Type: application/json' -d "${body}" \
    "${OLLAMA_BASE_URL}/api/chat" >/dev/null; then
    echo "The local tutor model is ready."
  else
    echo "Model warm-up did not complete. The first AI answer may take longer."
  fi
}
