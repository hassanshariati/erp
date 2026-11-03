#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
COMPOSE=(docker compose -f compose.yaml -f compose.production.yaml -f compose.ssl.yaml)
test -f .env || { echo "Create .env and set ACME_EMAIL"; exit 1; }
mkdir -p secrets backups
chmod 700 secrets backups
for name in db_root_password admin_password; do
  if [[ ! -s "secrets/$name" ]]; then
    (umask 077; openssl rand -base64 48 > "secrets/$name")
  fi
done
"${COMPOSE[@]}" config --quiet
docker build --build-arg ERPNEXT_VERSION=v16.53.0 -t armember/erpnext:v16.53.0 -f Dockerfile .
"${COMPOSE[@]}" up -d db redis-cache redis-queue
"${COMPOSE[@]}" up -d configurator
"${COMPOSE[@]}" wait configurator
DB_ROOT_PASSWORD="$(cat secrets/db_root_password)"
ADMIN_PASSWORD="$(cat secrets/admin_password)"
export DB_ROOT_PASSWORD ADMIN_PASSWORD
if ! "${COMPOSE[@]}" run --rm --no-deps backend bash -c 'test -f sites/armember.ir/site_config.json'; then
  "${COMPOSE[@]}" run --rm -e DB_ROOT_PASSWORD -e ADMIN_PASSWORD backend bash -c 'bench new-site armember.ir --mariadb-user-host-login-scope="%" --db-root-username root --db-root-password "$DB_ROOT_PASSWORD" --admin-password "$ADMIN_PASSWORD" --install-app erpnext --set-default'
fi
unset DB_ROOT_PASSWORD ADMIN_PASSWORD
"${COMPOSE[@]}" up -d
"${COMPOSE[@]}" ps
