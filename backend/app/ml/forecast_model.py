from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from .data import DEFAULT_DATA_PATH, load_groceries_sales, resolve_data_path
from .gnn_inference import most_similar
from .mlflow_utils import log_run
from .features import build_feature_frame

try:
    from mapie.regression import MapieRegressor
except ImportError:  # pragma: no cover - optional dependency fallback
    MapieRegressor = None

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_DIR = ROOT / "backend" / "app" / "ml" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = ARTIFACT_DIR / "forecast_model.joblib"


@dataclass
class ForecastArtifacts:
    model: HistGradientBoostingRegressor
    feature_columns: List[str]
    mapie: Optional[object]
    resid_std: float
    history: pd.DataFrame
    metrics: Dict[str, float]
    metadata: Dict[str, object]


def _train_model(df: pd.DataFrame, source_path: Path) -> ForecastArtifacts:
    feats = build_feature_frame(df)

    cutoff_1 = feats["date"].quantile(0.70)
    cutoff_2 = feats["date"].quantile(0.85)
    train = feats[feats["date"] <= cutoff_1]
    val = feats[(feats["date"] > cutoff_1) & (feats["date"] <= cutoff_2)]

    target = "units_sold"
    drop_cols = ["date", target]
    feature_cols = [c for c in feats.columns if c not in drop_cols]

    model = HistGradientBoostingRegressor(max_depth=6, learning_rate=0.08, max_iter=250, random_state=42)
    model.fit(train[feature_cols], train[target])

    mapie: Optional[object] = None
    resid_std: float
    if len(val) > 0 and MapieRegressor is not None:
        mapie = MapieRegressor(estimator=model, cv="split")
        mapie.fit(train[feature_cols], train[target], X_cal=val[feature_cols], y_cal=val[target])
        preds = model.predict(val[feature_cols])
        resid_std = float(np.std(val[target].values - preds))
    else:
        resid_std = float(np.std(train[target].values - model.predict(train[feature_cols])))

    if len(val) > 0:
        eval_pred = model.predict(val[feature_cols])
        mae = float(np.mean(np.abs(val[target].values - eval_pred)))
        rmse = float(np.sqrt(np.mean((val[target].values - eval_pred) ** 2)))
        denom = np.where(val[target].values > 0, val[target].values, np.nan)
        mape = float(np.nanmean(np.abs((val[target].values - eval_pred) / denom)) * 100.0)
    else:
        train_pred = model.predict(train[feature_cols])
        mae = float(np.mean(np.abs(train[target].values - train_pred)))
        rmse = float(np.sqrt(np.mean((train[target].values - train_pred) ** 2)))
        denom = np.where(train[target].values > 0, train[target].values, np.nan)
        mape = float(np.nanmean(np.abs((train[target].values - train_pred) / denom)) * 100.0)

    history = df.copy()
    params = {
        "model": "HistGradientBoostingRegressor",
        "max_depth": 6,
        "learning_rate": 0.08,
        "max_iter": 250,
        "features": len(feature_cols),
    }
    metrics = {
        "mae": float(mae),
        "rmse": float(rmse),
        "mape": float(np.clip(mape, 0.0, 100.0)),
        "val_resid_std": float(resid_std),
        "train_rows": float(len(train)),
        "val_rows": float(len(val)),
    }
    metadata = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "data_path": str(source_path),
        "dataset_rows": int(len(df)),
        "store_count": int(df["store_id"].nunique()),
        "product_count": int(df["product_id"].nunique()),
        "feature_count": int(len(feature_cols)),
        "supports_mapie": MapieRegressor is not None,
    }
    log_run("forecast_baseline", params=params, metrics=metrics)
    return ForecastArtifacts(
        model=model,
        feature_columns=feature_cols,
        mapie=mapie,
        resid_std=resid_std,
        history=history,
        metrics=metrics,
        metadata=metadata,
    )


def train_and_save(path: Optional[Path] = None) -> ForecastArtifacts:
    source_path = resolve_data_path(path or DEFAULT_DATA_PATH)
    df = load_groceries_sales(source_path)
    artifacts = _train_model(df, source_path)
    joblib.dump(artifacts, MODEL_PATH)
    logger.info("Saved forecast model to %s", MODEL_PATH)
    return artifacts


