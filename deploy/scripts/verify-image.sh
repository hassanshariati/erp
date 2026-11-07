#!/usr/bin/env bash
# Inspect the locally built image; never connect to any database.
set -Eeuo pipefail
cd "$(dirname "$0")/.."
test -f .env || { echo "Missing deploy/.env."; exit 2; }
set -a
source ./.env
set +a
: "${CUSTOM_IMAGE:?}"
: "${CUSTOM_TAG:?}"

IMAGE="${CUSTOM_IMAGE}:${CUSTOM_TAG}"
docker image inspect "$IMAGE" >/dev/null
docker run --rm --entrypoint bash "$IMAGE" -lc '
  set -Eeuo pipefail
  cd /home/frappe/frappe-bench
  for app in frappe erpnext hrms erpnext_iran bisness_core crm insights telephony helpdesk wiki; do
    test -d "apps/$app" || { echo "Missing app: $app"; exit 1; }
  done
  ./env/bin/python -m pip show hrms erpnext_iran bisness_core crm insights telephony helpdesk wiki >/dev/null
  echo "Helpdesk/Wiki/Telephony image package check passed."
'
