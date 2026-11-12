"""Frappe v16 app switcher registration for the first-party app."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "bisness_core" / "bisness_core"


class BusinessCoreAppScreenTests(unittest.TestCase):
    def test_registers_app_screen_entry_and_existing_logo(self):
        hooks = ast.parse((APP / "hooks.py").read_text())
        names = {target.id: node.value for node in hooks.body
                 if isinstance(node, ast.Assign)
                 for target in node.targets if isinstance(target, ast.Name)}
        self.assertEqual(ast.literal_eval(names["app_name"]), "bisness_core")
        self.assertEqual(ast.literal_eval(names["app_title"]), "Business Core")
        self.assertEqual(ast.literal_eval(names["app_logo_url"]),
                         "/assets/bisness_core/images/login-mark.svg")
        self.assertEqual(ast.literal_eval(names["app_home"]),
                         "/desk/business-settings")
        self.assertIn("add_to_apps_screen", names)
        registration = ast.unparse(names["add_to_apps_screen"])
        self.assertIn("bisness_core.api.navigation.check_app_permission", registration)
        self.assertIn("app_logo_url", registration)
        self.assertTrue((APP / "public" / "images" / "login-mark.svg").is_file())

    def test_permissions_match_workspace(self):
        workspace = (APP / "bisness_core" / "workspace"
                     / "business_settings" / "business_settings.json").read_text()
        navigation = (APP / "api" / "navigation.py").read_text()
        self.assertIn('"System Manager"', workspace)
        self.assertIn('"System Manager"', navigation)
        self.assertIn('"Administrator"', navigation)
        self.assertIn('"Guest"', navigation)


if __name__ == "__main__":
    unittest.main()
