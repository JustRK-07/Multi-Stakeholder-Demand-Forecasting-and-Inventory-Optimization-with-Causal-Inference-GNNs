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
    lift_pct: float
    confidence: float
    baseline: float
    with_promo: float
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

    y_model = RandomForestRegressor(n_estimators=100, random_state=42)
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


def estimate_promo_effect(store_id: Optional[str] = None) -> CausalResult:
    df = _prepare_frame(store_id)
    if df.empty:
        return CausalResult(lift_pct=0.0, confidence=0.0, baseline=0.0, with_promo=0.0, warning="No data.")

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
        lift_pct=round(lift_pct, 1),
        confidence=round(confidence, 1),
        baseline=round(baseline, 2),
        with_promo=round(with_promo, 2),
        warning=warning,
    )


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
