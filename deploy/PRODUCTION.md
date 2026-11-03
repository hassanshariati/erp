# armember.ir deployment — Ubuntu VPS

Target: 94.184.27.131. This repository prepares files only; no remote execution or SSL issuance has been verified.

Requirements: Ubuntu x86_64, Docker Engine + Compose v2, adequate RAM/disk, DNS A record armember.ir pointing to 94.184.27.131, reachable TCP 80/443, and no competing listener on those ports. Verify DNS with dig. Do not expose database, Redis or port 8080; frontend's port 8080 is loopback-only.

On the VPS:

    git clone https://github.com/hassanshariati/erp.git
    cd erp/deploy
    cp .env.example .env
    nano .env
    bash scripts/initialize.sh

Set ACME_EMAIL to an email you actually control before running. Caddy will request and renew HTTPS certificates automatically only after DNS and firewall conditions are met. Verify using curl -I https://armember.ir and check docker compose logs caddy.

The Dockerfile builds a locally tagged image FROM the official pinned ERPNext image; it does not compile Frappe from source. Source is tracked separately as a submodule.

Secrets are generated locally in deploy/secrets. Administrator password is in deploy/secrets/admin_password on the VPS. Never commit or send secrets or SSH private keys. The supplied id_ed25519.pub is a public key, not authorization for this assistant to connect. SSH requires a properly authorized operator key. Use a dedicated sudo user and test key login before disabling password/root login.

Before production use: verify site creation, TLS, scheduler/workers, backups to an encrypted off-host location and tested restores, monitoring and patching. Do not use docker compose down -v.
