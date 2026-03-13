from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
META_PATH = ROOT / "backend" / "app" / "ml" / "artifacts" / "product_gnn_meta.json"


@lru_cache(maxsize=1)
def _load_meta() -> Optional[Dict[str, object]]:
    if not META_PATH.exists():
        return None
    try:
        return json.loads(META_PATH.read_text())
    except Exception:
        return None


def load_embeddings() -> Dict[str, np.ndarray]:
    meta = _load_meta()
    if not meta:
        return {}
    product_ids = meta.get("product_ids", [])
    embeddings = meta.get("embeddings", [])
    if not product_ids or not embeddings:
        return {}
    return {pid: np.array(vec, dtype=float) for pid, vec in zip(product_ids, embeddings)}


def get_embedding(product_id: str) -> Optional[np.ndarray]:
    embs = load_embeddings()
    return embs.get(product_id)


def most_similar(product_id: str, k: int = 5) -> List[Tuple[str, float]]:
    embs = load_embeddings()
    if product_id not in embs:
        return []
    target = embs[product_id]
    sims: List[Tuple[str, float]] = []
    t_norm = np.linalg.norm(target) + 1e-9
    for pid, vec in embs.items():
        if pid == product_id:
            continue
        sim = float(np.dot(target, vec) / (t_norm * (np.linalg.norm(vec) + 1e-9)))
        sims.append((pid, sim))
    sims.sort(key=lambda x: x[1], reverse=True)
    return sims[:k]
