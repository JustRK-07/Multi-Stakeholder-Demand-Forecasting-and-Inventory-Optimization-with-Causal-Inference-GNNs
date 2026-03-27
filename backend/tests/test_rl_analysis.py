from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ml.rl_analysis import evaluate_policies, recommendation_rows, scenario_simulation, simulate_inventory_policy  # noqa: E402


def test_simulate_inventory_policy_returns_costs():
    result = simulate_inventory_policy([10, 12, 11, 9, 14, 8, 10], use_rl=True)
    assert result["total_cost"] >= 0
    assert "reward_curve" in result
    assert len(result["daily"]) == 7


def test_evaluate_policies_returns_comparison_metrics():
    metrics = evaluate_policies(refresh=True)
    assert {"rl_total_cost", "baseline_total_cost", "reward_curve", "series"} <= set(metrics.keys())
    assert len(metrics["reward_curve"]) > 0


def test_scenario_simulation_returns_daily_comparison():
    result = scenario_simulation(periods=10, demand_scale=1.1)
    assert {"rl", "baseline", "daily", "savings"} <= set(result.keys())
    assert len(result["daily"]) > 0


def test_recommendation_rows_returns_ranked_actions():
    rows = recommendation_rows(limit=3)
    assert len(rows) <= 3
    assert rows
    assert {"sku", "rl_order_qty", "baseline_order_qty", "expected_saving_value", "urgency"} <= set(rows[0].keys())
