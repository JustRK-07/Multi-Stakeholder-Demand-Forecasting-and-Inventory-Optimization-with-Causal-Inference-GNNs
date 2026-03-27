from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ml.drift_monitor import generate_drift_report  # noqa: E402
from app.ml.monitoring import model_status  # noqa: E402
from app.ml.shap_explain import build_explainability_summary, compute_shap_features  # noqa: E402


def test_compute_shap_features_returns_ranked_rows():
    rows = compute_shap_features(top_n=5)
    assert rows
    assert len(rows) <= 5
    assert rows[0].importance >= rows[-1].importance


def test_explainability_summary_returns_narrative_and_recommendations():
    summary = build_explainability_summary()
    assert "headline" in summary
    assert "narrative" in summary
    assert len(summary["drivers"]) >= 1
    assert len(summary["recommendations"]) >= 1


def test_generate_drift_report_returns_feature_metrics():
    report = generate_drift_report(baseline_days=45, recent_days=10, rows=3000)
    assert report["summary"]["featureCount"] >= 1
    assert len(report["features"]) >= 1
    assert {"feature", "baselineMean", "recentMean", "meanShiftPct", "psi", "severity"} <= set(report["features"][0].keys())


def test_model_status_returns_monitoring_payload():
    status = model_status()
    assert {"status", "metrics", "driftSeverity", "alerts", "topDriftFeatures"} <= set(status.keys())
    assert {"mae", "rmse", "mape"} <= set(status["metrics"].keys())
