"""Exercise fail-closed behavior with a fake Docker CLI, never a live daemon."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class OperatorGuardTests(unittest.TestCase):
    def test_probe_failure_unknown_or_existing_site_never_starts_database(self) -> None:
        for probe_mode in ("fail", "UNRECOGNIZED", "SITE_PRESENT"):
            with self.subTest(probe_mode=probe_mode), tempfile.TemporaryDirectory() as tmp:
                deploy = Path(tmp) / "deploy"
                scripts = deploy / "scripts"
                scripts.mkdir(parents=True)
                for name in ("preflight.sh", "initialize.sh"):
                    shutil.copy2(ROOT / "deploy" / "scripts" / name, scripts / name)
                (deploy / ".env").write_text(
                    "COMPOSE_PROJECT_NAME=erp-test-isolated\n"
                    "SITE_NAME=tenant.example.test\n"
                    "CUSTOM_IMAGE=test/erpnext\n"
                    "CUSTOM_TAG=test\n"
                    "ERPNEXT_VERSION=v16.53.0\n"
                    "HOST_HTTP_PORT=18880\n"
                    "PULL_POLICY=never\n",
                    encoding="utf-8",
                )
                bin_dir = Path(tmp) / "bin"
                bin_dir.mkdir()
                docker = bin_dir / "docker"
                docker.write_text(
                    "#!/usr/bin/env bash\n"
                    "printf '%s\\n' \"$*\" >> \"$DOCKER_CALL_LOG\"\n"
                    "if [[ \" $* \" == *\" run \"* ]]; then\n"
                    "  if [[ \"$PROBE_MODE\" == fail ]]; then exit 91; fi\n"
                    "  printf '%s\\n' \"$PROBE_MODE\"\n"
                    "fi\n",
                    encoding="utf-8",
                )
                docker.chmod(0o755)
                log = Path(tmp) / "docker-calls.log"
                env = {
                    **os.environ,
                    "PATH": f"{bin_dir}:{os.environ['PATH']}",
                    "PROBE_MODE": probe_mode,
                    "DOCKER_CALL_LOG": str(log),
                    "CONFIRM_INITIALIZE": "YES",
                }
                run = subprocess.run(
                    ["bash", str(scripts / "initialize.sh")],
                    cwd=deploy,
                    env=env,
                    text=True,
                    capture_output=True,
                    timeout=10,
                    check=False,
                )
                self.assertEqual(run.returncode, 3, run.stdout + run.stderr)
                self.assertNotIn(" up -d ", log.read_text(encoding="utf-8"))
                self.assertFalse((deploy / "secrets").exists())


if __name__ == "__main__":
    unittest.main()
