#!/usr/bin/env bash
# Explicit first-site initialization only. Never upgrades an existing site.
set -Eeuo pipefail
cd "$(dirname "$0")/.."

if [[ "${CONFIRM_INITIALIZE:-}" != "YES" ]]; then
  echo "Refusing to create a site. Use CONFIRM_INITIALIZE=YES only on a new, isolated environment."
  exit 2
fi

bash scripts/preflight.sh
set -a
# The operator controls this server-side file; never commit it.
source ./.env
set +a
: "${SITE_NAME:?Set SITE_NAME in .env}"
: "${CUSTOM_IMAGE:?Set CUSTOM_IMAGE in .env}"
: "${CUSTOM_TAG:?Set CUSTOM_TAG in .env}"
: "${ERPNEXT_VERSION:?Set ERPNEXT_VERSION in .env}"

if [[ ! "$SITE_NAME" =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]*$ ]]; then
  echo "SITE_NAME must be a valid site name with no path or shell characters."
  exit 2
fi

COMPOSE=(docker compose -f compose.yaml -f compose.production.yaml)
docker image inspect "${CUSTOM_IMAGE}:${CUSTOM_TAG}" >/dev/null || {
  echo "Custom image missing. Run bash scripts/build-image.sh first."; exit 2;
}

# Reject existing/partial sites BEFORE starting DB. A failed Docker probe is
# not evidence that the site is absent; stop rather than guessing.
site_state="$("${COMPOSE[@]}" run --rm --no-deps -e SITE_NAME="$SITE_NAME" backend \
  bash -lc 'if test -e "sites/$SITE_NAME"; then echo SITE_PRESENT; else echo SITE_ABSENT; fi')" || {
  echo "Unable to determine site state; initialization stopped."
  exit 3
}
case "$site_state" in
  *SITE_PRESENT*)
    echo "An existing or partial site was found. No app install or migration performed."
    echo "Use a separately reviewed upgrade or restore procedure."
    exit 3
    ;;
  *SITE_ABSENT*)
    ;;
  *)
    echo "Unable to determine site state; initialization stopped."
    exit 3
    ;;
esac

umask 077
mkdir -p secrets backups
chmod 700 secrets backups
for name in db_root_password admin_password; do
  if [[ ! -s "secrets/$name" ]]; then
    openssl rand -base64 48 > "secrets/$name"
  fi
done
chmod 600 secrets/*
"${COMPOSE[@]}" config --quiet

"${COMPOSE[@]}" up -d db redis-cache redis-queue
"${COMPOSE[@]}" up -d configurator
"${COMPOSE[@]}" wait configurator

DB_ROOT_PASSWORD="$(< secrets/db_root_password)"
ADMIN_PASSWORD="$(< secrets/admin_password)"
export DB_ROOT_PASSWORD ADMIN_PASSWORD
trap 'unset DB_ROOT_PASSWORD ADMIN_PASSWORD' EXIT

"${COMPOSE[@]}" run --rm --no-deps \
  -e DB_ROOT_PASSWORD -e ADMIN_PASSWORD -e SITE_NAME="$SITE_NAME" backend bash -lc \
  'bench new-site "$SITE_NAME" --mariadb-user-host-login-scope="%" \
    --db-root-username root --db-root-password "$DB_ROOT_PASSWORD" \
    --admin-password "$ADMIN_PASSWORD" --install-app erpnext --set-default'

unset DB_ROOT_PASSWORD ADMIN_PASSWORD
trap - EXIT

# Ordered app installation: ERPNext first, then HRMS, Iran, business core, CRM, Insights.
"${COMPOSE[@]}" run --rm --no-deps -e SITE_NAME="$SITE_NAME" backend bash -lc \
  'for app in hrms erpnext_iran bisness_core crm insights wiki; do
     bench --site "$SITE_NAME" install-app "$app" || exit $?
   done
   bench --site "$SITE_NAME" list-apps'

"${COMPOSE[@]}" up -d
"${COMPOSE[@]}" ps

