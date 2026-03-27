from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[3]
META_PATH = ROOT / "backend" / "app" / "ml" / "artifacts" / "rl_policy_meta.json"


from .rl_analysis import evaluate_policies


def load_rl_metrics(refresh: bool = False) -> Dict[str, float]:
    if not META_PATH.exists() or refresh:
        data = evaluate_policies(refresh=True)
    else:
        try:
            data = json.loads(META_PATH.read_text())
        except Exception:
            data = evaluate_policies(refresh=True)
    return {
        "rl_total_cost": float(data.get("rl_total_cost", 0.0)),
        "baseline_total_cost": float(data.get("baseline_total_cost", 0.0)),
        "cost_delta": float(data.get("cost_delta", 0.0)),
        "service_level_rl": float(data.get("service_level_rl", 0.0)),
        "service_level_baseline": float(data.get("service_level_baseline", 0.0)),
        "average_inventory_rl": float(data.get("average_inventory_rl", 0.0)),
        "average_inventory_baseline": float(data.get("average_inventory_baseline", 0.0)),
    }
