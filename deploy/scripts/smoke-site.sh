#!/usr/bin/env bash
# Read-only smoke checks after an operator-managed disposable site installation.
set -Eeuo pipefail
cd "$(dirname "$0")/.."
test -f .env || { echo "Missing deploy/.env."; exit 2; }
set -a
source ./.env
set +a
: "${SITE_NAME:?}"
: "${HOST_HTTP_PORT:?}"

COMPOSE=(docker compose -f compose.yaml -f compose.production.yaml)
installed="$("${COMPOSE[@]}" exec -T backend bench --site "$SITE_NAME" list-apps)"
for app in erpnext hrms erpnext_iran bisness_core; do
  printf '%s\n' "$installed" | grep -Eq "^$app([[:space:]]|$)" || {
    echo "Missing installed app on site: $app"; exit 1;
  }
done
command -v curl >/dev/null || { echo "curl is required for HTTP smoke."; exit 2; }
curl --fail --silent --show-error --max-time 15 \
  --retry 12 --retry-delay 5 --retry-connrefused \
  -H "Host: $SITE_NAME" "http://127.0.0.1:$HOST_HTTP_PORT/api/method/ping" >/dev/null
echo "Four-app site and private HTTP smoke checks passed."
