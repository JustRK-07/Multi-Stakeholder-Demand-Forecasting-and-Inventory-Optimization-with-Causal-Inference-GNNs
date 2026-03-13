from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from .data import DEFAULT_DATA_PATH, load_groceries_sales

ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_DIR = ROOT / "backend" / "app" / "ml" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOT_PATH = ARTIFACT_DIR / "drift_snapshot.csv"


def export_snapshot(path: Optional[Path] = None, rows: int = 5000) -> Path:
    df = load_groceries_sales(DEFAULT_DATA_PATH)
    df = df.sort_values("date").tail(rows)
    out = path or SNAPSHOT_PATH
    df.to_csv(out, index=False)
    return out
