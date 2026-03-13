from __future__ import annotations

from typing import List, Dict

import numpy as np

from .data import DEFAULT_DATA_PATH, load_groceries_sales


def simulate_federated_rounds(rounds: int = 7) -> List[Dict[str, float]]:
    df = load_groceries_sales(DEFAULT_DATA_PATH)
    base = 0.78 + min(0.08, np.log1p(len(df)) / 100)
    rng = np.random.default_rng(42)
    results: List[Dict[str, float]] = []
    for r in range(1, rounds + 1):
        improvement = 0.02 * (1 - np.exp(-r / 3.0))
        noise = float(rng.normal(0, 0.003))
        global_acc = min(0.99, base + improvement + noise)
        local_acc = min(0.99, global_acc - 0.01 + float(rng.normal(0, 0.004)))
        privacy = max(0.5, 1.0 - r * 0.06)
        results.append(
            {
                "round": r,
                "globalAccuracy": round(global_acc * 100, 1),
                "localAccuracy": round(local_acc * 100, 1),
                "privacyBudget": round(privacy, 2),
            }
        )
    return results
