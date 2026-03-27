from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ml.forecast_model import forecast, recent_actuals, training_summary  # noqa: E402


def test_training_summary_contains_metrics_and_metadata():
    summary = training_summary()
    assert {"metrics", "metadata", "stores", "products"} <= set(summary.keys())
    assert {"mae", "rmse", "mape"} <= set(summary["metrics"].keys())
    assert "trained_at" in summary["metadata"]
    assert len(summary["stores"]) >= 1
    assert len(summary["products"]) >= 1


def test_forecast_returns_expected_rows():
    rows = forecast("S001", horizon=7, gnn_adjust=False)
    assert len(rows) == 7
    assert {"date", "predicted", "lowerBound", "upperBound"} <= set(rows[0].keys())


def test_recent_actuals_returns_history_rows():
    rows = recent_actuals("S001", None, days=5)
    assert len(rows) <= 5
    assert rows
    assert {"date", "actual"} <= set(rows[0].keys())
