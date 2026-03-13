from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import networkx as nx
import numpy as np
import pandas as pd

from .data import DEFAULT_DATA_PATH, load_groceries_sales

ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_DIR = ROOT / "backend" / "app" / "ml" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
GRAPH_PATH = ARTIFACT_DIR / "product_graph.json"


@dataclass
class ProductGraph:
    nodes: List[Dict[str, object]]
    edges: List[Dict[str, object]]


def _build_graph_from_data(df: pd.DataFrame, top_n: int, min_corr: float) -> ProductGraph:
    totals = df.groupby("product_id")["units_sold"].sum().sort_values(ascending=False)
    products = totals.head(top_n).index.tolist()
    focus = df[df["product_id"].isin(products)]

    pivot = focus.pivot_table(index="date", columns="product_id", values="units_sold", aggfunc="sum").fillna(0.0)
    corr = pivot.corr()

    graph = nx.Graph()
    for pid in products:
        graph.add_node(pid)

    edges: List[Dict[str, object]] = []
    for i, a in enumerate(products):
        for b in products[i + 1 :]:
            c = corr.loc[a, b]
            if np.isnan(c) or abs(c) < min_corr:
                continue
            rel_type = "complement" if c >= 0 else "substitute"
            weight = float(abs(c))
            graph.add_edge(a, b, weight=weight, rel_type=rel_type)
            edges.append({"from": a, "to": b, "type": rel_type, "weight": round(weight, 3)})

    pos = nx.spring_layout(graph, seed=42, weight="weight")
    nodes: List[Dict[str, object]] = []
    for idx, pid in enumerate(products, start=1):
        x, y = pos.get(pid, (0.0, 0.0))
        nodes.append(
            {
                "id": idx,
                "label": pid,
                "x": float(300 + x * 220),
                "y": float(250 + y * 180),
                "size": float(20 + min(20, totals.loc[pid] / max(1.0, totals.iloc[0]) * 20)),
                "category": "Groceries",
                "product_id": pid,
            }
        )

    id_map = {n["label"]: n["id"] for n in nodes}
    edges_mapped = [
        {"from": id_map[e["from"]], "to": id_map[e["to"]], "type": e["type"], "weight": e["weight"]}
        for e in edges
        if e["from"] in id_map and e["to"] in id_map
    ]

    return ProductGraph(nodes=nodes, edges=edges_mapped)


def build_product_graph(
    path: Optional[Path] = None, top_n: int = 30, min_corr: float = 0.25
) -> ProductGraph:
    df = load_groceries_sales(path or DEFAULT_DATA_PATH)
    return _build_graph_from_data(df, top_n=top_n, min_corr=min_corr)


def load_or_build(top_n: int = 30, min_corr: float = 0.25) -> ProductGraph:
    if GRAPH_PATH.exists():
        try:
            data = json.loads(GRAPH_PATH.read_text())
            return ProductGraph(nodes=data["nodes"], edges=data["edges"])
        except Exception:
            pass
    graph = build_product_graph(top_n=top_n, min_corr=min_corr)
    GRAPH_PATH.write_text(json.dumps({"nodes": graph.nodes, "edges": graph.edges}, indent=2))
    return graph
