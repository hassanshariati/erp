#!/usr/bin/env bash
# Read-only checks; safe to run before any Docker build or site mutation.
set -Eeuo pipefail
cd "$(dirname "$0")/.."

test -f .env || { echo "Missing deploy/.env. Copy .env.example and edit it."; exit 2; }
set -a
source ./.env
set +a

: "${COMPOSE_PROJECT_NAME:?Set a unique COMPOSE_PROJECT_NAME in .env}"
: "${SITE_NAME:?Set SITE_NAME in .env}"
: "${CUSTOM_IMAGE:?Set CUSTOM_IMAGE in .env}"
: "${CUSTOM_TAG:?Set CUSTOM_TAG in .env}"
: "${ERPNEXT_VERSION:?Set ERPNEXT_VERSION in .env}"
: "${HOST_HTTP_PORT:?Set HOST_HTTP_PORT in .env}"

[[ "$COMPOSE_PROJECT_NAME" =~ ^[a-z0-9][a-z0-9_-]*$ ]] || {
  echo "COMPOSE_PROJECT_NAME must contain only lowercase letters, digits, dash or underscore."; exit 2;
}
[[ "$SITE_NAME" =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]*$ ]] || {
  echo "Invalid SITE_NAME."; exit 2;
}
[[ "$HOST_HTTP_PORT" =~ ^[0-9]+$ ]] &&
  ((10#$HOST_HTTP_PORT >= 1024 && 10#$HOST_HTTP_PORT <= 65535)) || {
  echo "HOST_HTTP_PORT must be between 1024 and 65535."; exit 2;
}
[[ "$ERPNEXT_VERSION" == "v16.53.0" ]] || {
  echo "This integration is locked to ERPNext v16.53.0."; exit 2;
}
[[ "${PULL_POLICY:-never}" == "never" || "${PULL_POLICY:-never}" == "missing" ]] || {
  echo "PULL_POLICY must be never or missing for a custom image."; exit 2;
}

command -v docker >/dev/null || { echo "Docker is required."; exit 2; }
docker compose version >/dev/null || { echo "Docker Compose v2 is required."; exit 2; }
docker info --format '{{.ServerVersion}}' >/dev/null || {
  echo "Cannot connect to the Docker daemon."; exit 2;
}
echo "Preflight OK: project=$COMPOSE_PROJECT_NAME site=$SITE_NAME private-port=$HOST_HTTP_PORT"
