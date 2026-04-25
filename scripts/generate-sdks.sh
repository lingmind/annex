#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPENAPI="${ROOT_DIR}/api/openapi.yaml"
OUT_DIR="${ROOT_DIR}/generated"

if ! command -v openapi-generator-cli >/dev/null 2>&1; then
  echo "openapi-generator-cli is required" >&2
  exit 127
fi

mkdir -p "${OUT_DIR}"

openapi-generator-cli generate \
  -i "${OPENAPI}" \
  -g typescript-fetch \
  -c "${ROOT_DIR}/sdks/typescript/config.yaml" \
  -o "${OUT_DIR}/typescript"

openapi-generator-cli generate \
  -i "${OPENAPI}" \
  -g python \
  -c "${ROOT_DIR}/sdks/python/config.yaml" \
  -o "${OUT_DIR}/python"

openapi-generator-cli generate \
  -i "${OPENAPI}" \
  -g java \
  -c "${ROOT_DIR}/sdks/java/config.yaml" \
  -o "${OUT_DIR}/java"
