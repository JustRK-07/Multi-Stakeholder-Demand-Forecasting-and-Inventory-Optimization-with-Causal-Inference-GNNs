from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .data import load_groceries_sales

ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_DIR = ROOT / "backend" / "app" / "ml" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
META_PATH = ARTIFACT_DIR / "rl_policy_meta.json"


def _series_frame(store_id: Optional[str] = None) -> pd.DataFrame:
    df = load_groceries_sales()
    if store_id:
        store_df = df[df["store_id"] == str(store_id)]
        if not store_df.empty:
            return store_df
    return df


def _policy_order_qty(
    inventory: float,
    recent_demand: np.ndarray,
    *,
    use_rl: bool,
    lead_time_days: int = 1,
) -> float:
    mean_demand = float(np.mean(recent_demand)) if len(recent_demand) else 0.0
    volatility = float(np.std(recent_demand) / max(mean_demand, 1.0)) if len(recent_demand) else 0.0
    safety_factor = 1.0 + min(0.75, volatility)

    if use_rl:
        target_days = 5.0 + lead_time_days + min(2.0, volatility * 3.0)
    else:
        target_days = 7.0 + lead_time_days

    target_stock = mean_demand * target_days * safety_factor
    if use_rl:
        target_stock *= 0.92
    return max(0.0, target_stock - inventory)


def simulate_inventory_policy(
    demand_series: np.ndarray,
    *,
    use_rl: bool,
    holding_cost: float = 0.15,
    stockout_cost: float = 1.5,
    lead_time_days: int = 1,
    initial_inventory_days: float = 7.0,
) -> Dict[str, object]:
    demand_series = np.asarray(demand_series, dtype=float)
    if demand_series.size == 0:
        return {
            "total_cost": 0.0,
            "holding_cost": 0.0,
            "stockout_cost": 0.0,
            "service_level": 100.0,
            "average_inventory": 0.0,
            "total_orders": 0.0,
            "reward_curve": [],
            "daily": [],
        }

    mean_demand = float(np.mean(demand_series))
    inventory = max(0.0, mean_demand * initial_inventory_days)
    pipeline: List[Tuple[int, float]] = []
    holding_total = 0.0
    stockout_total = 0.0
    total_orders = 0.0
    total_demand = 0.0
    total_fulfilled = 0.0
    inventory_trace: List[float] = []
    reward_curve: List[Dict[str, float]] = []
    daily: List[Dict[str, float]] = []

    for t, demand in enumerate(demand_series):
        arrivals = sum(qty for due, qty in pipeline if due == t)
        inventory += arrivals
        pipeline = [(due, qty) for due, qty in pipeline if due != t]

        start_inventory = inventory
        lookback_start = max(0, t - 7)
        recent = demand_series[lookback_start:t] if t > 0 else demand_series[:1]
        order_qty = _policy_order_qty(inventory, recent, use_rl=use_rl, lead_time_days=lead_time_days)
        if order_qty > 0:
            pipeline.append((t + lead_time_days, float(order_qty)))
            total_orders += float(order_qty)

        sold = min(inventory, demand)
        inventory -= sold
        stockout = max(0.0, float(demand - sold))
        hold_cost = inventory * holding_cost
        shortage_cost = stockout * stockout_cost
        holding_total += hold_cost
        stockout_total += shortage_cost
        total_demand += float(demand)
        total_fulfilled += float(sold)
        inventory_trace.append(inventory)
        reward_curve.append(
            {
                "episode": t + 1,
                "reward": round(-(hold_cost + shortage_cost), 2),
            }
        )
        daily.append(
            {
                "day": t + 1,
                "startInventory": round(start_inventory, 2),
                "demand": round(float(demand), 2),
                "ordered": round(float(order_qty), 2),
                "endingInventory": round(inventory, 2),
                "stockout": round(stockout, 2),
            }
        )

    service_level = (total_fulfilled / total_demand * 100.0) if total_demand > 0 else 100.0
    return {
        "total_cost": float(holding_total + stockout_total),
        "holding_cost": float(holding_total),
        "stockout_cost": float(stockout_total),
        "service_level": float(service_level),
        "average_inventory": float(np.mean(inventory_trace)) if inventory_trace else 0.0,
        "total_orders": float(total_orders),
        "reward_curve": reward_curve,
        "daily": daily,
    }


