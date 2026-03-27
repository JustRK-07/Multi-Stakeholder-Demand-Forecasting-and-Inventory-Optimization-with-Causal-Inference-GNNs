from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ml.causal_engine import available_promotion_segments, estimate_promo_effect, promotion_summary  # noqa: E402
from app.ml.gnn_inference import graph_meta, load_embeddings, most_similar  # noqa: E402
from app.ml.gnn_train import train_gnn  # noqa: E402
from app.ml.graph_model import build_product_graph  # noqa: E402


def test_gnn_training_generates_embeddings():
    meta = train_gnn(top_n=20, min_corr=0.2, embedding_dim=6)
    assert meta["graph_stats"]["nodes"] > 0
    embeddings = load_embeddings()
    assert len(embeddings) > 0
    summary = graph_meta()
    assert summary["embedding_dim"] > 0


def test_graph_contains_nodes_and_edges():
    graph = build_product_graph(top_n=20, min_corr=0.2)
    assert len(graph.nodes) > 0
    assert len(graph.edges) > 0
    assert {"from_product", "to_product", "type", "weight"} <= set(graph.edges[0].keys())


def test_similarity_returns_neighbors():
    train_gnn(top_n=20, min_corr=0.2, embedding_dim=6)
    embeddings = load_embeddings()
    product_id = next(iter(embeddings.keys()))
    similar = most_similar(product_id, k=3)
    assert len(similar) > 0


def test_causal_effect_returns_method_diagnostics():
    result = estimate_promo_effect("all")
    assert result.promo_name
    assert {"psm", "dml", "did"} <= set(result.methods.keys())
    assert "treated_share" in result.diagnostics


def test_promotion_summary_returns_backend_rows():
    segments = available_promotion_segments()
    assert len(segments) > 0
    rows = promotion_summary()
    assert len(rows) == len(segments)
    assert {"id", "name", "lift", "confidence", "baseline", "withPromo", "incrementalUnits"} <= set(rows[0].keys())
