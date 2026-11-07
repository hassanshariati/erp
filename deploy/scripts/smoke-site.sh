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
for app in erpnext hrms erpnext_iran bisness_core crm insights wiki; do
  printf '%s\n' "$installed" | grep -Eq "^$app([[:space:]]|$)" || {
    echo "Missing installed app on site: $app"; exit 1;
  }
done
command -v curl >/dev/null || { echo "curl is required for HTTP smoke."; exit 2; }
curl --fail --silent --show-error --max-time 15 \
  --retry 12 --retry-delay 5 --retry-connrefused \
  -H "Host: $SITE_NAME" "http://127.0.0.1:$HOST_HTTP_PORT/api/method/ping" >/dev/null
# Both SPAs restrict unauthenticated visitors. CRM normally returns 403
# to Guest; a 404 or 5xx is a real route/asset/server failure.
for path in crm insights; do
  response_code="$(curl --silent --show-error --max-time 15 \
    --retry 12 --retry-delay 5 --retry-connrefused \
    --output /dev/null --write-out '%{http_code}' \
    -H "Host: $SITE_NAME" "http://127.0.0.1:$HOST_HTTP_PORT/$path")"
  echo "/$path unauthenticated HTTP $response_code"
  case "$response_code" in
    200|301|302|303|401|403) ;;
    *) echo "Unexpected route response for /$path: $response_code" >&2; exit 1 ;;
  esac
done
# Wiki's app shell exists even before a Wiki Space is created.
# Unauthenticated clients may be redirected or forbidden.
code="$(curl --silent --show-error --max-time 15 \
  --retry 12 --retry-delay 5 --retry-connrefused \
  --output /dev/null --write-out '%{http_code}' \
  -H "Host: $SITE_NAME" "http://127.0.0.1:$HOST_HTTP_PORT/wiki-app")"
echo "/wiki-app unauthenticated HTTP $code"
case "$code" in
  200|301|302|303|401|403) ;;
  *) echo "Wiki app route returned an unexpected HTTP status: $code" >&2; exit 1 ;;
esac
echo "ERPNext, CRM, Insights and Wiki disposable-site checks passed."
