from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

from .data import DEFAULT_DATA_PATH, load_groceries_sales


@dataclass
class CausalResult:
    promo_id: str
    promo_name: str
    lift_pct: float
    confidence: float
    baseline: float
    with_promo: float
    incremental_units: float
    ate_units: float
    methods: Dict[str, float]
    diagnostics: Dict[str, float]
    cohort: Dict[str, object]
    warning: Optional[str] = None


@dataclass
class CausalFactor:
    factor: str
    impact: float
    direction: str


def _prepare_frame(store_id: Optional[str] = None) -> pd.DataFrame:
    df = load_groceries_sales(DEFAULT_DATA_PATH)
    if store_id:
        df = df[df["store_id"] == str(store_id)]
    df = df.copy()
    df["dow"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    return df


PROMOTION_SEGMENTS: Dict[str, Dict[str, object]] = {
    "all": {"name": "All Promotions"},
    "holiday": {"name": "Holiday Promotion", "filter": lambda df: df["holiday"] == 1},
    "high_discount": {"name": "High Discount", "filter": lambda df: df["discount"] >= df["discount"].median()},
    "weekend": {"name": "Weekend Promotion", "filter": lambda df: df["dow"].isin([5, 6])},
    "winter": {"name": "Winter Promotion", "filter": lambda df: df["seasonality"].astype(str).str.lower() == "winter"},
}


def available_promotion_segments() -> List[Dict[str, str]]:
    return [{"id": key, "name": value["name"]} for key, value in PROMOTION_SEGMENTS.items()]


def _features(df: pd.DataFrame) -> pd.DataFrame:
    X = df[
        ["price", "discount", "competitor_price", "holiday", "dow", "month"]
    ].copy()
    X = pd.get_dummies(X, columns=[], dtype=float)
    return X


def _psm_ate(df: pd.DataFrame) -> float:
    X = _features(df)
    y = df["units_sold"].values
    t = df["holiday"].values

    if t.mean() == 0 or t.mean() == 1:
        return 0.0

    model = LogisticRegression(max_iter=200)
    model.fit(X, t)
    scores = model.predict_proba(X)[:, 1]

    treated_idx = np.where(t == 1)[0]
    control_idx = np.where(t == 0)[0]
    if len(treated_idx) == 0 or len(control_idx) == 0:
        return 0.0

    nn = NearestNeighbors(n_neighbors=1)
    nn.fit(scores[control_idx].reshape(-1, 1))
    _, indices = nn.kneighbors(scores[treated_idx].reshape(-1, 1))
    matched_controls = control_idx[indices[:, 0]]
    return float(y[treated_idx].mean() - y[matched_controls].mean())


def _dml_ate(df: pd.DataFrame) -> float:
    X = _features(df)
    y = df["units_sold"].values
    t = df["holiday"].values
    if t.mean() == 0 or t.mean() == 1:
        return 0.0

    y_model = RandomForestRegressor(n_estimators=30, max_depth=6, random_state=42, n_jobs=1)
    t_model = LogisticRegression(max_iter=200)
    y_model.fit(X, y)
    t_model.fit(X, t)

    y_hat = y_model.predict(X)
    t_hat = t_model.predict_proba(X)[:, 1]
    y_resid = y - y_hat
    t_resid = t - t_hat

    lr = LinearRegression()
    lr.fit(t_resid.reshape(-1, 1), y_resid)
    return float(lr.coef_[0])


def _did_ate(df: pd.DataFrame) -> float:
    df = df.sort_values("date")
    treated_units = df.groupby(["store_id", "product_id"])["holiday"].max()
    treated_keys = treated_units[treated_units == 1].index
    control_keys = treated_units[treated_units == 0].index

    if len(treated_keys) == 0 or len(control_keys) == 0:
        return 0.0

    def unit_diff(keys, mode: str) -> float:
        diffs = []
        for key in keys:
            g = df[(df["store_id"] == key[0]) & (df["product_id"] == key[1])].sort_values("date")
            if g.empty:
                continue
            if mode == "treated":
                pre = g[g["holiday"] == 0]["units_sold"].mean()
                post = g[g["holiday"] == 1]["units_sold"].mean()
            else:
                mid = len(g) // 2
                pre = g.iloc[:mid]["units_sold"].mean()
                post = g.iloc[mid:]["units_sold"].mean()
            if np.isfinite(pre) and np.isfinite(post):
                diffs.append(post - pre)
        return float(np.mean(diffs)) if diffs else 0.0

    treated_diff = unit_diff(treated_keys, "treated")
    control_diff = unit_diff(control_keys, "control")
    return treated_diff - control_diff


def _estimate_from_frame(df: pd.DataFrame, promo_id: str, store_id: Optional[str], sku: Optional[str]) -> CausalResult:
    if df.empty:
        return CausalResult(
            promo_id=promo_id,
            promo_name=PROMOTION_SEGMENTS.get(promo_id, PROMOTION_SEGMENTS["all"])["name"],
            lift_pct=0.0,
            confidence=0.0,
            baseline=0.0,
            with_promo=0.0,
            incremental_units=0.0,
            ate_units=0.0,
            methods={"psm": 0.0, "dml": 0.0, "did": 0.0},
            diagnostics={"treated_share": 0.0, "sample_size": 0.0, "spread_pct": 0.0},
            cohort={"store_id": store_id, "sku": sku},
            warning="No data.",
        )

    segment = PROMOTION_SEGMENTS.get(promo_id, PROMOTION_SEGMENTS["all"])
    if "filter" in segment:
        treatment_mask = segment["filter"](df)
        if hasattr(treatment_mask, "any") and treatment_mask.any():
            df = df.copy()
            df["holiday"] = treatment_mask.astype(int)

    baseline = float(df[df["holiday"] == 0]["units_sold"].mean())
    with_promo = float(df[df["holiday"] == 1]["units_sold"].mean())
    baseline = baseline if np.isfinite(baseline) else 0.0
    with_promo = with_promo if np.isfinite(with_promo) else 0.0

    psm = _psm_ate(df)
    dml = _dml_ate(df)
    did = _did_ate(df)

    effects = np.array([psm, dml, did], dtype=float)
    spread = float(np.max(effects) - np.min(effects))

    # Use a simple inverse-variance weighting proxy.
    variances = np.maximum(np.abs(effects), 1.0)
    weights = 1.0 / (variances ** 2)
    ate = float(np.average(effects, weights=weights))

    lift_pct = 0.0
    if baseline > 0:
        lift_pct = (ate / baseline) * 100.0

    confidence = float(np.clip(70 + min(25, abs(lift_pct)), 0, 99))
    warning = None
    if spread / max(1.0, baseline) * 100.0 > 10:
        warning = "Estimates diverge across methods."

    return CausalResult(
        promo_id=promo_id,
        promo_name=segment["name"],
        lift_pct=round(lift_pct, 1),
        confidence=round(confidence, 1),
        baseline=round(baseline, 2),
        with_promo=round(with_promo, 2),
        incremental_units=round(with_promo - baseline, 2),
        ate_units=round(ate, 2),
        methods={"psm": round(psm, 2), "dml": round(dml, 2), "did": round(did, 2)},
        diagnostics={
            "treated_share": round(float(df["holiday"].mean() * 100.0), 2),
            "sample_size": float(len(df)),
            "spread_pct": round(float(spread / max(1.0, baseline) * 100.0), 2),
        },
        cohort={"store_id": store_id, "sku": sku},
        warning=warning,
    )


def estimate_promo_effect(promo_id: str = "all", store_id: Optional[str] = None, sku: Optional[str] = None) -> CausalResult:
    df = _prepare_frame(store_id)
    if sku:
        df = df[df["product_id"] == str(sku)]
    return _estimate_from_frame(df, promo_id, store_id, sku)


def promotion_summary(store_id: Optional[str] = None, sku: Optional[str] = None) -> List[Dict[str, object]]:
    df = _prepare_frame(store_id)
    if sku:
        df = df[df["product_id"] == str(sku)]
    rows = []
    for segment in available_promotion_segments():
        result = _estimate_from_frame(df.copy(), segment["id"], store_id, sku)
        rows.append(
            {
                "id": result.promo_id,
                "name": result.promo_name,
                "lift": result.lift_pct,
                "confidence": result.confidence,
                "baseline": result.baseline,
                "withPromo": result.with_promo,
                "incrementalUnits": result.incremental_units,
                "warning": result.warning,
            }
        )
    rows.sort(key=lambda row: row["lift"], reverse=True)
    return rows


def explain_factors(store_id: Optional[str] = None, sku: Optional[str] = None, top_n: int = 6) -> List[CausalFactor]:
    df = _prepare_frame(store_id)
    if sku:
        df = df[df["product_id"] == str(sku)]
    if df.empty:
        return []

    X = df[
        ["price", "discount", "competitor_price", "holiday", "dow", "month", "seasonality", "weather"]
    ].copy()
    X = pd.get_dummies(X, columns=["seasonality", "weather"], dtype=float)
    y = df["units_sold"].values.astype(float)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    lr = LinearRegression()
    lr.fit(X_scaled, y)
    coefs = lr.coef_

    impacts: List[CausalFactor] = []
    total = float(np.sum(np.abs(coefs))) or 1.0

    for name, coef in zip(X.columns, coefs):
        impact = float(abs(coef) / total * 100.0)
        direction = "positive" if coef >= 0 else "negative"
        factor_name = name.replace("seasonality_", "Season ").replace("weather_", "Weather ")
        factor_name = factor_name.replace("competitor_price", "Competitor Price")
        factor_name = factor_name.replace("price", "Price")
        factor_name = factor_name.replace("discount", "Discount")
        factor_name = factor_name.replace("holiday", "Holiday/Promotion")
        factor_name = factor_name.replace("dow", "Day of Week")
        factor_name = factor_name.replace("month", "Month")
        impacts.append(CausalFactor(factor=factor_name, impact=round(impact, 1), direction=direction))

    impacts.sort(key=lambda x: x.impact, reverse=True)
    return impacts[:top_n]
