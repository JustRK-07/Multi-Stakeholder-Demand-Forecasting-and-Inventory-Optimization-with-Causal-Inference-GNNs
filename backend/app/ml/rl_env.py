from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np


@dataclass
class InventoryConfig:
    holding_cost: float = 0.15
    stockout_cost: float = 1.5
    max_inventory: float = 5000.0
    lead_time_days: int = 1


class InventoryEnv:
    """Minimal inventory environment for one SKU."""

    def __init__(self, demand_series: np.ndarray, config: InventoryConfig | None = None) -> None:
        self.config = config or InventoryConfig()
        self.demand_series = demand_series.astype(float)
        self.t = 0
        self.inventory = float(np.clip(demand_series.mean() * 7, 0, self.config.max_inventory))

    def reset(self) -> np.ndarray:
        self.t = 0
        self.inventory = float(np.clip(self.demand_series.mean() * 7, 0, self.config.max_inventory))
        return self._obs()

    def _obs(self) -> np.ndarray:
        mean_demand = float(self.demand_series.mean())
        return np.array([self.inventory, mean_demand], dtype=np.float32)

    def step(self, action: float) -> Tuple[np.ndarray, float, bool, Dict[str, float]]:
        # action in [0,1] scales target replenishment
        mean_demand = float(self.demand_series.mean())
        target = mean_demand * 7
        order_qty = np.clip(action, 0.0, 1.0) * max(0.0, target - self.inventory)
        self.inventory = min(self.config.max_inventory, self.inventory + order_qty)

        demand = float(self.demand_series[self.t])
        sold = min(self.inventory, demand)
        self.inventory -= sold

        stockout = max(0.0, demand - sold)
        holding = self.inventory
        reward = -(self.config.stockout_cost * stockout + self.config.holding_cost * holding)

        self.t += 1
        done = self.t >= len(self.demand_series)
        return self._obs(), reward, done, {"order_qty": float(order_qty), "stockout": float(stockout)}
