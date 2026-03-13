from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .api_response import ok
from .ml.forecast_model import forecast as forecast_units
from .ml.forecast_model import forecast_multi, recent_actuals
from .ml.gnn_inference import get_embedding, most_similar
from .ml.graph_model import load_or_build as load_product_graph
from .ml.rl_inference import recommend_orders
from .ml.rl_metrics import load_rl_metrics
from .ml.causal_engine import estimate_promo_effect, explain_factors
from .ml.federated_sim import simulate_federated_rounds
from .ml.shap_explain import compute_shap_features
from .ml.drift_monitor import export_snapshot
from .ml.data import list_grocery_products


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
    _ = (store_id, date_range)
    # Matches `foretell-vista-main/src/data/mockData.ts` KPI cards.
    return ok(
        [
            {"title": "Forecast Accuracy", "value": "94.2%", "change": 2.1, "trend": "up"},
            {"title": "Service Level", "value": "97.8%", "change": 0.5, "trend": "up"},
            {"title": "Inventory Turnover", "value": "12.4x", "change": -0.3, "trend": "down"},
            {"title": "Stockout Rate", "value": "1.2%", "change": -0.8, "trend": "up"},
            {"title": "Order Fill Rate", "value": "98.5%", "change": 1.2, "trend": "up"},
            {"title": "MAPE", "value": "5.8%", "change": -1.4, "trend": "up"},
        ]
    )


@app.get("/api/v1/dashboard/summary")
def get_dashboard_summary(store_id: Optional[str] = None) -> Dict[str, Any]:
    _ = store_id
    today = date.today()
    sales_trend = []
    inventory_trend = []
    for i in range(14):
        d = today - timedelta(days=13 - i)
        # Keep values deterministic-ish across calls without extra deps.
        base_sales = 600 + (i % 6) * 25
        base_demand = 620 + (i % 6) * 22
        sales_trend.append({"day": d.strftime("%b %d"), "sales": base_sales, "demand": base_demand})
        inventory_trend.append({"day": d.strftime("%b %d"), "level": 2000 - i * 80})
    alerts = [
        {"severity": "high", "message": "Stockout risk detected for SKU-004 (Micro Sensors)."},
        {"severity": "medium", "message": "Promotion impact analysis available for 'Festival Discount'."},
    ]
    return ok({"salesTrend": sales_trend, "inventoryTrend": inventory_trend, "alerts": alerts})


@app.get("/api/v1/forecasts/{store_id}")
def get_forecasts(
    store_id: str,
    horizon: int = 30,
    product_id: Optional[str] = None,
    multi: bool = False,
    include_actuals: bool = True,
    gnn_adjust: bool = True,
) -> Dict[str, Any]:
    _ = product_id
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

    payload: Dict[str, Any] = {"horizon": horizon}

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


@app.get("/api/v1/inventory")
def get_inventory(store_id: Optional[str] = None, risk_level: Optional[str] = None) -> Dict[str, Any]:
    _ = store_id
    items = [
        {"sku": "SKU-001", "name": "Premium Widgets", "stock": 1240, "capacity": 2000, "reorderPoint": 500, "daysOfSupply": 18, "risk": "low"},
        {"sku": "SKU-002", "name": "Standard Bolts", "stock": 320, "capacity": 1500, "reorderPoint": 400, "daysOfSupply": 5, "risk": "high"},
        {"sku": "SKU-003", "name": "Deluxe Gaskets", "stock": 890, "capacity": 1200, "reorderPoint": 300, "daysOfSupply": 22, "risk": "low"},
        {"sku": "SKU-004", "name": "Micro Sensors", "stock": 150, "capacity": 800, "reorderPoint": 200, "daysOfSupply": 3, "risk": "critical"},
        {"sku": "SKU-005", "name": "Copper Cables", "stock": 2100, "capacity": 3000, "reorderPoint": 700, "daysOfSupply": 30, "risk": "low"},
        {"sku": "SKU-006", "name": "LED Modules", "stock": 450, "capacity": 1000, "reorderPoint": 350, "daysOfSupply": 8, "risk": "medium"},
        {"sku": "SKU-007", "name": "Steel Frames", "stock": 680, "capacity": 1500, "reorderPoint": 500, "daysOfSupply": 12, "risk": "medium"},
        {"sku": "SKU-008", "name": "Circuit Boards", "stock": 95, "capacity": 600, "reorderPoint": 150, "daysOfSupply": 2, "risk": "critical"},
    ]
    if risk_level:
        items = [i for i in items if i["risk"] == risk_level]
    return ok({"items": items})


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
    stores = [
        {"id": 1, "name": "Downtown Hub", "lat": 40.7128, "lng": -74.006, "demand": 920, "performance": 96},
        {"id": 2, "name": "Westside Mall", "lat": 40.7589, "lng": -73.9851, "demand": 750, "performance": 91},
        {"id": 3, "name": "Airport Terminal", "lat": 40.6413, "lng": -73.7781, "demand": 1100, "performance": 98},
        {"id": 4, "name": "Harbor Point", "lat": 40.6892, "lng": -74.0445, "demand": 430, "performance": 87},
        {"id": 5, "name": "Midtown Center", "lat": 40.7549, "lng": -73.984, "demand": 1340, "performance": 94},
    ]
    return ok({"data": stores})


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
    # optional in the future: column mapping from Upload page
    column_mapping: Optional[str] = Form(default=None),
) -> Dict[str, Any]:
    _ = column_mapping
    # For now we just accept the file and return IDs.
    # Later: stream to object storage, enqueue ingestion job, etc.
    await file.read()  # consume to avoid "unread file" warnings in some servers
    dataset_id = str(uuid4())
    task_id = str(uuid4())
    return ok({"datasetId": dataset_id, "status": "processing", "taskId": task_id})


@app.get("/api/v1/datasets/{dataset_id}/status")
def dataset_status(dataset_id: str) -> Dict[str, Any]:
    _ = dataset_id
    return ok({"status": "processing", "progressPct": 35, "error": None})


@app.get("/api/v1/settings")
def get_settings() -> Dict[str, Any]:
    return ok({"forecastHorizon": 30, "holdingCost": 0.15, "stockoutCost": 1.5, "notifications": True})


@app.put("/api/v1/settings")
def update_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Stub: echo back.
    return ok({"updated": True, "settings": payload})


@app.post("/api/v1/drift/snapshot")
def create_drift_snapshot(rows: int = 5000) -> Dict[str, Any]:
    path = export_snapshot(rows=rows)
    return ok({"snapshot": str(path)})
