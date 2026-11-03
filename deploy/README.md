# ERPNext production-oriented VPS stack (Ubuntu x86_64)

This is a **production-oriented baseline, not a completed public production deployment**. It uses the official Frappe Docker base Compose file plus our MariaDB/Redis override. ERPNext image version: v16.53.0. The HTTP frontend binds **only to 127.0.0.1:8080**; it is deliberately NOT public until a domain and HTTPS reverse proxy are configured. No credentials are stored in Git.

## Requirements
- Ubuntu VPS, x86_64, Docker Engine and Docker Compose v2; recommended at least 4 vCPU, 8 GB RAM, 40 GB SSD (size according to workload).
- Firewall: allow SSH only from trusted IPs; open 80/443 only after TLS proxy is configured. Do not expose MariaDB, Redis or port 8080 publicly.
- Secure SSH account with sudo, SSH keys, and backups.

## Initialize on server

```bash
git clone https://github.com/hassanshariati/erp.git
cd erp/deploy
cp .env.example .env
mkdir -p secrets backups
chmod 700 secrets backups
openssl rand -base64 48 > secrets/db_root_password
openssl rand -base64 48 > secrets/admin_password
chmod 600 secrets/*
docker compose -f compose.yaml -f compose.production.yaml config --quiet
docker compose -f compose.yaml -f compose.production.yaml up -d db redis-cache redis-queue
docker compose -f compose.yaml -f compose.production.yaml up -d configurator
docker compose -f compose.yaml -f compose.production.yaml logs --tail=100 configurator
```

After configurator completes successfully, initialize the site **once** (do not repeat if the site already exists). Read the passwords into local shell variables without printing them:

```bash
DB_ROOT_PASSWORD="$(cat secrets/db_root_password)"
ADMIN_PASSWORD="$(cat secrets/admin_password)"
docker compose -f compose.yaml -f compose.production.yaml run --rm -e DB_ROOT_PASSWORD -e ADMIN_PASSWORD backend bash -c 'bench new-site --mariadb-user-host-login-scope="%" --db-root-username root --db-root-password "$DB_ROOT_PASSWORD" --admin-password "$ADMIN_PASSWORD" --install-app erpnext --set-default erp.local'
unset DB_ROOT_PASSWORD ADMIN_PASSWORD
docker compose -f compose.yaml -f compose.production.yaml up -d
docker compose -f compose.yaml -f compose.production.yaml ps
```

Check logs and wait for site initialization. To access privately before DNS/TLS, create an SSH tunnel from your own computer:

```bash
ssh -N -L 8080:127.0.0.1:8080 deploy@YOUR_VPS_IP
```

Open http://localhost:8080 and sign in as `Administrator` with the randomly generated password in `deploy/secrets/admin_password` (on the VPS). Treat that file as sensitive.

## Before going live
1. Obtain domain; point DNS A record at VPS; add a trusted TLS reverse proxy and HTTPS; update SITE_NAME and the Frappe site configuration carefully (renaming a site requires an explicit migration procedure).
2. Configure off-host encrypted backups of database and site files, retention, scheduled backup jobs and test restores.
3. Configure monitoring, updates, OS hardening, and verify ERPNext functionality.
4. Run `docker compose ... config` and smoke tests before traffic. Do not run `down -v` on a live system.

## SSH hardening checklist
- Create non-root sudo user and install **public** SSH key in `~/.ssh/authorized_keys`.
- Verify key login in a second terminal **before** disabling password login.
- Disable SSH password and root login after verification; use provider firewall/UFW to restrict SSH to your trusted IP.
- Never share a private SSH key, passwords or `.env` in chat or GitHub.
- If access must be delegated, use a time-limited dedicated user/key and revoke it afterwards.

Upstream: https://github.com/frappe/frappe_docker . This Compose baseline was sourced from the upstream `main` branch on 2026-11-03; review changes and pin a known-good upstream revision before a production release.
