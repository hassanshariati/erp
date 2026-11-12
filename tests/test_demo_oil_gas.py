"""Offline tests for the opt-in, tenant-isolated oil & gas demo package."""

import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "bisness_core" / "bisness_core"
DATASET = APP / "demo" / "oil_gas_dataset.py"
DASHBOARD = APP / "demo" / "insights_dashboard.py"
SEEDER = APP / "demo" / "seed.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class OilGasDemoTests(unittest.TestCase):
    def test_dataset_is_deterministic_and_marked_demo(self):
        generator = load_module("_oil_gas_dataset_contract", DATASET)
        first = list(generator.generate_daily_kpis("[DEMO] Operations", days=30))
        second = list(generator.generate_daily_kpis("[DEMO] Operations", days=30))
        self.assertEqual(first, second)
        self.assertEqual(len(first), 30 * 12)
        self.assertEqual(len({x["record_id"] for x in first}), len(first))
        self.assertTrue(all(x["record_id"].startswith("DEMO-OG-") for x in first))
        self.assertTrue(all(x["company"] == "[DEMO] Operations" for x in first))
        self.assertTrue(all(x["planned_boe"] > 0 and x["actual_boe"] >= 0
                            and x["downtime_hours"] >= 0 for x in first))
        with self.assertRaises(ValueError):
            list(generator.generate_daily_kpis("[DEMO] Operations", days=800))

    def test_schema_supports_insights_operations(self):
        schema = (APP / "bisness_core" / "doctype" / "demo_oil_gas_kpi" /
                  "demo_oil_gas_kpi.json")
        doc = json.loads(schema.read_text())
        self.assertEqual(doc["name"], "Demo Oil Gas KPI")
        self.assertEqual(doc["autoname"], "field:record_id")
        fields = {f["fieldname"] for f in doc["fields"]}
        expected = {"record_id", "production_date", "company", "asset", "region",
                    "planned_boe", "actual_boe", "revenue_usd", "opex_usd",
                    "downtime_hours", "water_cut_pct", "emissions_tco2e",
                    "hse_events", "work_orders", "crew"}
        self.assertTrue(expected <= fields)

    def test_insights_native_v3_charts_and_layout(self):
        fake_frappe = types.ModuleType("frappe")
        previous = sys.modules.get("frappe")
        sys.modules["frappe"] = fake_frappe
        try:
            module = load_module("_insights_demo_contract", DASHBOARD)
            definitions = module.chart_definitions()
            self.assertEqual(len(definitions), 18)
            self.assertEqual(len([d for d in definitions if d[1][0] == "Number"]), 10)
            self.assertTrue(all("order_by" in cfg for _, (_, cfg) in definitions))
            self.assertTrue(all(kind in {"Number", "Bar", "Line", "Donut", "Table"}
                                for _, (kind, _) in definitions))
            names = [f"chart-{i}" for i in range(18)]
            items = module.dashboard_layout(names)
            self.assertEqual(len(items), 19)
            self.assertEqual(sum(1 for item in items if item["type"] == "chart"), 18)
            self.assertTrue(all(0 <= item["layout"]["x"] < 20 and
                                item["layout"]["x"] + item["layout"]["w"] <= 20
                                for item in items))
            self.assertTrue(all(item["layout"]["h"] > 0 for item in items))
            self.assertIn("DEMO DATA", items[0]["text"])
        finally:
            if previous is None:
                sys.modules.pop("frappe", None)
            else:
                sys.modules["frappe"] = previous

    def test_seeder_is_off_by_default_and_never_submits_live_transactions(self):
        seed = SEEDER.read_text()
        self.assertIn("SEED_OIL_GAS_DEMO", seed)
        self.assertIn('frappe.conf.get("enable_oil_gas_demo_seed")', seed)
        self.assertIn('company.startswith(DEMO_PREFIX)', seed)
        self.assertIn("ignore_duplicates=True", seed)
        self.assertNotIn(".submit(", seed)
        self.assertNotIn("set_user(", seed)
        self.assertNotIn("set_default_company(", seed)
        self.assertNotIn("frappe.whitelist", seed)
        hooks = (APP / "hooks.py").read_text()
        self.assertNotIn("seed_demo", hooks)
        patch = (APP / "patches.txt").read_text()
        self.assertNotIn("demo.seed", patch)


if __name__ == "__main__":
    unittest.main()
