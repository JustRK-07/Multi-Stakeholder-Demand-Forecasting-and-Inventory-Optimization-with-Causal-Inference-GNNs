from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .ml.data import load_groceries_sales


STORE_META: Dict[str, Dict[str, Any]] = {
    "S001": {"name": "Store S001", "lat": 40.7128, "lng": -74.0060},
    "S002": {"name": "Store S002", "lat": 40.7589, "lng": -73.9851},
    "S003": {"name": "Store S003", "lat": 40.6413, "lng": -73.7781},
    "S004": {"name": "Store S004", "lat": 40.6892, "lng": -74.0445},
    "S005": {"name": "Store S005", "lat": 40.7549, "lng": -73.9840},
}


@dataclass
class MetricCard:
    title: str
    value: str
    change: float
    trend: str


def _filtered_df(store_id: Optional[str] = None) -> pd.DataFrame:
    df = load_groceries_sales()
    if store_id:
        store_df = df[df["store_id"] == str(store_id)]
        if not store_df.empty:
            return store_df
    return df


def _date_window(df: pd.DataFrame, days: int) -> pd.DataFrame:
    if df.empty:
        return df
    cutoff = df["date"].max() - pd.Timedelta(days=days - 1)
    return df[df["date"] >= cutoff]


def _format_day(d: pd.Timestamp) -> str:
    return d.strftime("%b %-d") if "%-d" in pd.Timestamp.now().strftime("%-d") else d.strftime("%b %d")


def _mean_abs_pct_error(actual: pd.Series, pred: pd.Series) -> float:
    mask = actual > 0
    if not mask.any():
        return 0.0
    return float((np.abs(actual[mask] - pred[mask]) / actual[mask]).mean() * 100.0)


def _change_and_trend(current: float, previous: float, higher_is_better: bool = True) -> tuple[float, str]:
    baseline = previous if abs(previous) > 1e-9 else 1.0
    pct_change = ((current - previous) / abs(baseline)) * 100.0
    favorable = pct_change >= 0 if higher_is_better else pct_change <= 0
    return abs(round(float(pct_change), 1)), "up" if favorable else "down"


def compute_kpis(store_id: Optional[str] = None, date_range: Optional[str] = None) -> List[Dict[str, Any]]:
    _ = date_range
    df = _filtered_df(store_id)
    if df.empty:
        return []

    recent = _date_window(df, 60).copy()
    midpoint = recent["date"].max() - pd.Timedelta(days=30)
    current = recent[recent["date"] > midpoint].copy()
    previous = recent[recent["date"] <= midpoint].copy()
    if previous.empty:
        previous = current

    daily = recent.groupby("date", as_index=False)["units_sold"].sum().sort_values("date")
    daily["lag_7"] = daily["units_sold"].shift(1).rolling(window=7, min_periods=1).mean()
    current_eval = daily[daily["date"] > midpoint].dropna(subset=["lag_7"])
    previous_eval = daily[daily["date"] <= midpoint].dropna(subset=["lag_7"])
    if current_eval.empty:
        current_eval = daily[daily["date"] > midpoint].copy()
        current_eval["lag_7"] = current_eval["units_sold"]
    if previous_eval.empty:
        previous_eval = daily[daily["date"] <= midpoint].copy()
        previous_eval["lag_7"] = previous_eval["units_sold"]

    current_mape = _mean_abs_pct_error(current_eval["units_sold"], current_eval["lag_7"])
    previous_mape = _mean_abs_pct_error(previous_eval["units_sold"], previous_eval["lag_7"])
    current_mape = min(current_mape, 100.0)
    previous_mape = min(previous_mape, 100.0)
    forecast_accuracy = max(0.0, 100.0 - current_mape)
    prev_accuracy = max(0.0, 100.0 - previous_mape)

    current_service = float((current["inventory_level"] >= current["units_sold"]).mean() * 100.0)
    previous_service = float((previous["inventory_level"] >= previous["units_sold"]).mean() * 100.0)

    avg_inventory = float(current["inventory_level"].mean()) or 1.0
    prev_avg_inventory = float(previous["inventory_level"].mean()) or 1.0
    current_turnover = float(current["units_sold"].sum() / avg_inventory)
    previous_turnover = float(previous["units_sold"].sum() / prev_avg_inventory)

    current_stockout = float((current["inventory_level"] <= current["units_sold"] * 0.25).mean() * 100.0)
    previous_stockout = float((previous["inventory_level"] <= previous["units_sold"] * 0.25).mean() * 100.0)

    current_fill = float((np.minimum(current["inventory_level"], current["units_sold"]).sum() / max(current["units_sold"].sum(), 1.0)) * 100.0)
    previous_fill = float((np.minimum(previous["inventory_level"], previous["units_sold"]).sum() / max(previous["units_sold"].sum(), 1.0)) * 100.0)

    accuracy_change, accuracy_trend = _change_and_trend(forecast_accuracy, prev_accuracy, higher_is_better=True)
    service_change, service_trend = _change_and_trend(current_service, previous_service, higher_is_better=True)
    turnover_change, turnover_trend = _change_and_trend(current_turnover, previous_turnover, higher_is_better=True)
    stockout_change, stockout_trend = _change_and_trend(current_stockout, previous_stockout, higher_is_better=False)
    fill_change, fill_trend = _change_and_trend(current_fill, previous_fill, higher_is_better=True)
    mape_change, mape_trend = _change_and_trend(current_mape, previous_mape, higher_is_better=False)

    cards = [
        MetricCard("Forecast Accuracy", f"{forecast_accuracy:.1f}%", accuracy_change, accuracy_trend),
        MetricCard("Service Level", f"{current_service:.1f}%", service_change, service_trend),
        MetricCard("Inventory Turnover", f"{current_turnover:.1f}x", turnover_change, turnover_trend),
        MetricCard("Stockout Rate", f"{current_stockout:.1f}%", stockout_change, stockout_trend),
        MetricCard("Order Fill Rate", f"{current_fill:.1f}%", fill_change, fill_trend),
        MetricCard("MAPE", f"{current_mape:.1f}%", mape_change, mape_trend),
    ]
    return [card.__dict__ for card in cards]


