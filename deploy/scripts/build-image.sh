#!/usr/bin/env bash
# Build only. Does not start containers or alter any ERPNext site.
set -Eeuo pipefail
cd "$(dirname "$0")/.."
bash scripts/preflight.sh
set -a
source ./.env
set +a

docker build \
  --build-arg "ERPNEXT_VERSION=$ERPNEXT_VERSION" \
  --tag "${CUSTOM_IMAGE}:${CUSTOM_TAG}" \
  --file Dockerfile ..

bash scripts/verify-image.sh
