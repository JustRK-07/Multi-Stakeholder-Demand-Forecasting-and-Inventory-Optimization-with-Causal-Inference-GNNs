from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.dashboard_metrics import (  # noqa: E402
    compute_dashboard_summary,
    compute_inventory_items,
    compute_kpis,
    compute_stores,
)


def test_compute_kpis_returns_expected_cards():
    cards = compute_kpis()
    assert len(cards) == 6
    titles = {card["title"] for card in cards}
    assert {
        "Forecast Accuracy",
        "Service Level",
        "Inventory Turnover",
        "Stockout Rate",
        "Order Fill Rate",
        "MAPE",
    } <= titles


def test_compute_inventory_items_returns_ranked_items():
    items = compute_inventory_items()
    assert items
    assert {"sku", "name", "stock", "capacity", "reorderPoint", "daysOfSupply", "risk"} <= set(items[0].keys())
    severity = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    assert severity[items[0]["risk"]] <= severity[items[-1]["risk"]]


def test_compute_dashboard_summary_returns_timeseries_and_alerts():
    summary = compute_dashboard_summary()
    assert len(summary["salesTrend"]) > 0
    assert len(summary["inventoryTrend"]) > 0
    assert len(summary["alerts"]) > 0
    assert {"day", "sales", "demand"} <= set(summary["salesTrend"][0].keys())


def test_compute_stores_returns_real_store_rows():
    stores = compute_stores()
    assert len(stores) >= 1
    assert {"id", "name", "lat", "lng", "demand", "performance"} <= set(stores[0].keys())
