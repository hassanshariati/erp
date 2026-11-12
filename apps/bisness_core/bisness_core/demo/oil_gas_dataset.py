"""Deterministic, fictional oil-and-gas operations data for sales demonstrations.

Never imported by hooks, migrations, schedulers, or normal customer transactions.
Every record is explicitly marked DEMO. Quantities are illustrative, not forecasts.
"""

from datetime import date, timedelta
from math import pi, sin
import random


# Fictional asset names: these are not customers, wells, contracts, or locations.
ASSETS = (
    ("Caspian Alpha", "North Offshore", "Oil", 8100),
    ("Caspian Bravo", "North Offshore", "Mixed", 6400),
    ("Persian Delta", "South Offshore", "Oil", 9900),
    ("Persian Echo", "South Offshore", "Mixed", 7800),
    ("Zagros One", "Onshore West", "Oil", 5100),
    ("Zagros Two", "Onshore West", "Mixed", 4400),
    ("Karun East", "Onshore South", "Oil", 7000),
    ("Karun West", "Onshore South", "Mixed", 6200),
    ("Desert Gas A", "Central Gas", "Natural Gas", 4700),
    ("Desert Gas B", "Central Gas", "Natural Gas", 5300),
    ("Offshore Gas C", "South Offshore", "Natural Gas", 5900),
    ("Offshore Gas D", "South Offshore", "Natural Gas", 5500),
)
PRODUCTS = (
    "Crude Oil", "Natural Gas", "Condensate", "Drilling Mud", "Wellhead Valve",
    "Pipeline Gasket", "Submersible Pump", "High Pressure Hose",
    "Instrumentation Cable", "Gas Compressor Part", "Process Filter",
    "Safety Helmet", "Flame Detector", "Protective Glove", "Control Panel",
    "Steel Pipe", "Chemical Inhibitor", "Separator Part", "Pressure Gauge",
    "Rotary Pump",
)
PROJECTS = (
    "Platform Maintenance", "Well Recompletion", "Pipeline Integrity",
    "Gas Compression Upgrade", "Produced Water Treatment", "Reservoir Study",
    "Drilling Campaign", "Export Terminal Upgrade", "HSE Audit", "SCADA Modernization",
)


def generate_daily_kpis(company, end_date=date(2026, 10, 31), days=365):
    """Yield repeatable, clearly identified daily rows suitable for Insights v3."""
    if isinstance(end_date, str):
        end_date = date.fromisoformat(end_date)
    if not (30 <= int(days) <= 730):
        raise ValueError("days must be between 30 and 730")
    rng = random.Random(20261112)
    for offset in range(int(days)):
        day = end_date - timedelta(days=int(days) - offset - 1)
        for idx, (asset, region, product, capacity) in enumerate(ASSETS):
            seasonal = 1 + 0.045 * sin(2 * pi * (offset / 365 + idx / 11))
            planned = capacity * seasonal
            downtime = round(max(0, rng.gauss(2.3, 2.5)), 1)
            uptime = max(0.52, (24 - downtime) / 24)
            actual = max(0, planned * uptime * rng.uniform(0.94, 1.035))
            oil_share = {"Oil": 0.92, "Mixed": 0.57, "Natural Gas": 0.04}[product]
            oil = actual * oil_share
            gas = (actual - oil) * 6  # illustrative Mscf-to-boe relationship
            crew = 16 + idx * 2 + (offset % 4)
            revenue = oil * 73 + gas * 3.2
            opex = actual * 22.5 + downtime * 1150 + crew * 180
            emissions = actual * (0.017 if product == "Natural Gas" else 0.025)
            slug = asset.lower().replace(" ", "-")
            yield {
                "record_id": "DEMO-OG-%s-%s" % (day.strftime("%Y%m%d"), slug),
                "production_date": day.isoformat(),
                "company": company,
                "asset": asset,
                "region": region,
                "product_line": product,
                "planned_boe": round(planned, 2),
                "actual_boe": round(actual, 2),
                "oil_bbl": round(oil, 2),
                "gas_mscf": round(gas, 2),
                "revenue_usd": round(revenue, 2),
                "opex_usd": round(opex, 2),
                "downtime_hours": downtime,
                "water_cut_pct": round(18 + idx * 2.2 + rng.uniform(-2, 2), 2),
                "emissions_tco2e": round(emissions, 2),
                "hse_events": int(rng.random() < 0.012),
                "work_orders": rng.randrange(0, 4),
                "crew": crew,
            }
