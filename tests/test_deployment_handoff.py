"""Fast, no-Docker checks for the handoff's operational safety contract."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / "deploy"


class DeploymentHandoffTests(unittest.TestCase):
    def test_build_is_a_separate_explicit_action(self) -> None:
        build = (DEPLOY / "scripts" / "build-image.sh").read_text(encoding="utf-8")
        initialize = (DEPLOY / "scripts" / "initialize.sh").read_text(encoding="utf-8")
        self.assertIn("docker build", build)
        self.assertNotIn("docker build", initialize)
        self.assertIn("docker image inspect", initialize)

    def test_preflight_is_read_only_and_project_scoped(self) -> None:
        preflight = (DEPLOY / "scripts" / "preflight.sh").read_text(encoding="utf-8")
        self.assertIn("COMPOSE_PROJECT_NAME", preflight)
        self.assertIn("SITE_NAME", preflight)
        for mutation in ("docker build", "docker compose up", "install-app", "new-site"):
            self.assertNotIn(mutation, preflight)

    def test_existing_site_guard_precedes_service_start(self) -> None:
        source = (DEPLOY / "scripts" / "initialize.sh").read_text(encoding="utf-8")
        self.assertLess(source.index("sites/$SITE_NAME"), source.index('up -d db redis-cache redis-queue'))
        self.assertIn("CONFIRM_INITIALIZE", source)
        self.assertIn("SITE_PRESENT", source)
        self.assertIn("SITE_ABSENT", source)
        self.assertIn("Unable to determine site state", source)

    def test_image_and_site_verification_are_explicit(self) -> None:
        image_check = (DEPLOY / "scripts" / "verify-image.sh").read_text(encoding="utf-8")
        site_check = (DEPLOY / "scripts" / "smoke-site.sh").read_text(encoding="utf-8")
        for app in ("erpnext", "hrms", "erpnext_iran", "bisness_core", "crm", "insights", "telephony", "helpdesk", "wiki"):
            self.assertIn(app, image_check)
            self.assertIn(app, site_check)

    def test_build_context_excludes_secrets(self) -> None:
        ignored = (ROOT / ".dockerignore").read_text(encoding="utf-8")
        self.assertIn("deploy/secrets", ignored)
        self.assertIn("deploy/.env", ignored)

    def test_existing_production_upgrade_installs_new_apps_after_backup(self) -> None:
        upgrade = (DEPLOY / "scripts" / "upgrade-existing-production.sh").read_text(encoding="utf-8")
        self.assertIn("bench --site armember.ir backup --with-files", upgrade)
        self.assertIn("for app in hrms erpnext_iran bisness_core crm insights;", upgrade)
        self.assertIn("bench --site armember.ir migrate", upgrade)
        self.assertIn("ERPNext upgrade with Helpdesk, Telephony and Wiki", upgrade)
        self.assertIn("for app in hrms erpnext_iran bisness_core crm insights telephony helpdesk wiki;", upgrade)
        self.assertLess(upgrade.index("bench --site armember.ir backup --with-files"), upgrade.index("for app in hrms erpnext_iran bisness_core crm insights telephony helpdesk wiki"))
        self.assertNotIn("docker compose down -v", upgrade)

    def test_image_build_has_separate_compiler_stage(self) -> None:
        dockerfile = (DEPLOY / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("FROM frappe/build:version-16 AS builder", dockerfile)
        self.assertIn("FROM frappe/erpnext:${ERPNEXT_VERSION} AS runtime", dockerfile)
        self.assertIn("COPY --from=builder", dockerfile)


if __name__ == "__main__":
    unittest.main()
