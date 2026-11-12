"""Create private, editable Frappe Insights v3 charts from the DEMO KPI DocType.

Designed for the reviewed Insights v3 release included in this repository.
Only called explicitly from the demo seed CLI; never runs on migrate.
"""

import frappe


WORKBOOK_TITLE = "[DEMO] Oil & Gas | Executive Intelligence"
DASHBOARD_TITLE = "[DEMO] Oil & Gas | Executive Command Center"
TABLE_NAME = "tabDemo Oil Gas KPI"


def _measure(column, aggregation="sum"):
    return {
        "measure_name": f"{aggregation}_{column}",
        "column_name": column,
        "data_type": "Integer" if column in ("hse_events", "work_orders", "crew") else "Decimal",
        "aggregation": aggregation,
    }


def _dimension(column, label=None, granularity=None):
    result = {
        "dimension_name": label or column,
        "column_name": column,
        "data_type": "Date" if column == "production_date" else "String",
    }
    if granularity:
        result["granularity"] = granularity
    return result


def _number(field, suffix="", aggregation="sum"):
    return (
        "Number",
        {
            "number_columns": [_measure(field, aggregation)],
            "number_column_options": [{}],
            "comparison": False,
            "sparkline": False,
            "shorten_numbers": True,
            "suffix": suffix,
            "order_by": [],
        },
    )


def _axis(field, group, chart_type="Bar", compare=None, aggregate="sum"):
    d = _dimension(group, "Month" if group == "production_date" else group,
                   "month" if group == "production_date" else None)
    columns = [_measure(field, aggregate)]
    if compare:
        columns.append(_measure(compare))
    return (
        chart_type,
        {
            "x_axis": {"dimension": d},
            "y_axis": {"series": [{"name": c["measure_name"], "measure": c} for c in columns]},
            "order_by": [],
            "limit": 100,
        },
    )


def _donut(field, group):
    return (
        "Donut",
        {
            "label_column": _dimension(group),
            "value_column": _measure(field),
            "legend_position": "right",
            "max_slices": 12,
            "order_by": [],
        },
    )


def chart_definitions():
    """Pure, testable descriptions; titles are clear that data is fictional."""
    result = [
        ("Produced BOE", _number("actual_boe", " boe")),
        ("Planned BOE", _number("planned_boe", " boe")),
        ("Crude Oil Barrels", _number("oil_bbl", " bbl")),
        ("Natural Gas (Mscf)", _number("gas_mscf", " Mscf")),
        ("Estimated Revenue USD", _number("revenue_usd", " USD")),
        ("Operating Costs USD", _number("opex_usd", " USD")),
        ("Downtime Hours", _number("downtime_hours", " h")),
        ("Safety Near Misses", _number("hse_events")),
        ("Emissions (tCO2e)", _number("emissions_tco2e", " t")),
        ("Maintenance Orders", _number("work_orders")),
        ("Production vs Plan by Month", _axis("actual_boe", "production_date", "Line", "planned_boe")),
        ("Revenue vs Opex by Month", _axis("revenue_usd", "production_date", "Bar", "opex_usd")),
        ("Production by Region", _donut("actual_boe", "region")),
        ("Production by Asset", _axis("actual_boe", "asset", "Bar")),
        ("Downtime by Asset", _axis("downtime_hours", "asset", "Bar")),
        ("Emissions Trend", _axis("emissions_tco2e", "production_date", "Line")),
        ("Production Mix", _donut("actual_boe", "product_line")),
        (
            "Asset Performance Table",
            (
                "Table",
                {
                    "rows": [_dimension("asset", "Asset")],
                    "columns": [],
                    "values": [
                        _measure("actual_boe"),
                        _measure("planned_boe"),
                        _measure("revenue_usd"),
                        _measure("opex_usd"),
                        _measure("downtime_hours"),
                        _measure("water_cut_pct", "avg"),
                    ],
                    "show_row_totals": False,
                    "show_column_totals": False,
                    "order_by": [],
                },
            ),
        ),
    ]
    return result