def compute_inventory_items(store_id: Optional[str] = None, risk_level: Optional[str] = None) -> List[Dict[str, Any]]:
    df = _filtered_df(store_id)
    if df.empty:
        return []

    latest_date = df["date"].max()
    latest = df[df["date"] == latest_date].copy()
    history = _date_window(df, 60)

    items: List[Dict[str, Any]] = []
    for _, row in latest.sort_values(["inventory_level", "product_id"]).iterrows():
        product_id = str(row["product_id"])
        product_hist = history[history["product_id"] == product_id]
        mean_demand = float(product_hist["units_sold"].mean()) if not product_hist.empty else float(row["units_sold"])
        mean_demand = max(mean_demand, 1.0)
        stock = int(round(float(row["inventory_level"])))
        capacity = int(round(max(float(product_hist["inventory_level"].max()) if not product_hist.empty else stock, stock * 1.2, stock + 50)))
        reorder_point = int(round(mean_demand * 5))
        days_of_supply = round(stock / mean_demand, 1)
        if days_of_supply <= 2:
            risk = "critical"
        elif days_of_supply <= 5:
            risk = "high"
        elif days_of_supply <= 10:
            risk = "medium"
        else:
            risk = "low"

        item = {
            "sku": product_id,
            "name": f"Product {product_id}",
            "stock": stock,
            "capacity": capacity,
            "reorderPoint": reorder_point,
            "daysOfSupply": days_of_supply,
            "risk": risk,
        }
        items.append(item)

    if risk_level:
        items = [item for item in items if item["risk"] == risk_level]
    severity = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    items.sort(key=lambda item: (severity[item["risk"]], item["daysOfSupply"], item["sku"]))
    return items


def compute_dashboard_summary(store_id: Optional[str] = None) -> Dict[str, Any]:
    df = _filtered_df(store_id)
    if df.empty:
        return {"salesTrend": [], "inventoryTrend": [], "alerts": []}

    recent = _date_window(df, 14)
    daily = (
        recent.groupby("date", as_index=False)
        .agg(sales=("units_sold", "sum"), level=("inventory_level", "sum"))
        .sort_values("date")
    )
    daily["demand"] = daily["sales"].rolling(window=3, min_periods=1).mean().round()

    sales_trend = [
        {"day": _format_day(row.date), "sales": int(round(row.sales)), "demand": int(round(row.demand))}
        for row in daily.itertuples()
    ]
    inventory_trend = [
        {"day": _format_day(row.date), "level": int(round(row.level))}
        for row in daily.itertuples()
    ]

    inventory_items = compute_inventory_items(store_id=store_id)
    alerts: List[Dict[str, str]] = []
    critical_items = inventory_items[:3]
    for item in critical_items:
        if item["risk"] in {"critical", "high"}:
            alerts.append(
                {
                    "severity": "high" if item["risk"] == "critical" else "medium",
                    "message": f"Stock risk detected for {item['sku']} with {item['daysOfSupply']} days of supply remaining.",
                }
            )

    promo_rate = float(recent["holiday"].mean() * 100.0)
    if promo_rate > 10.0:
        alerts.append(
            {
                "severity": "medium",
                "message": f"Promotion activity detected in {promo_rate:.1f}% of recent observations.",
            }
        )

    if not alerts:
        alerts.append({"severity": "low", "message": "No critical supply chain alerts in the recent window."})

    return {"salesTrend": sales_trend, "inventoryTrend": inventory_trend, "alerts": alerts[:4]}


def compute_stores() -> List[Dict[str, Any]]:
    df = load_groceries_sales()
    latest_date = df["date"].max()
    latest = df[df["date"] == latest_date]
    recent = _date_window(df, 30)

    stores: List[Dict[str, Any]] = []
    for idx, store_id in enumerate(sorted(df["store_id"].unique()), start=1):
        meta = STORE_META.get(store_id, {})
        store_recent = recent[recent["store_id"] == store_id]
        store_latest = latest[latest["store_id"] == store_id]
        demand = int(round(store_recent.groupby("date")["units_sold"].sum().mean())) if not store_recent.empty else 0
        service_level = float((store_recent["inventory_level"] >= store_recent["units_sold"]).mean() * 100.0) if not store_recent.empty else 0.0
        stock_penalty = float((store_latest["inventory_level"] <= store_latest["units_sold"] * 0.25).mean() * 10.0) if not store_latest.empty else 0.0
        performance = max(0.0, min(99.0, service_level - stock_penalty))
        stores.append(
            {
                "id": idx,
                "name": meta.get("name", f"Store {store_id}"),
                "lat": meta.get("lat", 0.0),
                "lng": meta.get("lng", 0.0),
                "demand": demand,
                "performance": int(round(performance)),
            }
        )
    return stores
