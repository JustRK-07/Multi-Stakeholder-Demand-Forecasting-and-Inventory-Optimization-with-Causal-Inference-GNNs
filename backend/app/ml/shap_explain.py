from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .forecast_model import load_or_train


@dataclass
class ShapFeature:
    feature: str
    importance: float
    shap: float


FEATURE_LABELS = {
    "lag_1": "Yesterday demand",
    "lag_7": "Last week demand",
    "lag_14": "Two-week demand",
    "roll_7": "7-day demand trend",
    "discount": "Discount depth",
    "price": "Shelf price",
    "competitor_price": "Competitor price gap",
    "holiday": "Holiday or promotion",
    "dow": "Day of week",
    "month": "Month seasonality",
    "day": "Day in month",
}


def compute_shap_features(
    store_id: Optional[str] = None,
    product_id: Optional[str] = None,
    top_n: int = 8,
) -> List[ShapFeature]:
    artifacts = load_or_train()
    history = artifacts.history
    df = history.copy()

    if store_id:
        df = df[df["store_id"] == str(store_id)]
    if product_id:
        df = df[df["product_id"] == str(product_id)]
    if df.empty:
        return []

    # Build a recent window for SHAP background.
    recent = df.sort_values("date").tail(1000)
    from .features import build_feature_frame

    feats = build_feature_frame(recent)
    if feats.empty:
        feats = build_feature_frame(df.sort_values("date"))
    if feats.empty:
        return []
    target = "units_sold"
    drop_cols = ["date", target]
    feature_cols = artifacts.feature_columns
    X = feats[feature_cols]

    try:
        import shap

        explainer = shap.Explainer(artifacts.model, X)
        shap_values = explainer(X)
        values = np.abs(shap_values.values).mean(axis=0)
    except Exception:
        # Fallback: feature importance from permutation of model predictions
        base = artifacts.model.predict(X)
        values = []
        for col in feature_cols:
            Xp = X.copy()
            Xp[col] = np.random.permutation(Xp[col].values)
            pred = artifacts.model.predict(Xp)
            values.append(float(np.mean(np.abs(base - pred))))
        values = np.array(values, dtype=float)

    total = float(np.sum(values)) or 1.0
    rows: List[ShapFeature] = []
    for name, val in zip(feature_cols, values):
        rows.append(
            ShapFeature(
                feature=name,
                importance=float(val / total),
                shap=float(val),
            )
        )

    rows.sort(key=lambda r: r.importance, reverse=True)
    return rows[:top_n]


def _feature_label(name: str) -> str:
    return FEATURE_LABELS.get(name, name.replace("_", " ").title())


def build_explainability_summary(
    store_id: Optional[str] = None,
    product_id: Optional[str] = None,
    top_n: int = 5,
) -> Dict[str, Any]:
    rows = compute_shap_features(store_id=store_id, product_id=product_id, top_n=top_n)
    if not rows:
        return {
            "headline": "Explainability unavailable",
            "narrative": "There is not enough store or product history to build a stable explanation.",
            "drivers": [],
            "recommendations": ["Upload more recent sales history or broaden the selected store/product scope."],
            "focus": {"storeId": store_id, "productId": product_id},
        }

    top_rows = rows[:3]
    dominant = top_rows[0]
    driver_text = ", ".join(f"{_feature_label(row.feature)} ({row.importance * 100:.1f}%)" for row in top_rows)
    operational_recs: List[str] = []

    feature_names = {row.feature for row in rows}
    if {"lag_1", "lag_7", "roll_7"} & feature_names:
        operational_recs.append("Recent sell-through is the main signal. Keep replenishment plans aligned to the latest 7-day trend.")
    if {"discount", "holiday"} & feature_names:
        operational_recs.append("Promotion-sensitive demand is material. Review promo calendars before committing inventory.")
    if {"price", "competitor_price"} & feature_names:
        operational_recs.append("Price position is influencing demand. Check local pricing before treating the forecast as purely seasonal.")
    if not operational_recs:
        operational_recs.append("The forecast is being driven more by seasonal structure than by one-off operational events.")

    direction = "upward" if dominant.shap >= 0 else "downward"
    headline = f"{_feature_label(dominant.feature)} is the strongest {direction} demand driver"
    narrative = (
        f"The current forecast is mainly explained by {driver_text}. "
        f"{_feature_label(dominant.feature)} contributes the largest share of model impact in the selected slice."
    )

    return {
        "headline": headline,
        "narrative": narrative,
        "drivers": [
            {
                **asdict(row),
                "label": _feature_label(row.feature),
                "impactDirection": "positive" if row.shap >= 0 else "negative",
            }
            for row in rows
        ],
        "recommendations": operational_recs[:3],
        "focus": {"storeId": store_id, "productId": product_id},
    }