def _aggregate_series_metrics(df: pd.DataFrame) -> Dict[str, object]:
    top_series = []
    for (store_id, product_id), group in df.groupby(["store_id", "product_id"]):
        ordered = group.sort_values("date")
        demand = ordered["units_sold"].to_numpy(dtype=float)
        if len(demand) < 10:
            continue
        top_series.append((store_id, product_id, float(demand.sum()), demand))
    top_series.sort(key=lambda item: item[2], reverse=True)
    top_series = top_series[:8]

    if not top_series:
        return {
            "rl_total_cost": 0.0,
            "baseline_total_cost": 0.0,
            "cost_delta": 0.0,
            "service_level_rl": 100.0,
            "service_level_baseline": 100.0,
            "average_inventory_rl": 0.0,
            "average_inventory_baseline": 0.0,
            "reward_curve": [],
            "scenario_defaults": {},
            "series": [],
        }

    rl_total = baseline_total = 0.0
    rl_service = baseline_service = 0.0
    rl_inventory = baseline_inventory = 0.0
    combined_rewards: List[Dict[str, float]] = []
    series_rows: List[Dict[str, object]] = []

    for idx, (store_id, product_id, _, demand) in enumerate(top_series, start=1):
        rl_metrics = simulate_inventory_policy(demand, use_rl=True)
        base_metrics = simulate_inventory_policy(demand, use_rl=False)
        rl_total += float(rl_metrics["total_cost"])
        baseline_total += float(base_metrics["total_cost"])
        rl_service += float(rl_metrics["service_level"])
        baseline_service += float(base_metrics["service_level"])
        rl_inventory += float(rl_metrics["average_inventory"])
        baseline_inventory += float(base_metrics["average_inventory"])
        series_rows.append(
            {
                "store_id": store_id,
                "product_id": product_id,
                "rl_total_cost": round(float(rl_metrics["total_cost"]), 2),
                "baseline_total_cost": round(float(base_metrics["total_cost"]), 2),
                "savings": round(float(base_metrics["total_cost"] - rl_metrics["total_cost"]), 2),
                "service_level_rl": round(float(rl_metrics["service_level"]), 2),
                "service_level_baseline": round(float(base_metrics["service_level"]), 2),
            }
        )
        rewards = rl_metrics["reward_curve"]
        base_rewards = base_metrics["reward_curve"]
        for step, (rl_reward, base_reward) in enumerate(zip(rewards, base_rewards), start=1):
            if len(combined_rewards) < step:
                combined_rewards.append({"episode": step, "reward": 0.0, "baseline": 0.0})
            combined_rewards[step - 1]["reward"] += float(rl_reward["reward"])
            combined_rewards[step - 1]["baseline"] += float(base_reward["reward"])

    count = float(len(top_series))
    reward_curve = [
        {
            "episode": row["episode"],
            "reward": round(row["reward"] / count, 2),
            "baseline": round(row["baseline"] / count, 2),
        }
        for row in combined_rewards
    ]
    return {
        "rl_total_cost": round(rl_total, 2),
        "baseline_total_cost": round(baseline_total, 2),
        "cost_delta": round(baseline_total - rl_total, 2),
        "service_level_rl": round(rl_service / count, 2),
        "service_level_baseline": round(baseline_service / count, 2),
        "average_inventory_rl": round(rl_inventory / count, 2),
        "average_inventory_baseline": round(baseline_inventory / count, 2),
        "reward_curve": reward_curve,
        "scenario_defaults": {
            "store_id": top_series[0][0],
            "product_id": top_series[0][1],
            "periods": min(14, len(top_series[0][3])),
        },
        "series": series_rows,
    }


def evaluate_policies(store_id: Optional[str] = None, refresh: bool = False) -> Dict[str, object]:
    if META_PATH.exists() and not refresh and store_id is None:
        try:
            return json.loads(META_PATH.read_text())
        except Exception:
            pass

    df = _series_frame(store_id)
    metrics = _aggregate_series_metrics(df)
    metrics["evaluated_store_id"] = store_id
    if store_id is None:
        META_PATH.write_text(json.dumps(metrics, indent=2))
    return metrics