def dashboard_layout(chart_names):
    """20-column responsive Insights layout, with 10 KPIs and 8 charts."""
    items = [{
        "type": "text",
        "text": "<h2>Oil & Gas Executive Command Center · DEMO DATA</h2><p>Fictional operational metrics for product demonstrations; not investment, reserves or safety reporting.</p>",
        "layout": {"i": "demo-header", "x": 0, "y": 0, "w": 20, "h": 2},
    }]
    for i, name in enumerate(chart_names):
        number = i < 10
        x = (i % 5) * 4 if number else ((i - 10) % 2) * 10
        y = 2 + (i // 5) * 3 if number else 8 + ((i - 10) // 2) * 8
        w, h = (4, 3) if number else (10, 8)
        items.append({
            "type": "chart", "chart": name,
            "layout": {"i": f"demo-chart-{i:02}", "x": x, "y": y, "w": w, "h": h},
        })
    return items


def install_insights_dashboard():
    """Idempotently create a private workbook, charts and dashboard on a seeded site."""
    if not frappe.db.exists("DocType", "Insights Dashboard v3"):
        frappe.throw("Insights v3 is not installed on this site")

    ds = frappe.db.get_value(
        "Insights Data Source v3", {"is_site_db": 1}, "name"
    )
    if not ds:
        frappe.throw("Insights v3 Site DB data source is missing; configure Insights first")
    # Ensure new source table appears to the workbook's query builder.
    frappe.get_doc("Insights Data Source v3", ds).update_table_list()
    if not frappe.db.exists("Insights Table v3", {"data_source": ds, "table": TABLE_NAME}):
        frappe.throw("Insights cannot discover the demo KPI table")

    workbook = frappe.db.get_value(
        "Insights Workbook", {"title": WORKBOOK_TITLE}, "name"
    )
    if not workbook:
        workbook = frappe.get_doc({
            "doctype": "Insights Workbook", "title": WORKBOOK_TITLE,
        }).insert(ignore_permissions=True).name

    query_title = "[DEMO] Daily O&G Operations"
    query_name = frappe.db.get_value(
        "Insights Query v3", {"title": query_title, "workbook": workbook}, "name"
    )
    if not query_name:
        query_name = frappe.get_doc({
            "doctype": "Insights Query v3",
            "title": query_title,
            "workbook": workbook,
            "is_builder_query": 1,
            "use_live_connection": 1,
            "operations": [{
                "type": "source",
                "table": {"type": "table", "data_source": ds, "table_name": TABLE_NAME},
            }],
        }).insert(ignore_permissions=True).name

    chart_names = []
    for i, (title, (chart_type, config)) in enumerate(chart_definitions()):
        full_title = "[DEMO] " + title
        chart_name = frappe.db.get_value(
            "Insights Chart v3", {"title": full_title, "workbook": workbook}, "name"
        )
        if not chart_name:
            chart_name = frappe.get_doc({
                "doctype": "Insights Chart v3",
                "title": full_title,
                "workbook": workbook,
                "query": query_name,
                "chart_type": chart_type,
                "sort_order": i,
                "config": config,
                "is_public": 0,
            }).insert(ignore_permissions=True).name
        chart_names.append(chart_name)

    dashboard_name = frappe.db.get_value(
        "Insights Dashboard v3", {"title": DASHBOARD_TITLE, "workbook": workbook}, "name"
    )
    if not dashboard_name:
        dashboard_name = frappe.get_doc({
            "doctype": "Insights Dashboard v3",
            "title": DASHBOARD_TITLE,
            "workbook": workbook,
            "is_public": 0,
            "items": dashboard_layout(chart_names),
        }).insert(ignore_permissions=True).name
    return {
        "workbook": workbook,
        "dashboard": dashboard_name,
        "chart_count": len(chart_names),
        "url": "/insights/workbook/" + str(workbook),
    }


def repair_demo_insights(confirm=None):
    """Repair generated charts only; preserve real workbooks and user-created charts.

    Older demo charts used capitalized 'Month', which Insights v3 rejects while
    constructing the generated summarize step. Nothing is deleted or recreated.
    """
    if confirm != "REPAIR_DEMO_INSIGHTS":
        frappe.throw("Confirmation REPAIR_DEMO_INSIGHTS required")
    workbook = frappe.db.get_value("Insights Workbook", {"title": WORKBOOK_TITLE}, "name")
    if not workbook:
        frappe.throw("Demo Insights workbook not found; run the demo seed first")

    repaired = []
    missing = []
    for title, _ in chart_definitions():
        full_title = "[DEMO] " + title
        name = frappe.db.get_value(
            "Insights Chart v3", {"workbook": workbook, "title": full_title}, "name"
        )
        if not name:
            missing.append(full_title)
            continue
        chart = frappe.get_doc("Insights Chart v3", name)
        config = frappe.parse_json(chart.config) or {}
        changed = False

        def fix_month(value):
            nonlocal changed
            if isinstance(value, dict):
                for key, child in value.items():
                    if key == "granularity" and child == "Month":
                        value[key] = "month"
                        changed = True
                    else:
                        fix_month(child)
            elif isinstance(value, list):
                for child in value:
                    fix_month(child)

        fix_month(config)
        if changed:
            chart.config = config
            chart.save(ignore_permissions=True)
            repaired.append(full_title)

    frappe.db.commit()
    return {
        "workbook": workbook,
        "dashboard": frappe.db.get_value(
            "Insights Dashboard v3",
            {"title": DASHBOARD_TITLE, "workbook": workbook}, "name"
        ),
        "repaired_charts": repaired,
        "missing_charts": missing,
        "note": "Open all charts in Insights to verify their rendered results.",
    }