def load_or_train() -> ForecastArtifacts:
    current_data_path = str(resolve_data_path())
    if MODEL_PATH.exists():
        artifacts = joblib.load(MODEL_PATH)
        if not hasattr(artifacts, "metrics") or not hasattr(artifacts, "metadata"):
            logger.warning("Forecast artifact missing metrics/metadata. Re-training model.")
            return train_and_save()
        if str(artifacts.metadata.get("data_path")) != current_data_path:
            logger.warning("Forecast artifact data source changed from %s to %s. Re-training model.", artifacts.metadata.get("data_path"), current_data_path)
            return train_and_save()
        return artifacts
    logger.warning("Forecast model not found. Training a new model from %s", DEFAULT_DATA_PATH)
    return train_and_save()


def training_summary(artifacts: Optional[ForecastArtifacts] = None) -> Dict[str, object]:
    if artifacts is None:
        artifacts = load_or_train()
    return {
        "metrics": artifacts.metrics,
        "metadata": artifacts.metadata,
        "stores": sorted(artifacts.history["store_id"].astype(str).unique().tolist()),
        "products": sorted(artifacts.history["product_id"].astype(str).unique().tolist()),
    }


def _feature_row(
    store_id: str,
    product_id: str,
    date: pd.Timestamp,
    history: pd.DataFrame,
    future_units: List[float],
) -> Dict[str, float]:
    recent = history[(history["store_id"] == store_id) & (history["product_id"] == product_id)].sort_values("date")
    if recent.empty:
        recent = history.sort_values("date")

    last = recent.iloc[-1]
    series = recent["units_sold"].tolist() + future_units

    def lag(idx: int) -> float:
        return series[-idx] if len(series) >= idx else series[-1]

    lag_1 = lag(1)
    lag_7 = lag(7)
    lag_14 = lag(14)
    roll_7 = float(np.mean(series[-7:])) if len(series) >= 7 else float(np.mean(series))

    row: Dict[str, float] = {
        "store_id": store_id,
        "product_id": product_id,
        "dow": float(date.dayofweek),
        "month": float(date.month),
        "day": float(date.day),
        "price": float(last["price"]),
        "discount": float(last["discount"]),
        "competitor_price": float(last["competitor_price"]),
        "holiday": 0.0,
        "lag_1": float(lag_1),
        "lag_7": float(lag_7),
        "lag_14": float(lag_14),
        "roll_7": float(roll_7),
    }

    row["seasonality"] = last["seasonality"]
    row["weather"] = last["weather"]
    return row


def _pick_product(history: pd.DataFrame, store_id: str) -> str:
    store_hist = history[history["store_id"] == store_id]
    if store_hist.empty:
        return history["product_id"].iloc[-1]
    ranked = store_hist.groupby("product_id")["units_sold"].sum().sort_values(ascending=False)
    return ranked.index[0]


def _predict_row(artifacts: ForecastArtifacts, row_frame: pd.DataFrame) -> Dict[str, float]:
    pred = float(artifacts.model.predict(row_frame)[0])
    if artifacts.mapie is not None:
        y_pred, y_int = artifacts.mapie.predict(row_frame, alpha=0.05)
        lower = float(y_int[0, 0, 0])
        upper = float(y_int[0, 1, 0])
    else:
        interval = 1.96 * artifacts.resid_std
        lower = pred - interval
        upper = pred + interval
    return {"predicted": pred, "lower": lower, "upper": upper}


