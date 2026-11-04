#!/usr/bin/env bash
# Run once as root after reviewing the production release script and protecting main.
# Grants the GitHub runner ONLY the fixed root-owned deployment executable, not Docker.
set -Eeuo pipefail
[[ "$(id -u)" -eq 0 ]] || { echo "Run: sudo bash $0" >&2; exit 1; }
id gha-erp >/dev/null
src="/opt/erp/deploy/scripts/upgrade-existing-production.sh"
dst="/usr/local/sbin/erpnext-gha-release"
test -s "$src"
test ! -L "$dst" || { echo "Refusing symlink at $dst" >&2; exit 1; }
install -o root -g root -m 0755 "$src" "$dst"
printf '%s\n' 'gha-erp ALL=(root) NOPASSWD: /usr/local/sbin/erpnext-gha-release' \
  > /etc/sudoers.d/erpnext-gha-release
chmod 0440 /etc/sudoers.d/erpnext-gha-release
visudo -cf /etc/sudoers.d/erpnext-gha-release
install -o root -g root -d -m 0700 /var/backups/erpnext
echo "Root-owned deployment wrapper installed; gha-erp is NOT granted the docker group."
echo "Next: rerun the failed GitHub Actions production job after the staging image was published."
