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
# Regression guard for the shared login experience: keep Frappe's native
# username/password input while loading the new theme and image from assets.
# These checks are read-only and run on the isolated staging site before publish.
echo "Checking Frappe /login page..."
login_html="$(curl --fail --silent --show-error --max-time 15 \
  --retry 12 --retry-delay 5 --retry-connrefused \
  -H "Host: $SITE_NAME" "http://127.0.0.1:$HOST_HTTP_PORT/login")"
for marker in 'id="page-login"' 'id="login_email"' 'id="login_password"' 'login-theme.css'; do
  if [[ "$login_html" != *"$marker"* ]]; then
    echo "Login page missing expected Frappe markup or stylesheet: $marker" >&2
    exit 1
  fi
done
echo "Checking packaged /assets/bisness_core/css/login-theme.css..."
login_css="$(curl --fail --silent --show-error --max-time 15 \
  --retry 12 --retry-delay 5 --retry-connrefused \
  -H "Host: $SITE_NAME" \
  "http://127.0.0.1:$HOST_HTTP_PORT/assets/bisness_core/css/login-theme.css")"
[[ "$login_css" == *'#page-login'* ]] || {
  echo "Login theme CSS asset is not served correctly." >&2; exit 1;
}
echo "Checking packaged /assets/bisness_core/images/login-visual.svg..."
login_visual="$(curl --fail --silent --show-error --max-time 15 \
  --retry 12 --retry-delay 5 --retry-connrefused \
  -H "Host: $SITE_NAME" \
  "http://127.0.0.1:$HOST_HTTP_PORT/assets/bisness_core/images/login-visual.svg")"
[[ "$login_visual" == *'<svg'* ]] || {
  echo "Login theme SVG asset is not served correctly." >&2; exit 1;
}
# Validate tenant branding functionality, not just the previous static theme.
for path in \
  assets/bisness_core/js/login-branding.js \
  assets/bisness_core/images/login-mark.svg; do
  body="$(curl --fail --silent --show-error --max-time 15 \
    --retry 12 --retry-delay 5 --retry-connrefused \
    -H "Host: $SITE_NAME" "http://127.0.0.1:$HOST_HTTP_PORT/$path")"
  case "$path" in
    *.js) [[ "$body" == *"get_login_branding"* ]] || { echo "Branding JS not served" >&2; exit 1; } ;;
    *.svg) [[ "$body" == *"<svg"* ]] || { echo "Branding logo SVG not served" >&2; exit 1; } ;;
  esac
done
[[ "$login_html" == *"login-branding.js"* ]] || { echo "Login page does not load branding script" >&2; exit 1; }
branding="$(curl --fail --silent --show-error --max-time 15 \
  --retry 12 --retry-delay 5 --retry-connrefused \
  -H "Host: $SITE_NAME" \
  "http://127.0.0.1:$HOST_HTTP_PORT/api/method/bisness_core.api.branding.get_login_branding")"
[[ "$branding" == *'"brand_name"'* && "$branding" == *'"accent_color"'* ]] || {
  echo "Guest branding API does not return expected public data" >&2; exit 1;
}
echo "Tenant branding JS, icon, guest API, and native Frappe login are healthy."
echo "Native Frappe login and new theme assets served successfully."
echo "ERPNext, CRM, Insights and Wiki disposable-site checks passed."
