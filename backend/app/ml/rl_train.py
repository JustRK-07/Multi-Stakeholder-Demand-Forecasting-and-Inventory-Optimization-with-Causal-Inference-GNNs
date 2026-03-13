from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

from .data import DEFAULT_DATA_PATH, load_groceries_sales
from .rl_env import InventoryEnv
from .rl_sim import simulate_policy


def _require_rl() -> None:
    try:
        import gymnasium  # noqa: F401
        import stable_baselines3  # noqa: F401
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "RL dependencies not installed. Install CPU-only deps:\n"
            "  pip install -r backend/requirements-rl.txt\n"
            "Then re-run: python -m app.ml.rl_train"
        ) from exc


ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_DIR = ROOT / "backend" / "app" / "ml" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = ARTIFACT_DIR / "rl_policy.zip"
META_PATH = ARTIFACT_DIR / "rl_policy_meta.json"


def _build_series(df: pd.DataFrame) -> Dict[str, np.ndarray]:
    series = {}
    for (store_id, product_id), g in df.groupby(["store_id", "product_id"]):
        g = g.sort_values("date")
        key = f"{store_id}:{product_id}"
        series[key] = g["units_sold"].to_numpy(dtype=float)
    return series


def train_rl() -> None:
    _require_rl()
    import gymnasium as gym
    from stable_baselines3 import PPO

    df = load_groceries_sales(DEFAULT_DATA_PATH)
    series = _build_series(df)
    if not series:
        raise RuntimeError("No grocery series found to train RL.")

    # Train on the highest-volume SKU series
    key = max(series.items(), key=lambda kv: kv[1].sum())[0]
    demand = series[key]

    class GymWrapper(gym.Env):
        def __init__(self) -> None:
            self.env = InventoryEnv(demand)
            self.observation_space = gym.spaces.Box(low=0, high=np.inf, shape=(2,), dtype=np.float32)
            self.action_space = gym.spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32)

        def reset(self, *, seed: int | None = None, options: dict | None = None):
            _ = (seed, options)
            obs = self.env.reset()
            return obs, {}

        def step(self, action):
            obs, reward, done, info = self.env.step(float(action[0]))
            return obs, reward, done, False, info

    model = PPO("MlpPolicy", GymWrapper(), verbose=0, n_steps=256, batch_size=64)
    model.learn(total_timesteps=5000)
    model.save(MODEL_PATH)

    # Evaluate policy in SimPy simulator vs heuristic baseline.
    def rl_policy(inv: float, mean_demand: float) -> float:
        obs = np.array([[inv, mean_demand]], dtype=np.float32)
        action, _ = model.predict(obs, deterministic=True)
        target = mean_demand * 7
        return float(np.clip(action[0], 0.0, 1.0) * max(0.0, target - inv))

    def baseline_policy(inv: float, mean_demand: float) -> float:
        target = mean_demand * 7
        return max(0.0, target - inv)

    rl_metrics = simulate_policy(demand, rl_policy)
    base_metrics = simulate_policy(demand, baseline_policy)

    META_PATH.write_text(
        (
            '{'
            f'"series_key": "{key}", "timesteps": 5000, '
            f'"rl_total_cost": {rl_metrics["total_cost"]:.3f}, '
            f'"baseline_total_cost": {base_metrics["total_cost"]:.3f}'
            '}'
        )
    )


def main() -> None:
    train_rl()


if __name__ == "__main__":
    main()
