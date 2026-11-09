"""Static contract: theme the native Frappe login without replacing authentication."""

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "bisness_core" / "bisness_core"


class LoginThemeTests(unittest.TestCase):
    def test_frappe_website_hook_loads_existing_app_css(self) -> None:
        hooks = ast.parse((APP / "hooks.py").read_text(encoding="utf-8"))
        declared = {
            target.id: ast.literal_eval(node.value)
            for node in hooks.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name) and target.id == "web_include_css"
        }
        self.assertEqual(
            ["/assets/bisness_core/css/login-theme.css"],
            declared["web_include_css"],
        )
        self.assertTrue((APP / "public" / "css" / "login-theme.css").is_file())

    def test_theme_is_only_visual_and_keeps_frappes_native_forms(self) -> None:
        css = (APP / "public" / "css" / "login-theme.css").read_text(encoding="utf-8")
        for required in (
            "#page-login",
            ".for-login",
            ".page-card",
            ".form-control",
            "@media",
            "prefers-reduced-motion",
            "login-visual.svg",
        ):
            self.assertIn(required, css)
        self.assertTrue((APP / "public" / "images" / "login-visual.svg").is_file())
        self.assertFalse((APP / "www" / "login.html").exists())
        self.assertFalse((APP / "public" / "js" / "login.js").exists())
        for customer in ("vira", "armember", "bmicc"):
            self.assertNotIn(customer, css.lower())

    def test_visual_does_not_hide_dashboard_when_svg_filters_are_unsupported(self) -> None:
        visual = (APP / "public" / "images" / "login-visual.svg").read_text(encoding="utf-8")
        self.assertNotIn("feDropShadow", visual)
        self.assertNotIn('filter="url(#shadow)"', visual)


if __name__ == "__main__":
    unittest.main()
