"""Contract for tenant-editable login branding and media."""

import ast
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "bisness_core" / "bisness_core"
BRANDING = APP / "api" / "branding.py"
SETTINGS = (
    APP / "bisness_core" / "doctype" / "bisness_branding_settings"
    / "bisness_branding_settings.json"
)


class LoginBrandingTests(unittest.TestCase):
    def test_login_svgs_are_included_when_app_is_packaged(self) -> None:
        manifest = (ROOT / "apps" / "bisness_core" / "MANIFEST.in").read_text(encoding="utf-8")
        self.assertIn("*.svg", manifest)

    def test_single_settings_are_editable_by_system_manager(self) -> None:
        doc = json.loads(SETTINGS.read_text(encoding="utf-8"))
        self.assertEqual(doc["name"], "Bisness Branding Settings")
        self.assertEqual(doc["issingle"], 1)
        self.assertEqual(doc["module"], "Bisness Core")
        fieldnames = {field["fieldname"] for field in doc["fields"]}
        self.assertTrue(
            {"brand_name", "brand_tagline", "brand_logo", "accent_color", "animation_file"}
            <= fieldnames
        )
        self.assertTrue(
            any(p.get("role") == "System Manager" and p.get("write") for p in doc["permissions"])
        )

    def test_login_js_is_loaded_through_supported_frappe_hook(self) -> None:
        hooks = ast.parse((APP / "hooks.py").read_text(encoding="utf-8"))
        values = {
            target.id: ast.literal_eval(node.value)
            for node in hooks.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name) and target.id == "web_include_js"
        }
        self.assertEqual(
            values["web_include_js"], ["/assets/bisness_core/js/login-branding.js"]
        )
        js = (APP / "public" / "js" / "login-branding.js").read_text(encoding="utf-8")
        css = (APP / "public" / "css" / "login-theme.css").read_text(encoding="utf-8")
        self.assertIn("#page-login", css)
        for item in ("#page-login", "get_login_branding", "autoplay", "muted", "loop", "textContent"):
            self.assertIn(item, js)
        for item in ("bisness-login-orbit", "@keyframes bisness-orbit", "prefers-reduced-motion"):
            self.assertIn(item, css)
        self.assertTrue((APP / "public" / "images" / "login-mark.svg").is_file())

    def test_guest_endpoint_returns_only_safe_public_media(self) -> None:
        settings = {
            "brand_name": "Example Tenant",
            "brand_tagline": "Shared operations",
            "brand_logo": "/files/example logo.png",
            "animation_file": "/files/orbit.webm",
            "accent_color": "#ABCDEF",
        }
        fake_frappe = types.ModuleType("frappe")
        fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
        fake_frappe.whitelist = lambda **kwargs: (lambda fn: fn)
        fake_frappe.get_cached_doc = lambda doctype: settings
        existing = sys.modules.get("frappe")
        sys.modules["frappe"] = fake_frappe
        try:
            spec = importlib.util.spec_from_file_location("_branding_contract", BRANDING)
            self.assertIsNotNone(spec)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            result = module.get_login_branding()
            self.assertEqual(result["brand_name"], "Example Tenant")
            self.assertEqual(result["logo_url"], "/files/example logo.png")
            self.assertEqual(result["media_url"], "/files/orbit.webm")
            self.assertEqual(result["media_kind"], "video")
            self.assertEqual(result["accent_color"], "#ABCDEF")

            settings["brand_logo"] = "https://tracker.example/logo.png"
            settings["animation_file"] = "/private/files/secret.mp4"
            settings["accent_color"] = "red; background:url(https://tracker.example)"
            rejected = module.get_login_branding()
            self.assertEqual(rejected["logo_url"], "")
            self.assertEqual(rejected["media_url"], "")
            self.assertEqual(rejected["accent_color"], "#35C991")
        finally:
            if existing is None:
                sys.modules.pop("frappe", None)
            else:
                sys.modules["frappe"] = existing


if __name__ == "__main__":
    unittest.main()
