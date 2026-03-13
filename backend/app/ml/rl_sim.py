from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

import numpy as np


@dataclass
class SimConfig:
    holding_cost: float = 0.15
    stockout_cost: float = 1.5
    max_inventory: float = 5000.0
    lead_time_days: int = 1
    demand_sigma: float = 0.1


def _require_simpy() -> None:
    try:
        import simpy  # noqa: F401
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "SimPy not installed. Install:\n"
            "  pip install -r backend/requirements-rl.txt\n"
            "Then re-run."
        ) from exc


def simulate_policy(
    demand_series: np.ndarray,
    policy_fn: Callable[[float, float], float],
    config: SimConfig | None = None,
) -> Dict[str, float]:
    _require_simpy()
    import simpy

    cfg = config or SimConfig()
    env = simpy.Environment()
    inventory = float(np.clip(demand_series.mean() * 7, 0, cfg.max_inventory))
    holding_cost = 0.0
    stockout_cost = 0.0
    total_orders = 0.0

    pending_orders: List[Dict[str, float]] = []

    def supplier():
        nonlocal inventory
        while True:
            now = int(env.now)
            arrivals = [o for o in pending_orders if o["arrival"] == now]
            for o in arrivals:
                inventory = min(cfg.max_inventory, inventory + o["qty"])
            pending_orders[:] = [o for o in pending_orders if o["arrival"] != now]
            yield env.timeout(1)

    def store():
        nonlocal inventory, holding_cost, stockout_cost, total_orders
        for t in range(len(demand_series)):
            mean_demand = float(demand_series.mean())
            order_qty = max(0.0, policy_fn(inventory, mean_demand))
            if order_qty > 0:
                pending_orders.append({"arrival": int(env.now) + cfg.lead_time_days, "qty": order_qty})
                total_orders += order_qty

            demand = float(demand_series[t])
            noise = np.random.normal(0.0, cfg.demand_sigma * max(demand, 1.0))
            demand = max(0.0, demand + noise)

            sold = min(inventory, demand)
            inventory -= sold
            stockout = max(0.0, demand - sold)
            holding_cost += inventory * cfg.holding_cost
            stockout_cost += stockout * cfg.stockout_cost
            yield env.timeout(1)

    env.process(supplier())
    env.process(store())
    env.run()

    return {
        "holding_cost": float(holding_cost),
        "stockout_cost": float(stockout_cost),
        "total_cost": float(holding_cost + stockout_cost),
        "total_orders": float(total_orders),
    }
