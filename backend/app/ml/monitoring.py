from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

import pandas as pd

from ..dataset_registry import get_active_dataset
from .data import resolve_data_path, load_groceries_sales
from .drift_monitor import generate_drift_report
from .forecast_model import training_summary


def _parse_trained_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _status_alerts(days_since_training: int | None, mape: float, drift_severity: str) -> List[Dict[str, str]]:
    alerts: List[Dict[str, str]] = []
    if days_since_training is not None and days_since_training >= 30:
        alerts.append(
            {
                "severity": "high",
                "title": "Model refresh overdue",
                "message": f"The forecast model was last trained {days_since_training} days ago.",
            }
        )
    elif days_since_training is not None and days_since_training >= 14:
        alerts.append(
            {
                "severity": "medium",
                "title": "Model aging",
                "message": f"The forecast model is {days_since_training} days old. A refresh should be scheduled.",
            }
        )

    if mape >= 25:
        alerts.append(
            {
                "severity": "high",
                "title": "Forecast error elevated",
                "message": f"Validation MAPE is {mape:.1f}%, which is above the target operating range.",
            }
        )
    elif mape >= 15:
        alerts.append(
            {
                "severity": "medium",
                "title": "Forecast error watch",
                "message": f"Validation MAPE is {mape:.1f}%. Monitor forecast quality for degradation.",
            }
        )

    if drift_severity in {"high", "critical"}:
        alerts.append(
            {
                "severity": drift_severity,
                "title": "Feature drift detected",
                "message": "Recent feature distributions have shifted materially against the baseline window.",
            }
        )
    return alerts


def model_status() -> Dict[str, Any]:
    summary = training_summary()
    metadata = summary["metadata"]
    metrics = summary["metrics"]
    drift = generate_drift_report()
    df = load_groceries_sales(resolve_data_path())
    active_dataset = get_active_dataset()

    trained_at_raw = str(metadata.get("trained_at", "")) or None
    trained_at = _parse_trained_at(trained_at_raw)
    now = datetime.now(timezone.utc)
    days_since_training = None if trained_at is None else max((now - trained_at).days, 0)

    last_observation = None
    data_span_days = 0
    if not df.empty:
        dates = pd.to_datetime(df["date"])
        start = dates.min()
        end = dates.max()
        last_observation = end.date().isoformat()
        data_span_days = int((end - start).days)

    alerts = _status_alerts(days_since_training, float(metrics.get("mape", 0.0)), str(drift["summary"]["severity"]))
    status = "healthy"
    if any(alert["severity"] == "critical" for alert in alerts):
        status = "critical"
    elif any(alert["severity"] == "high" for alert in alerts):
        status = "warning"
    elif alerts:
        status = "watch"

    return {
        "status": status,
        "activeDatasetId": active_dataset.get("datasetId") if active_dataset else None,
        "dataPath": str(resolve_data_path()),
        "trainedAt": trained_at_raw,
        "daysSinceTraining": days_since_training,
        "observationEndDate": last_observation,
        "dataSpanDays": data_span_days,
        "storeCount": len(summary["stores"]),
        "productCount": len(summary["products"]),
        "metrics": metrics,
        "driftSeverity": drift["summary"]["severity"],
        "topDriftFeatures": drift["features"][:3],
        "alerts": alerts + drift["alerts"][:3],
    }
