from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from .data import load_groceries_sales
from .graph_model import _build_graph_from_data

ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_DIR = ROOT / "backend" / "app" / "ml" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
META_PATH = ARTIFACT_DIR / "product_gnn_meta.json"


def _node_feature_frame(df: pd.DataFrame, product_ids: List[str]) -> pd.DataFrame:
    agg = (
        df[df["product_id"].isin(product_ids)]
        .groupby("product_id", as_index=False)
        .agg(
            mean_units=("units_sold", "mean"),
            std_units=("units_sold", "std"),
            mean_price=("price", "mean"),
            mean_discount=("discount", "mean"),
            promo_rate=("holiday", "mean"),
        )
        .fillna(0.0)
    )
    return agg.set_index("product_id").reindex(product_ids).fillna(0.0)


def _adjacency_matrix(product_ids: List[str], edges: List[Dict[str, object]]) -> np.ndarray:
    index = {pid: i for i, pid in enumerate(product_ids)}
    adj = np.eye(len(product_ids), dtype=float)
    for edge in edges:
        src = index.get(str(edge["from_product"]))
        dst = index.get(str(edge["to_product"]))
        if src is None or dst is None:
            continue
        weight = float(edge["weight"])
        signed = weight if edge["type"] == "complement" else -weight
        adj[src, dst] = signed
        adj[dst, src] = signed
    return adj


def train_gnn(top_n: int = 40, min_corr: float = 0.25, embedding_dim: int = 8) -> Dict[str, object]:
    df = load_groceries_sales()
    graph = _build_graph_from_data(df, top_n=top_n, min_corr=min_corr)
    product_ids = [str(node["product_id"]) for node in graph.nodes]
    if not product_ids:
        payload = {"product_ids": [], "embeddings": [], "graph_stats": {"nodes": 0, "edges": 0}}
        META_PATH.write_text(json.dumps(payload, indent=2))
        return payload

    feature_df = _node_feature_frame(df, product_ids)
    features = feature_df.to_numpy(dtype=float)
    features = (features - features.mean(axis=0)) / np.maximum(features.std(axis=0), 1e-9)

    adjacency = _adjacency_matrix(product_ids, graph.edges)
    u, s, _ = np.linalg.svd(adjacency, full_matrices=False)
    spectral_dim = min(max(2, embedding_dim // 2), u.shape[1])
    spectral = u[:, :spectral_dim] * s[:spectral_dim]

    combined = np.hstack([features, spectral])
    combined_dim = min(embedding_dim, combined.shape[1])
    if combined_dim < combined.shape[1]:
        u2, s2, _ = np.linalg.svd(combined, full_matrices=False)
        embeddings = u2[:, :combined_dim] * s2[:combined_dim]
    else:
        embeddings = combined

    payload = {
        "product_ids": product_ids,
        "embeddings": embeddings.astype(float).tolist(),
        "top_n": top_n,
        "min_corr": min_corr,
        "embedding_dim": int(embeddings.shape[1]),
        "graph_stats": {"nodes": len(graph.nodes), "edges": len(graph.edges)},
        "feature_columns": feature_df.columns.tolist(),
    }
    META_PATH.write_text(json.dumps(payload, indent=2))
    return payload


def main() -> None:
    print(train_gnn())


if __name__ == "__main__":
    main()
