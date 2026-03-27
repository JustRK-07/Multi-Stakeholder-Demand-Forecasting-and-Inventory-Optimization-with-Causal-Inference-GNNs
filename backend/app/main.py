from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api_response import err, ok
from .dashboard_metrics import (
    compute_dashboard_summary,
    compute_inventory_items,
    compute_kpis,
    compute_stores,
)
from .dataset_registry import activate_dataset, get_active_dataset, get_dataset, list_datasets, register_dataset_upload
from .ml.forecast_model import forecast as forecast_units
from .ml.forecast_model import forecast_multi, recent_actuals
from .ml.forecast_model import training_summary
from .ml.gnn_inference import get_embedding, most_similar
from .ml.graph_model import load_or_build as load_product_graph
from .ml.rl_inference import recommend_orders
from .ml.rl_metrics import load_rl_metrics
from .ml.causal_engine import estimate_promo_effect, explain_factors
from .ml.federated_sim import simulate_federated_rounds
from .ml.shap_explain import compute_shap_features
from .ml.drift_monitor import export_snapshot
from .ml.data import list_grocery_products
from .settings_store import load_settings, save_settings


app = FastAPI(title="RetailCast API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, Any]:
    return ok({"status": "ok"})


@app.get("/api/v1/kpis")
def get_kpis(store_id: Optional[str] = None, date_range: Optional[str] = None) -> Dict[str, Any]:
    return ok(compute_kpis(store_id=store_id, date_range=date_range))


@app.get("/api/v1/dashboard/summary")
def get_dashboard_summary(store_id: Optional[str] = None) -> Dict[str, Any]:
    return ok(compute_dashboard_summary(store_id=store_id))


@app.get("/api/v1/forecasts/{store_id}")
def get_forecasts(
    store_id: str,
    horizon: int = 30,
    product_id: Optional[str] = None,
    multi: bool = False,
    include_actuals: bool = True,
    gnn_adjust: bool = True,
) -> Dict[str, Any]:
    selected_store_id = store_id
    selected_product_id = product_id
    def format_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        data: List[Dict[str, Any]] = []
        for row in rows:
            d = row["date"]
            item: Dict[str, Any] = {
                "date": d.strftime("%b %-d") if "%-d" in datetime.now().strftime("%-d") else d.strftime("%b %d"),
                "predicted": int(round(row["predicted"])),
                "lowerBound": int(round(row["lowerBound"])),
                "upperBound": int(round(row["upperBound"])),
            }
            data.append(item)
        return data

    summary = training_summary()
    payload: Dict[str, Any] = {
        "horizon": horizon,
        "storeId": selected_store_id,
        "productId": selected_product_id,
        "gnnAdjust": gnn_adjust,
        "modelInfo": summary["metadata"],
        "metrics": summary["metrics"],
    }

    if multi:
        horizon_map = forecast_multi(store_id, product_id=product_id, gnn_adjust=gnn_adjust)
        payload["horizons"] = {str(k): format_rows(v) for k, v in horizon_map.items()}
    else:
        forecast_rows = forecast_units(store_id, horizon=horizon, product_id=product_id, gnn_adjust=gnn_adjust)
        payload["data"] = format_rows(forecast_rows)

    if include_actuals:
        actuals = recent_actuals(store_id, product_id, days=10)
        payload["actuals"] = [
            {"date": d["date"].strftime("%b %-d") if "%-d" in datetime.now().strftime("%-d") else d["date"].strftime("%b %d"), "actual": int(round(d["actual"]))}
            for d in actuals
        ]

    return ok(payload)


@app.get("/api/v1/forecast/meta")
def get_forecast_meta() -> Dict[str, Any]:
    summary = training_summary()
    active_dataset = get_active_dataset()
    return ok(
        {
            "metrics": summary["metrics"],
            "modelInfo": summary["metadata"],
            "stores": summary["stores"],
            "products": summary["products"],
            "activeDatasetId": active_dataset.get("datasetId") if active_dataset else None,
        }
    )


@app.get("/api/v1/inventory")
def get_inventory(store_id: Optional[str] = None, risk_level: Optional[str] = None) -> Dict[str, Any]:
    return ok({"items": compute_inventory_items(store_id=store_id, risk_level=risk_level)})


@app.get("/api/v1/orders/recommend")
def get_order_recommendations(store_id: Optional[str] = None, mode: str = "rl") -> Dict[str, Any]:
    use_rl = mode != "baseline"
    recs = recommend_orders(store_id=store_id, limit=4, use_rl=use_rl)
    return ok({"recommendations": recs})


@app.get("/api/v1/promotions/impact")
def get_promotion_impact(promo_id: str, store_id: Optional[str] = None) -> Dict[str, Any]:
    promo_id = promo_id.lower().strip()
    result = estimate_promo_effect(store_id=store_id)
    name_map = {
        "festival": "Festival Discount",
        "bogo": "Buy 1 Get 1",
        "seasonal": "Seasonal Offer",
        "flash": "Flash Sale",
        "holiday": "Holiday/Promotion",
        "promo": "Holiday/Promotion",
        "discount": "Discount Days",
    }
    promo = {
        "id": promo_id,
        "name": name_map.get(promo_id, "Holiday/Promotion"),
        "lift": result.lift_pct,
        "confidence": result.confidence,
        "baseline": result.baseline,
        "withPromo": result.with_promo,
    }
    response = {"found": True, "promotion": promo}
    if result.warning:
        response["warning"] = result.warning
    return ok(response)


@app.get("/api/v1/graph/products")
def get_product_graph(store_id: Optional[str] = None, top_n: int = 30, min_corr: float = 0.25) -> Dict[str, Any]:
    _ = store_id
    graph = load_product_graph(top_n=top_n, min_corr=min_corr)
    return ok({"nodes": graph.nodes, "edges": graph.edges})


@app.get("/api/v1/graph/embeddings")
def get_graph_embeddings(product_id: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
    if not product_id:
        return ok({"items": [], "similar": []})
    emb = get_embedding(product_id)
    if emb is None:
        return ok({"items": [], "similar": []})
    similar = [{"product_id": pid, "similarity": round(sim, 4)} for pid, sim in most_similar(product_id, k=top_k)]
    return ok({"items": [{"product_id": product_id, "embedding": emb.tolist()}], "similar": similar})


@app.get("/api/v1/rl/rewards")
def get_rl_rewards(store_id: Optional[str] = None) -> Dict[str, Any]:
    _ = store_id
    reward_curve = []
    for i in range(50):
        episode = i + 1
        # Smooth-ish curve approaching -50; baseline approaches -200.
        reward = -500 + (450 * (1 - (2.718281828 ** (-i / 15)))) + (i % 7) * 2
        baseline = -500 + (300 * (1 - (2.718281828 ** (-i / 20))))
        reward_curve.append({"episode": episode, "reward": round(reward, 2), "baseline": round(baseline, 2)})
    return ok({"data": reward_curve})


@app.get("/api/v1/rl/metrics")
def get_rl_metrics() -> Dict[str, Any]:
    return ok(load_rl_metrics())


@app.get("/api/v1/causal/factors")
def get_causal_factors(store_id: Optional[str] = None, sku: Optional[str] = None) -> Dict[str, Any]:
    factors = explain_factors(store_id=store_id, sku=sku)
    data = [{"factor": f.factor, "impact": f.impact, "direction": f.direction} for f in factors]
    return ok({"data": data})


@app.get("/api/v1/federated/rounds")
def get_federated_rounds() -> Dict[str, Any]:
    rounds = simulate_federated_rounds()
    return ok({"data": rounds})


@app.get("/api/v1/stores")
def get_stores() -> Dict[str, Any]:
    return ok({"data": compute_stores()})


@app.get("/api/v1/explainability/features")
def get_explainability_features(store_id: Optional[str] = None, sku: Optional[str] = None) -> Dict[str, Any]:
    features = compute_shap_features(store_id=store_id, product_id=sku)
    data = [{"feature": f.feature, "importance": round(f.importance, 3), "shap": round(f.shap, 4)} for f in features]
    return ok({"data": data})


@app.get("/api/v1/products")
def get_products(store_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    products = list_grocery_products(store_id=store_id)
    if limit > 0:
        products = products.head(limit)
    data = products[["store_id", "product_id", "units_sold"]].to_dict(orient="records")
    return ok({"items": data})


@app.post("/api/v1/datasets/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    column_mapping: Optional[str] = Form(default=None),
) -> Dict[str, Any]:
    mapping: Optional[Dict[str, str]] = None
    if column_mapping:
        import json

        try:
            payload = json.loads(column_mapping)
            if isinstance(payload, dict):
                mapping = {str(k): str(v) for k, v in payload.items()}
        except json.JSONDecodeError:
            return JSONResponse(
                status_code=400,
                content=err("INVALID_COLUMN_MAPPING", "Column mapping must be valid JSON."),
            )

    content = await file.read()
    record = register_dataset_upload(file.filename or "uploaded_dataset", content, mapping)
    return ok(record)


@app.get("/api/v1/datasets/{dataset_id}/status")
def dataset_status(dataset_id: str) -> Dict[str, Any]:
    record = get_dataset(dataset_id)
    if record is None:
        return JSONResponse(
            status_code=404,
            content=err("DATASET_NOT_FOUND", f"Dataset '{dataset_id}' was not found.", details={"datasetId": dataset_id}),
        )
    return ok(record)


@app.get("/api/v1/datasets")
def get_datasets() -> Dict[str, Any]:
    active_dataset = get_active_dataset()
    return ok({"items": list_datasets(), "activeDatasetId": active_dataset.get("datasetId") if active_dataset else None})


@app.post("/api/v1/datasets/{dataset_id}/activate")
def activate_uploaded_dataset(dataset_id: str) -> Dict[str, Any]:
    try:
        record = activate_dataset(dataset_id)
    except Exception as exc:
        return JSONResponse(
            status_code=404,
            content=err("DATASET_ACTIVATION_FAILED", str(exc), details={"datasetId": dataset_id}),
        )
    return ok(record)


@app.get("/api/v1/settings")
def get_settings() -> Dict[str, Any]:
    return ok(load_settings())


@app.put("/api/v1/settings")
def update_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
    saved = save_settings(payload)
    return ok({"updated": True, "settings": saved})


@app.post("/api/v1/drift/snapshot")
def create_drift_snapshot(rows: int = 5000) -> Dict[str, Any]:
    path = export_snapshot(rows=rows)
    return ok({"snapshot": str(path)})
