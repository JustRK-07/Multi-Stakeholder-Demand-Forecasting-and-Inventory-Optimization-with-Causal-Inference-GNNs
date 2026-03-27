from __future__ import annotations

from typing import Dict, List

import numpy as np

from .data import load_groceries_sales, resolve_data_path


def _store_validation_accuracy(df) -> Dict[str, float]:
    grouped = (
        df.groupby(["store_id", "date"], as_index=False)["units_sold"]
        .sum()
        .sort_values(["store_id", "date"])
    )
    accuracy_by_store: Dict[str, float] = {}
    for store_id, group in grouped.groupby("store_id", sort=False):
        series = group["units_sold"].astype(float)
        if len(series) < 15:
            continue
        pred = series.shift(1).rolling(7, min_periods=3).mean()
        valid = pred.notna()
        if valid.sum() < 7:
            continue
        actual = series[valid].to_numpy()
        forecast = pred[valid].to_numpy()
        denom = np.where(actual > 0, actual, np.nan)
        mape = float(np.nanmean(np.abs((actual - forecast) / denom)) * 100.0)
        accuracy = float(np.clip(100.0 - mape, 60.0, 99.0))
        accuracy_by_store[str(store_id)] = accuracy
    return accuracy_by_store


def simulate_federated_rounds(rounds: int = 7) -> List[Dict[str, float]]:
    df = load_groceries_sales(resolve_data_path())
    store_scores = _store_validation_accuracy(df)
    if not store_scores:
        return []

    stores = sorted(store_scores.items(), key=lambda item: item[1], reverse=True)
    total_rounds = min(max(rounds, 3), max(len(stores), 3))
    sample_size = max(2, min(4, len(stores)))
    results: List[Dict[str, float]] = []
    for r in range(1, total_rounds + 1):
        start = (r - 1) % len(stores)
        participants = [stores[(start + idx) % len(stores)] for idx in range(sample_size)]
        local_acc = float(np.mean([score for _, score in participants]))
        participation_ratio = r / total_rounds
        blended_acc = float(np.mean([score for _, score in stores[: max(sample_size, int(np.ceil(len(stores) * participation_ratio)))]]))
        global_acc = min(99.0, blended_acc + 0.4 * participation_ratio)
        privacy = max(0.55, 1.25 - 0.08 * r)
        results.append(
            {
                "round": r,
                "globalAccuracy": round(global_acc, 1),
                "localAccuracy": round(local_acc, 1),
                "privacyBudget": round(privacy, 2),
                "participants": len(participants),
            }
        )
    return results
