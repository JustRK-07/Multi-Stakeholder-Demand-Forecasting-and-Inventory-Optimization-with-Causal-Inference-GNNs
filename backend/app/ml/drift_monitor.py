from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .data import DEFAULT_DATA_PATH, load_groceries_sales

ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_DIR = ROOT / "backend" / "app" / "ml" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOT_PATH = ARTIFACT_DIR / "drift_snapshot.csv"


def export_snapshot(path: Optional[Path] = None, rows: int = 5000) -> Path:
    df = load_groceries_sales(DEFAULT_DATA_PATH)
    df = df.sort_values("date").tail(rows)
    out = path or SNAPSHOT_PATH
    df.to_csv(out, index=False)
    return out


NUMERIC_DRIFT_COLUMNS = [
    "units_sold",
    "inventory_level",
    "price",
    "discount",
    "competitor_price",
    "holiday",
]


def _safe_shift_pct(baseline_mean: float, recent_mean: float) -> float:
    denom = abs(baseline_mean) if abs(baseline_mean) > 1e-9 else 1.0
    return ((recent_mean - baseline_mean) / denom) * 100.0


def _psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    if expected.size == 0 or actual.size == 0:
        return 0.0
    lower = min(float(np.min(expected)), float(np.min(actual)))
    upper = max(float(np.max(expected)), float(np.max(actual)))
    if lower == upper:
        return 0.0

    edges = np.linspace(lower, upper, bins + 1)
    expected_hist, _ = np.histogram(expected, bins=edges)
    actual_hist, _ = np.histogram(actual, bins=edges)

    expected_pct = np.clip(expected_hist / max(expected_hist.sum(), 1), 1e-6, None)
    actual_pct = np.clip(actual_hist / max(actual_hist.sum(), 1), 1e-6, None)
    return float(np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct)))


def _drift_severity(psi_score: float, mean_shift_pct: float) -> str:
    abs_shift = abs(mean_shift_pct)
    if psi_score >= 0.5 or abs_shift >= 50:
        return "critical"
    if psi_score >= 0.25 or abs_shift >= 30:
        return "high"
    if psi_score >= 0.1 or abs_shift >= 15:
        return "medium"
    return "low"


def generate_drift_report(
    baseline_days: int = 60,
    recent_days: int = 14,
    rows: int = 5000,
) -> Dict[str, Any]:
    df = load_groceries_sales(DEFAULT_DATA_PATH).sort_values("date").tail(rows).copy()
    if df.empty:
        return {
            "baselineWindowDays": baseline_days,
            "recentWindowDays": recent_days,
            "features": [],
            "alerts": [],
            "summary": {"severity": "low", "featureCount": 0, "observationCount": 0},
        }

    df["date"] = pd.to_datetime(df["date"])
    end_date = df["date"].max()
    recent_start = end_date - pd.Timedelta(days=max(recent_days - 1, 0))
    baseline_end = recent_start - pd.Timedelta(days=1)
    baseline_start = baseline_end - pd.Timedelta(days=max(baseline_days - 1, 0))

    recent = df[df["date"] >= recent_start]
    baseline = df[(df["date"] >= baseline_start) & (df["date"] <= baseline_end)]
    if baseline.empty:
        split = max(len(df) - max(recent_days * 50, 1), 1)
        baseline = df.iloc[:split]
        recent = df.iloc[split:]
    if recent.empty:
        recent = df.tail(min(len(df), max(recent_days * 50, 1)))

    features: List[Dict[str, Any]] = []
    for column in NUMERIC_DRIFT_COLUMNS:
        if column not in df.columns:
            continue
        baseline_series = baseline[column].astype(float).replace([np.inf, -np.inf], np.nan).dropna()
        recent_series = recent[column].astype(float).replace([np.inf, -np.inf], np.nan).dropna()
        if baseline_series.empty or recent_series.empty:
            continue

        baseline_mean = float(baseline_series.mean())
        recent_mean = float(recent_series.mean())
        psi_score = _psi(baseline_series.to_numpy(), recent_series.to_numpy())
        mean_shift_pct = _safe_shift_pct(baseline_mean, recent_mean)
        severity = _drift_severity(psi_score, mean_shift_pct)
        features.append(
            {
                "feature": column,
                "baselineMean": round(baseline_mean, 4),
                "recentMean": round(recent_mean, 4),
                "meanShiftPct": round(mean_shift_pct, 2),
                "psi": round(psi_score, 4),
                "severity": severity,
            }
        )

    severity_rank = {"critical": 3, "high": 2, "medium": 1, "low": 0}
    features.sort(key=lambda row: (severity_rank[row["severity"]], abs(row["meanShiftPct"]), row["psi"]), reverse=True)
    overall = features[0]["severity"] if features else "low"

    alerts = [
        {
            "severity": row["severity"],
            "title": f"{row['feature']} drift",
            "message": f"{row['feature']} shifted {row['meanShiftPct']}% with PSI {row['psi']}.",
        }
        for row in features
        if row["severity"] in {"high", "critical"}
    ]

    target = next((row for row in features if row["feature"] == "units_sold"), None)
    return {
        "baselineWindowDays": baseline_days,
        "recentWindowDays": recent_days,
        "baselineStart": baseline_start.date().isoformat(),
        "baselineEnd": baseline_end.date().isoformat(),
        "recentStart": recent_start.date().isoformat(),
        "recentEnd": end_date.date().isoformat(),
        "features": features,
        "alerts": alerts,
        "target": target,
        "summary": {
            "severity": overall,
            "featureCount": len(features),
            "observationCount": int(len(df)),
        },
    }
