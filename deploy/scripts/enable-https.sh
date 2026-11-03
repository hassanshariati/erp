#!/usr/bin/env bash
set -Eeuo pipefail
cd /opt/erp/deploy
[[ "$(id -u)" -eq 0 ]] || { echo "Run as root (sudo)." >&2; exit 1; }
[[ -f .env ]] || { echo "Missing /opt/erp/deploy/.env" >&2; exit 1; }
[[ -f Caddyfile ]] || { echo "Missing Caddyfile" >&2; exit 1; }
dc=(docker compose -f compose.yaml -f compose.production.yaml -f compose.ssl.yaml -f compose.low-memory.yaml -f compose.registry.yaml)
read -r -p "ACME account email: " email
if [[ ! "$email" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
  echo "Invalid email" >&2; exit 2
fi
# Restrict permissions, preserve previous env and never print secrets.
chmod 600 .env
cp -p .env ".env.backup.$(date -u +%Y%m%dT%H%M%SZ)"
if grep -q '^ACME_EMAIL=' .env; then
  sed -i "s|^ACME_EMAIL=.*$|ACME_EMAIL=$email|" .env
else
  printf '\nACME_EMAIL=%s\n' "$email" >> .env
fi
echo "Checking local frontend..."
curl -fsS --max-time 15 -H 'Host: armember.ir' http://127.0.0.1:8080/ -o /dev/null || {
  echo "Frontend not responding on localhost:8080; fix application first." >&2
  exit 1
}
echo "Checking Compose configuration..."
"${dc[@]}" config --quiet
echo "Checking ports..."
if ss -ltnH '( sport = :80 or sport = :443 )' | grep -q .; then
  echo "Some process is already listening on TCP 80/443; review before starting Caddy." >&2
  ss -ltnp '( sport = :80 or sport = :443 )'
  exit 1
fi
echo "Starting HTTPS reverse proxy..."
"${dc[@]}" up -d caddy
"${dc[@]}" ps
echo "Checking public HTTPS (ACME issuance may still be in progress)..."
if curl -fsSI --max-time 30 https://armember.ir/; then
  echo "HTTPS responds successfully."
else
  echo "HTTPS not verified yet. Check DNS, provider firewall TCP 80/443 and Caddy logs." >&2
  "${dc[@]}" logs --tail=70 caddy
  exit 1
fi
