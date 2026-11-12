"""Offline checks for the opt-in fictional contact expansion and Insights repair."""
import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "bisness_core" / "bisness_core"


class DemoPeopleExpansionTests(unittest.TestCase):
    def test_names_are_distinct_and_belong_to_demo_scope(self):
        code = (APP / "demo" / "people.py").read_text()
        module = ast.parse(code)
        arrays = {
            target.id: ast.literal_eval(stmt.value)
            for stmt in module.body if isinstance(stmt, ast.Assign)
            for target in stmt.targets if isinstance(target, ast.Name)
            and target.id in {"FIRST_NAMES", "LAST_NAMES"}
        }
        self.assertGreaterEqual(len(arrays["FIRST_NAMES"]), 40)
        self.assertGreaterEqual(len(arrays["LAST_NAMES"]), 30)
        names = [
            (arrays["FIRST_NAMES"][n % len(arrays["FIRST_NAMES"])],
             arrays["LAST_NAMES"][n // len(arrays["FIRST_NAMES"])])
            for n in range(720)
        ]
        self.assertEqual(len(names), len(set(names)))
        self.assertIn("_must_be_demo_company(company)", code)
        self.assertIn("EXPAND_OIL_GAS_DEMO", code)
        self.assertIn("DEMO-OG-PERSON-", code)
        self.assertIn('{"type": "Open"}', code)
        self.assertNotIn("frappe.whitelist", code)
        self.assertNotIn(".submit(", code)
        self.assertNotIn("password", code.lower())

    def test_charts_only_use_supported_lowercase_month(self):
        code = (APP / "demo" / "insights_dashboard.py").read_text()
        self.assertIn('"month" if group == "production_date"', code)
        self.assertIn('if key == "granularity" and child == "Month":', code)
        self.assertIn('value[key] = "month"', code)
        self.assertIn("REPAIR_DEMO_INSIGHTS", code)

    def test_existing_seed_selects_only_open_crm_statuses(self):
        code = (APP / "demo" / "seed.py").read_text()
        self.assertIn('"CRM Lead Status", {"type": "Open"}', code)
        self.assertIn('"CRM Deal Status", {"type": "Open"}', code)

    def test_login_media_is_not_silently_accepted_when_private(self):
        settings = (APP / "bisness_core" / "doctype" / "business_branding_settings"
                    / "business_branding_settings.py").read_text()
        self.assertIn("is_private", settings)
        self.assertIn("this file is PRIVATE", settings)
        self.assertIn("unchecked in the upload dialog", settings)
        css = (APP / "public" / "css" / "login-theme.css").read_text()
        self.assertIn(".bisness-login-hero--uploaded .bisness-login-hero-stage", css)
        self.assertIn("object-fit: cover", css)


if __name__ == "__main__":
    unittest.main()
