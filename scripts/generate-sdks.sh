#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPENAPI="${ROOT_DIR}/api/openapi.yaml"
OUT_DIR="${ROOT_DIR}/generated"
CLIENT_APIS="Auth:Devices:Missions:RawData:RuleHits:Incidents:ClosedLoopActions:Messages"

if ! command -v openapi-generator-cli >/dev/null 2>&1; then
  echo "Install the official generator: npm install -g @openapitools/openapi-generator-cli" >&2
  exit 127
fi

GENERATOR_VERSION="$(openapi-generator-cli version)"
if [[ ! "${GENERATOR_VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+([.-][[:alnum:].-]+)?$ ]]; then
  echo "Invalid OpenAPI generator. Install @openapitools/openapi-generator-cli, not openapi-generator-cli." >&2
  exit 1
fi

mkdir -p "${OUT_DIR}"
STAGING_DIR="$(mktemp -d "${OUT_DIR}/.sdk-generation.XXXXXX")"
trap 'rm -rf "${STAGING_DIR}"' EXIT

openapi-generator-cli generate \
  -i "${OPENAPI}" \
  -g typescript-fetch \
  -c "${ROOT_DIR}/sdks/typescript/config.yaml" \
  --global-property "apis=${CLIENT_APIS},models,supportingFiles" \
  -o "${STAGING_DIR}/typescript"

openapi-generator-cli generate \
  -i "${OPENAPI}" \
  -g python \
  -c "${ROOT_DIR}/sdks/python/config.yaml" \
  --global-property "apis=${CLIENT_APIS},models,supportingFiles" \
  -o "${STAGING_DIR}/python"

openapi-generator-cli generate \
  -i "${OPENAPI}" \
  -g java \
  -c "${ROOT_DIR}/sdks/java/config.yaml" \
  --global-property "apis=${CLIENT_APIS},models,supportingFiles" \
  -o "${STAGING_DIR}/java"

# Replace complete outputs only after all generators succeed; preserve earlier outputs.
BACKUP_ROOT="${ROOT_DIR}/.local/sdk-backups"
mkdir -p "${BACKUP_ROOT}"
BACKUP_DIR="$(mktemp -d "${BACKUP_ROOT}/generation.XXXXXX")"
for SDK in typescript python java; do
  if [[ -e "${OUT_DIR}/${SDK}" ]]; then
    mv "${OUT_DIR}/${SDK}" "${BACKUP_DIR}/${SDK}"
  fi
  mv "${STAGING_DIR}/${SDK}" "${OUT_DIR}/${SDK}"
done
