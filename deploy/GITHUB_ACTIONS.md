# GitHub Actions deployment runner
Source: https://github.com/hassanshariati/erp
Target: /opt/erp/deploy (armember.ir)

## Prerequisites
Finish manual ERPNext startup, scheduler enablement, HTTPS, and a tested backup/restore plan before enabling unattended deployments.

## Runner setup
In GitHub open repository **Settings > Actions > Runners > New self-hosted runner**, choose Linux x64 and follow the current GitHub-provided download, verification, and configuration commands. Use a dedicated OS account `gha-erp` (not root). Give the runner the custom label `erpnext-deploy`, then install as a systemd service using GitHub's displayed `svc.sh` commands. Do not paste the registration token into chats, logs, or repository files.

The deployment script uses Docker and the existing /opt/erp working tree. The service account needs permission to read and write that tree and invoke Docker. Membership in the docker group is root-equivalent; therefore use a repository-specific runner only, restrict write access to main, use protected `production` environment with reviewers, and never run untrusted PR jobs on this runner. Do not run runner as root.

Example permissions (review before executing):
```bash
sudo useradd --create-home --shell /bin/bash gha-erp
sudo usermod -aG docker gha-erp
sudo chgrp -R gha-erp /opt/erp
sudo chmod -R g+rwX /opt/erp
sudo find /opt/erp -type d -exec chmod g+s {} +
sudo chmod 750 /opt/erp/deploy/scripts/ci-deploy.sh
```
Important: This grants the runner account access to deployment secrets; isolate it carefully. Avoid this on a public repository without a tightly controlled production environment.

## Trigger and safeguards
Workflow deploys on pushes to `main` affecting deploy files, or manually via workflow_dispatch. The `production` environment can require approval; set it in repository Settings > Environments. Deploys serialize, back up the site, build the pinned base image and recreate application containers only. It never runs `down -v`, never initializes the site again, and does not run migrations automatically. For schema-changing releases, plan a maintenance-window migration and rollback procedure first.

Before running the first workflow, verify runner is online, `/opt/erp` is accessible by the service account, Docker works for that account, backend is running, and the application responds on localhost:8080.
