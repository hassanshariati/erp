"""Static and runtime contract checks for per-site editable login branding."""

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
    APP / "bisness_core" / "doctype" / "business_branding_settings"
    / "business_branding_settings.json"
)


class LoginBrandingTests(unittest.TestCase):
    def test_login_svgs_are_included_when_app_is_packaged(self):
        manifest = (ROOT / "apps" / "bisness_core" / "MANIFEST.in").read_text(encoding="utf-8")
        self.assertIn("*.svg", manifest)

    def test_business_settings_are_editable_and_accessible(self):
        doc = json.loads(SETTINGS.read_text(encoding="utf-8"))
        self.assertEqual(doc["name"], "Business Branding Settings")
        self.assertEqual(doc["issingle"], 1)
        self.assertEqual(doc["module"], "Bisness Core")
        self.assertTrue({"brand_name", "brand_tagline", "brand_logo", "accent_color",
                         "animation_file"} <= {f["fieldname"] for f in doc["fields"]})
        self.assertTrue(any(p.get("role") == "System Manager" and p.get("write")
                            for p in doc["permissions"]))
        self.assertFalse((APP / "bisness_core" / "doctype" /
                          "bisness_branding_settings" /
                          "bisness_branding_settings.json").exists())
        patch = (APP / "patches" / "v0_2" / "rename_branding_settings.py").read_text()
        self.assertIn('OLD = "Bisness Branding Settings"', patch)
        self.assertIn('NEW = "Business Branding Settings"', patch)
        self.assertIn("rename_doc", patch)
        self.assertIn("tabSingles", patch)
        patch_list = (APP / "patches.txt").read_text()
        self.assertIn("[pre_model_sync]", patch_list)
        self.assertIn("rename_branding_settings", patch_list)

        workspace = json.loads((APP / "bisness_core" / "workspace" /
                                "business_settings" / "business_settings.json").read_text())
        self.assertEqual(workspace["name"], "Business Settings")
        self.assertTrue(any(s.get("link_to") == "Business Branding Settings"
                            for s in workspace["shortcuts"]))
        sidebar = json.loads((APP / "bisness_core" / "sidebar" /
                              "business_settings" / "business_settings.json").read_text())
        self.assertTrue(any(i.get("link_to") == "Business Branding Settings"
                            for i in sidebar["items"]))

    def test_login_js_loaded_via_frappe_hook(self):
        hooks = ast.parse((APP / "hooks.py").read_text(encoding="utf-8"))
        values = {
            target.id: ast.literal_eval(node.value)
            for node in hooks.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name) and target.id == "web_include_js"
        }
        self.assertEqual(values["web_include_js"],
                         ["/assets/bisness_core/js/login-branding.js"])
        js = (APP / "public" / "js" / "login-branding.js").read_text()
        css = (APP / "public" / "css" / "login-theme.css").read_text()
        for required in ("#page-login", "get_login_branding", "autoplay", "muted",
                         "loop", "textContent", "MutationObserver", "logo_version",
                         "media_version", "loadeddata", 'addEventListener("load"'):
            self.assertIn(required, js)
        for required in ("bisness-login-orbit", "@keyframes bisness-orbit",
                         "prefers-reduced-motion"):
            self.assertIn(required, css)

    def test_only_verified_public_media_is_returned(self):
        settings = {
            "brand_name": "Example Tenant",
            "brand_tagline": "Shared operations",
            "brand_logo": "/files/example logo.png",
            "animation_file": "/files/orbit.webm",
            "accent_color": "#ABCDEF",
        }
        fake_frappe = types.ModuleType("frappe")
        fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
        fake_frappe.whitelist = lambda **kwargs: lambda fn: fn
        fake_frappe.get_cached_doc = lambda doctype: settings
        fake_frappe.db = types.SimpleNamespace(
            get_value=lambda doctype, filters, field: (
                "2026-11-12 10:00:00"
                if doctype == "File" and filters["file_url"] in
                {"/files/example logo.png", "/files/orbit.webm"}
                and filters["is_private"] == 0 else None
            )
        )
        existing = sys.modules.get("frappe")
        sys.modules["frappe"] = fake_frappe
        try:
            spec = importlib.util.spec_from_file_location("_branding_contract", BRANDING)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            result = module.get_login_branding()
            self.assertEqual(result["brand_name"], "Example Tenant")
            self.assertEqual(result["logo_url"], "/files/example logo.png")
            self.assertEqual(result["media_url"], "/files/orbit.webm")
            self.assertEqual(result["media_kind"], "video")
            self.assertEqual(result["accent_color"], "#ABCDEF")
            self.assertEqual(len(result["logo_version"]), 12)
            self.assertEqual(len(result["media_version"]), 12)

            settings["brand_logo"] = "https://tracker.example/logo.png"
            settings["animation_file"] = "/private/files/secret.mp4"
            settings["accent_color"] = "red; background:url(https://tracker.example)"
            rejected = module.get_login_branding()
            self.assertEqual(rejected["logo_url"], "")
            self.assertEqual(rejected["media_url"], "")
            self.assertEqual(rejected["accent_color"], "#35C991")

            settings["brand_logo"] = "/files/unknown.png"
            self.assertEqual(module.get_login_branding()["logo_url"], "")
            settings["brand_logo"] = "/files/%2e%2e/secret.png"
            self.assertEqual(module.get_login_branding()["logo_url"], "")
        finally:
            if existing is None:
                sys.modules.pop("frappe", None)
            else:
                sys.modules["frappe"] = existing


if __name__ == "__main__":
    unittest.main()