def scenario_simulation(
    *,
    store_id: Optional[str] = None,
    product_id: Optional[str] = None,
    periods: int = 14,
    demand_scale: float = 1.0,
    lead_time_days: int = 1,
    holding_cost: float = 0.15,
    stockout_cost: float = 1.5,
) -> Dict[str, object]:
    df = _series_frame(store_id)
    if product_id:
        product_df = df[df["product_id"] == str(product_id)]
        if not product_df.empty:
            df = product_df

    grouped = []
    for (group_store, group_product), group in df.groupby(["store_id", "product_id"]):
        demand = group.sort_values("date")["units_sold"].to_numpy(dtype=float)
        if len(demand) >= 5:
            grouped.append((group_store, group_product, float(demand.sum()), demand))
    grouped.sort(key=lambda item: item[2], reverse=True)
    if not grouped:
        return {"rl": {}, "baseline": {}, "daily": [], "store_id": store_id, "product_id": product_id}

    chosen_store, chosen_product, _, demand = grouped[0]
    demand = demand[:periods] * max(demand_scale, 0.1)
    rl_metrics = simulate_inventory_policy(
        demand,
        use_rl=True,
        lead_time_days=lead_time_days,
        holding_cost=holding_cost,
        stockout_cost=stockout_cost,
    )
    base_metrics = simulate_inventory_policy(
        demand,
        use_rl=False,
        lead_time_days=lead_time_days,
        holding_cost=holding_cost,
        stockout_cost=stockout_cost,
    )
    daily = []
    for rl_day, base_day in zip(rl_metrics["daily"], base_metrics["daily"]):
        daily.append(
            {
                "day": rl_day["day"],
                "demand": rl_day["demand"],
                "rlOrdered": rl_day["ordered"],
                "baselineOrdered": base_day["ordered"],
                "rlStockout": rl_day["stockout"],
                "baselineStockout": base_day["stockout"],
                "rlEndingInventory": rl_day["endingInventory"],
                "baselineEndingInventory": base_day["endingInventory"],
            }
        )
    return {
        "store_id": chosen_store,
        "product_id": chosen_product,
        "rl": {k: v for k, v in rl_metrics.items() if k not in {"reward_curve", "daily"}},
        "baseline": {k: v for k, v in base_metrics.items() if k not in {"reward_curve", "daily"}},
        "daily": daily,
        "savings": round(float(base_metrics["total_cost"] - rl_metrics["total_cost"]), 2),
    }


def recommendation_rows(store_id: Optional[str] = None, limit: int = 4) -> List[Dict[str, object]]:
    df = _series_frame(store_id)
    latest_date = df["date"].max()
    latest = df[df["date"] == latest_date].copy()
    rows: List[Dict[str, object]] = []

    for _, row in latest.iterrows():
        sku = str(row["product_id"])
        sku_hist = df[(df["store_id"] == row["store_id"]) & (df["product_id"] == sku)].sort_values("date")
        demand = sku_hist["units_sold"].to_numpy(dtype=float)
        if len(demand) == 0:
            continue
        inventory = float(row["inventory_level"])
        recent = demand[-7:] if len(demand) >= 7 else demand
        rl_order = _policy_order_qty(inventory, recent, use_rl=True)
        base_order = _policy_order_qty(inventory, recent, use_rl=False)
        savings = max(0.0, base_order - rl_order) * max(float(np.mean(recent)) * 0.5, 1.0)
        days_until_stockout = inventory / max(float(np.mean(recent)), 1.0)
        urgency = "critical" if days_until_stockout <= 2 else "high" if days_until_stockout <= 5 else "medium" if days_until_stockout <= 10 else "low"
        rows.append(
            {
                "store_id": str(row["store_id"]),
                "sku": sku,
                "rl_order_qty": round(float(rl_order)),
                "baseline_order_qty": round(float(base_order)),
                "confidence": int(round(75 + min(20, np.std(recent)))),
                "expected_saving_value": round(float(savings), 2),
                "urgency": urgency,
            }
        )

    severity = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    rows.sort(key=lambda item: (severity[item["urgency"]], -item["expected_saving_value"]))
    return rows[:limit]