def _gnn_adjustment(
    history: pd.DataFrame,
    store_id: str,
    product_id: str,
    base_pred: float,
    k: int = 5,
    alpha: float = 0.1,
) -> float:
    sims = most_similar(product_id, k=k)
    if not sims:
        return base_pred

    store_hist = history[history["store_id"] == store_id]
    if store_hist.empty:
        store_hist = history

    target_mean = store_hist[store_hist["product_id"] == product_id]["units_sold"].mean()
    if not np.isfinite(target_mean) or target_mean <= 0:
        return base_pred

    weighted_means: List[float] = []
    weights: List[float] = []
    for pid, sim in sims:
        mean_val = store_hist[store_hist["product_id"] == pid]["units_sold"].mean()
        if not np.isfinite(mean_val):
            continue
        weights.append(max(0.0, sim))
        weighted_means.append(mean_val)

    if not weights or sum(weights) == 0:
        return base_pred

    neighbor_mean = float(np.average(weighted_means, weights=weights))
    ratio = neighbor_mean / target_mean
    adj = base_pred * (1.0 + alpha * (ratio - 1.0))
    return max(0.0, adj)


def forecast(
    store_id: str,
    horizon: int = 30,
    product_id: Optional[str] = None,
    gnn_adjust: bool = True,
    artifacts: Optional[ForecastArtifacts] = None,
) -> List[Dict[str, float]]:
    if artifacts is None:
        artifacts = load_or_train()
    history = artifacts.history
    store_hist = history[history["store_id"] == store_id]
    if store_hist.empty:
        store_hist = history
        store_id = store_hist["store_id"].iloc[-1]

    if not product_id:
        product_id = _pick_product(store_hist, store_id)

    series_hist = store_hist[store_hist["product_id"] == product_id].sort_values("date")
    if series_hist.empty:
        series_hist = store_hist.sort_values("date")
        product_id = series_hist["product_id"].iloc[-1]

    last_date = series_hist["date"].iloc[-1]
    future_units: List[float] = []
    results: List[Dict[str, float]] = []

    for i in range(horizon):
        d = last_date + pd.Timedelta(days=i + 1)
        row = _feature_row(store_id, product_id, d, history, future_units)

        row_frame = pd.DataFrame([row])
        row_frame = pd.get_dummies(
            row_frame,
            columns=["seasonality", "weather", "store_id", "product_id"],
            prefix=["season", "weather", "store", "product"],
            dtype=float,
        )
        for col in artifacts.feature_columns:
            if col not in row_frame.columns:
                row_frame[col] = 0.0
        row_frame = row_frame[artifacts.feature_columns]

        pred_pack = _predict_row(artifacts, row_frame)
        pred = pred_pack["predicted"]
        if gnn_adjust:
            pred = _gnn_adjustment(history, store_id, product_id, pred)
        pred_pack["predicted"] = pred
        pred_pack["lower"] = max(0.0, pred_pack["lower"])
        pred_pack["upper"] = max(pred_pack["lower"], pred_pack["upper"])
        future_units.append(pred)

        results.append(
            {
                "date": d,
                "predicted": max(0.0, pred),
                "lowerBound": max(0.0, pred_pack["lower"]),
                "upperBound": max(0.0, pred_pack["upper"]),
            }
        )

    return results


def forecast_multi(
    store_id: str,
    product_id: Optional[str] = None,
    horizons: Optional[List[int]] = None,
    gnn_adjust: bool = True,
    artifacts: Optional[ForecastArtifacts] = None,
) -> Dict[int, List[Dict[str, float]]]:
    horizons = horizons or [7, 14, 30]
    return {h: forecast(store_id, horizon=h, product_id=product_id, gnn_adjust=gnn_adjust, artifacts=artifacts) for h in horizons}


def recent_actuals(store_id: str, product_id: Optional[str], days: int = 10, artifacts: Optional[ForecastArtifacts] = None) -> List[Dict[str, float]]:
    if artifacts is None:
        artifacts = load_or_train()
    history = artifacts.history
    store_hist = history[history["store_id"] == store_id]
    if store_hist.empty:
        store_hist = history
        store_id = store_hist["store_id"].iloc[-1]

    if not product_id:
        product_id = _pick_product(store_hist, store_id)

    series_hist = store_hist[store_hist["product_id"] == product_id].sort_values("date")
    if series_hist.empty:
        series_hist = store_hist.sort_values("date")
    tail = series_hist.tail(days)
    return [
        {"date": d.to_pydatetime(), "actual": float(v)}
        for d, v in zip(tail["date"].tolist(), tail["units_sold"].tolist())
    ]
