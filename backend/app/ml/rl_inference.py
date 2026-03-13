from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .data import DEFAULT_DATA_PATH, load_groceries_sales

ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = ROOT / "backend" / "app" / "ml" / "artifacts" / "rl_policy.zip"


def _load_rl_model():
    if not MODEL_PATH.exists():
        return None
    try:
        from stable_baselines3 import PPO

        return PPO.load(MODEL_PATH)
    except Exception:
        return None


def _latest_inventory(df: pd.DataFrame, store_id: str) -> pd.DataFrame:
    store_df = df[df["store_id"] == store_id]
    if store_df.empty:
        store_df = df
    latest_date = store_df["date"].max()
    return store_df[store_df["date"] == latest_date]


def _urgency(days_until_stockout: float) -> str:
    if days_until_stockout <= 2:
        return "critical"
    if days_until_stockout <= 5:
        return "high"
    if days_until_stockout <= 10:
        return "medium"
    return "low"


def recommend_orders(store_id: Optional[str] = None, limit: int = 4, use_rl: bool = True) -> List[Dict[str, object]]:
    df = load_groceries_sales(DEFAULT_DATA_PATH)
    store_id = store_id or df["store_id"].iloc[0]

    latest = _latest_inventory(df, store_id)
    if latest.empty:
        return []

    model = _load_rl_model() if use_rl else None
    recs: List[Dict[str, object]] = []
    for _, row in latest.iterrows():
        product_id = row["product_id"]
        mean_demand = float(df[(df["store_id"] == store_id) & (df["product_id"] == product_id)]["units_sold"].mean())
        inventory = float(row.get("inventory_level", mean_demand * 7))
        target = mean_demand * 7
        base_order = max(0.0, target - inventory)

        if model is not None:
            obs = np.array([[inventory, mean_demand]], dtype=np.float32)
            action, _ = model.predict(obs, deterministic=True)
            base_order = float(np.clip(action[0], 0.0, 1.0) * max(0.0, target - inventory))

        days_until_stockout = inventory / max(mean_demand, 1.0)
        recs.append(
            {
                "sku": product_id,
                "action": f"Order {int(round(base_order))} units",
                "confidence": int(round(70 + min(25, mean_demand))),
                "expectedSaving": f"${int(round(base_order * 2.5))}",
                "urgency": _urgency(days_until_stockout),
            }
        )

    recs.sort(key=lambda r: ["critical", "high", "medium", "low"].index(r["urgency"]))
    return recs[:limit]
