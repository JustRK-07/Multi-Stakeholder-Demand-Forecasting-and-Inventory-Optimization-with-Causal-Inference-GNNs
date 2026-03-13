from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from .data import DEFAULT_DATA_PATH, load_groceries_sales
from .graph_model import _build_graph_from_data


def _require_torch() -> None:
    try:
        import torch  # noqa: F401
        import torch_geometric  # noqa: F401
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Torch or torch-geometric not installed. Install CPU-only deps:\n"
            "  pip install -r backend/requirements-gnn.txt "
            "--index-url https://download.pytorch.org/whl/cpu\n"
            "Then re-run: python -m app.ml.gnn_train"
        ) from exc


ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_DIR = ROOT / "backend" / "app" / "ml" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = ARTIFACT_DIR / "product_gnn.pt"
META_PATH = ARTIFACT_DIR / "product_gnn_meta.json"


@dataclass
class GraphData:
    product_ids: List[str]
    x: np.ndarray
    y: np.ndarray
    edge_index: np.ndarray


def _build_node_features(df: pd.DataFrame, product_ids: List[str]) -> GraphData:
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
    agg = agg.set_index("product_id").reindex(product_ids).fillna(0.0)

    x = agg[["mean_units", "std_units", "mean_price", "mean_discount", "promo_rate"]].values.astype("float32")
    y = agg["mean_units"].values.astype("float32")

    return GraphData(product_ids=product_ids, x=x, y=y, edge_index=np.empty((2, 0), dtype=np.int64))


def _edge_index_from_graph(nodes: List[Dict[str, object]], edges: List[Dict[str, object]]) -> np.ndarray:
    id_map = {n["id"]: i for i, n in enumerate(nodes)}
    pairs: List[List[int]] = []
    for e in edges:
        src = id_map.get(e["from"])
        dst = id_map.get(e["to"])
        if src is None or dst is None:
            continue
        pairs.append([src, dst])
        pairs.append([dst, src])
    if not pairs:
        return np.empty((2, 0), dtype=np.int64)
    return np.array(pairs, dtype=np.int64).T


def train_gnn(top_n: int = 40, min_corr: float = 0.25) -> None:
    _require_torch()
    import torch
    from torch import nn
    from torch_geometric.data import Data
    from torch_geometric.nn import GATConv, SAGEConv

    df = load_groceries_sales(DEFAULT_DATA_PATH)
    graph = _build_graph_from_data(df, top_n=top_n, min_corr=min_corr)

    product_ids = [n["product_id"] for n in graph.nodes]
    gdata = _build_node_features(df, product_ids)
    edge_index = _edge_index_from_graph(graph.nodes, graph.edges)
    gdata.edge_index = edge_index

    x = torch.tensor(gdata.x, dtype=torch.float32)
    y = torch.tensor(gdata.y, dtype=torch.float32)
    edge_index_t = torch.tensor(gdata.edge_index, dtype=torch.long)

    data = Data(x=x, edge_index=edge_index_t, y=y)

    class ProductGNN(nn.Module):
        def __init__(self, in_dim: int, hidden: int = 32) -> None:
            super().__init__()
            self.gat = GATConv(in_dim, hidden, heads=2, concat=False)
            self.sage = SAGEConv(hidden, hidden)
            self.mlp = nn.Sequential(nn.Linear(hidden, hidden), nn.ReLU(), nn.Linear(hidden, 1))

        def forward(self, g: Data) -> torch.Tensor:
            h = self.gat(g.x, g.edge_index)
            h = torch.relu(h)
            h = self.sage(h, g.edge_index)
            h = torch.relu(h)
            return self.mlp(h).squeeze(-1)

    model = ProductGNN(in_dim=x.size(1))
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()

    model.train()
    for _ in range(300):
        optimizer.zero_grad()
        preds = model(data)
        loss = loss_fn(preds, data.y)
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        embeddings = model.gat(x, edge_index_t).cpu().numpy()

    torch.save(model.state_dict(), MODEL_PATH)
    META_PATH.write_text(
        json.dumps(
            {
                "product_ids": product_ids,
                "top_n": top_n,
                "min_corr": min_corr,
                "embeddings": embeddings.tolist(),
            },
            indent=2,
        )
    )


def main() -> None:
    train_gnn()


if __name__ == "__main__":
    main()
