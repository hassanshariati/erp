"""Fast contract checks; no Frappe runtime or live site is required."""

from __future__ import annotations

import ast
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "bisness_core"
DEPLOY = ROOT / "deploy"

RUNTIME_FILES = (
    APP / "pyproject.toml",
    APP / "bisness_core" / "hooks.py",
    DEPLOY / ".env.example",
    DEPLOY / "Dockerfile",
    DEPLOY / "Caddyfile",
    DEPLOY / "compose.production.yaml",
    DEPLOY / "compose.ssl.yaml",
    DEPLOY / "scripts" / "initialize.sh",
)


class GenericProductContractTests(unittest.TestCase):
    def test_no_customer_identity_in_product_runtime(self) -> None:
        """Introducing a literal customer identity must break this test."""
        prohibited = (
            "armember",
            "vira",
            "94.184.27.131",
        )
        for path in RUNTIME_FILES:
            with self.subTest(path=str(path)):
                body = path.read_text(encoding="utf-8").lower()
                for value in prohibited:
                    self.assertNotIn(value, body)

    def test_frappe_app_has_generic_name_and_declared_requirements(self) -> None:
        """Replacing or removing the core dependencies must break this test."""
        root = ast.parse((APP / "bisness_core" / "hooks.py").read_text(encoding="utf-8"))
        values = {
            target.id: ast.literal_eval(node.value)
            for node in root.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
            and target.id in {"app_name", "required_apps"}
        }
        self.assertEqual("bisness_core", values["app_name"])
        self.assertEqual(["erpnext", "hrms", "erpnext_iran"], values["required_apps"])
        self.assertTrue((APP / "bisness_core" / "bisness_core" / "__init__.py").is_file())

    def test_external_app_source_refs_are_reviewed(self) -> None:
        """Changing a pinned commit without review must break this test."""
        source = (DEPLOY / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("ARG ERPNEXT_VERSION=v16.53.0", source)
        self.assertIn("ARG HRMS_REF=v16.53.0", source)
        self.assertIn("b12d935b99c1434618845fdd9f3a3d340b5a3aed", source)
        self.assertIn("60dc7b8b51f42a74ba65bee314922326788db59b", source)
        self.assertIn('git -C apps/hrms rev-parse HEAD', source)
        self.assertIn('git -C apps/erpnext_iran rev-parse HEAD', source)
        self.assertIn("638bf3db23e7142870819a213368e028866b79b1", source)
        self.assertIn("c7dc954d8275756deb5ad24f7c35c3f3c2ca1a6c", source)
        self.assertIn("ARG CRM_REF=main", source)
        self.assertIn("ARG INSIGHTS_REF=version-3", source)
        self.assertIn('git -C apps/crm rev-parse HEAD', source)
        self.assertIn('git -C apps/insights rev-parse HEAD', source)

    def test_default_http_is_private_and_site_is_parameterized(self) -> None:
        """Public HTTP or a fixed tenant site must break this test."""
        compose = (DEPLOY / "compose.production.yaml").read_text(encoding="utf-8")
        self.assertIn("127.0.0.1:", compose)
        self.assertIn("HOST_HTTP_PORT", compose)
        self.assertIn("SITE_NAME", compose)
        caddy = (DEPLOY / "Caddyfile").read_text(encoding="utf-8")
        self.assertIn("{$SITE_NAME}", caddy)

    def test_product_graph_uses_generic_components_and_real_dependency_edges(self) -> None:
        """Changing required app edges must break this test."""
        graph = json.loads((ROOT / "docs" / "architecture" / "product-components.json").read_text(encoding="utf-8"))
        self.assertFalse(graph["generated_by_graphify"])
        self.assertEqual("product_not_customer", graph["scope"])
        nodes = {node["id"] for node in graph["nodes"]}
        self.assertEqual({"frappe", "erpnext", "hrms", "erpnext_iran", "bisness_core"}, nodes)
        edges = {(edge["from"], edge["to"]) for edge in graph["edges"]}
        for required in ("erpnext", "hrms", "erpnext_iran"):
            self.assertIn(("bisness_core", required), edges)
        self.assertNotIn("vira", json.dumps(graph).lower())

    def test_existing_site_requires_separate_upgrade(self) -> None:
        """Allowing an automatic existing-site migration must break this test."""
        script = (DEPLOY / "scripts" / "initialize.sh").read_text(encoding="utf-8")
        self.assertIn('CONFIRM_INITIALIZE', script)
        self.assertIn('test -e "sites/$SITE_NAME"', script)
        self.assertIn("An existing or partial site was found.", script)
        self.assertIn('for app in hrms erpnext_iran bisness_core crm insights;', script)


if __name__ == "__main__":
    unittest.main()

