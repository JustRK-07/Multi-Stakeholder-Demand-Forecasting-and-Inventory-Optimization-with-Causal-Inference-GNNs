from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd

from .forecast_model import load_or_train


@dataclass
class ShapFeature:
    feature: str
    importance: float
    shap: float


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
    recent = df.sort_values("date").tail(200)
    from .features import build_feature_frame

    feats = build_feature_frame(recent)
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
