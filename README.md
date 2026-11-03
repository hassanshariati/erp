# ERPNext deployment workspace

This repository tracks **ERPNext v16.53.0 source as a Git submodule** at `upstream/erpnext` and includes the official Frappe Docker **disposable demo** Compose definition (`compose.demo.yml`). ERPNext is GPL-3.0 licensed; retain notices and comply with its license. No upstream application code has been modified.

## Clone including source

```bash
git clone --recurse-submodules https://github.com/hassanshariati/erp.git
cd erp
```

## Local evaluation ONLY

Requires Docker Engine and Docker Compose v2. The demo has default credentials and binds port 8080 on all interfaces. **Never run this demo on a public server or expose port 8080 to the internet.** Only run on an isolated development machine:

```bash
docker compose -f compose.demo.yml up -d
# open http://localhost:8080 once the site is created
```

Upstream demo credentials: `Administrator` / `admin` (NOT for production). Stop with `docker compose -f compose.demo.yml down` (do not use `-v` unless intentionally deleting data).

## Production deployment

**Do not deploy compose.demo.yml in production.** Use the official production stack from https://github.com/frappe/frappe_docker (`compose.yaml` and appropriate overrides). Before deployment configure a domain, HTTPS/TLS reverse proxy, strong database and admin secrets, persistent volumes, encrypted backups and recovery tests. Pin an approved image release and verify compatibility with the tracked source. Production configuration will be added after server OS, domain and access method are confirmed.

## Upstream

- ERPNext: https://github.com/frappe/erpnext
- Official Docker: https://github.com/frappe/frappe_docker
- Production docs: https://frappe.github.io/frappe_docker/
