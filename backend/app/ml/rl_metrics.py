from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[3]
META_PATH = ROOT / "backend" / "app" / "ml" / "artifacts" / "rl_policy_meta.json"


def load_rl_metrics() -> Dict[str, float]:
    if not META_PATH.exists():
        return {"rl_total_cost": 0.0, "baseline_total_cost": 0.0}
    try:
        data = json.loads(META_PATH.read_text())
        return {
            "rl_total_cost": float(data.get("rl_total_cost", 0.0)),
            "baseline_total_cost": float(data.get("baseline_total_cost", 0.0)),
        }
    except Exception:
        return {"rl_total_cost": 0.0, "baseline_total_cost": 0.0}
