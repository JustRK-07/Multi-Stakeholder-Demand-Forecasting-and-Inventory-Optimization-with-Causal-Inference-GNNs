from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, File, Form, Header, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api_response import err, ok
from .audit_log import append_audit_event, list_audit_events
from .auth_store import AuthError, create_session, create_user, delete_session, get_session, update_password
from .auth_store import update_profile as update_user_profile
from .dashboard_metrics import (
    compute_dashboard_summary,
    compute_inventory_items,
    compute_kpis,
    compute_stores,
)
from .dataset_registry import activate_dataset, archive_dataset, dataset_count, delete_dataset, get_active_dataset, get_dataset, list_datasets, register_dataset_upload
from .ml.forecast_model import forecast as forecast_units
from .ml.forecast_model import forecast_multi, recent_actuals
from .ml.forecast_model import training_summary
from .ml.gnn_inference import get_embedding, graph_meta, most_similar
from .ml.graph_model import load_or_build as load_product_graph
from .ml.rl_inference import recommend_orders
from .ml.rl_analysis import evaluate_policies, scenario_simulation
from .ml.rl_metrics import load_rl_metrics
from .ml.causal_engine import available_promotion_segments, estimate_promo_effect, explain_factors, promotion_summary
from .ml.federated_sim import simulate_federated_rounds
from .ml.shap_explain import compute_shap_features
from .ml.shap_explain import build_explainability_summary
from .ml.drift_monitor import export_snapshot, generate_drift_report, list_drift_history, record_drift_scan
from .ml.data import list_grocery_products
from .ml.monitoring import model_status
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


def _extract_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


def _session_email(authorization: Optional[str]) -> Optional[str]:
    token = _extract_token(authorization)
    session = get_session(token or "")
    if not session:
        return None
    return str(session["user"]["email"])


def _session_from_header(authorization: Optional[str]) -> Optional[Dict[str, Any]]:
    token = _extract_token(authorization)
    return get_session(token or "")


@app.get("/health")
def health() -> Dict[str, Any]:
    return ok({"status": "ok"})


@app.post("/api/v1/auth/signup")
def signup(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        user = create_user(str(payload.get("name", "")), str(payload.get("email", "")), str(payload.get("password", "")))
        session = create_session(str(payload.get("email", "")), str(payload.get("password", "")))
    except AuthError as exc:
        return JSONResponse(status_code=400, content=err(exc.code, exc.message, details=exc.details))
    return ok({"token": session["token"], "user": user})


@app.post("/api/v1/auth/login")
def login(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        session = create_session(str(payload.get("email", "")), str(payload.get("password", "")))
    except AuthError as exc:
        return JSONResponse(status_code=401, content=err(exc.code, exc.message, details=exc.details))
    return ok(session)


@app.get("/api/v1/auth/session")
def auth_session(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    token = _extract_token(authorization)
    session = get_session(token or "")
    if not session:
        return JSONResponse(status_code=401, content=err("UNAUTHORIZED", "A valid session is required."))
    return ok(session)


@app.post("/api/v1/auth/logout")
def logout(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    token = _extract_token(authorization)
    actor = _session_email(authorization)
    if not token or not delete_session(token):
        return JSONResponse(status_code=401, content=err("UNAUTHORIZED", "A valid session is required."))
    append_audit_event("auth.logout", actor=actor, target=actor)
    return ok({"loggedOut": True})


@app.put("/api/v1/auth/password")
def change_password(payload: Dict[str, Any], authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    token = _extract_token(authorization)
    session = get_session(token or "")
    if not session:
        return JSONResponse(status_code=401, content=err("UNAUTHORIZED", "A valid session is required."))
    try:
        user = update_password(
            session["user"]["email"],
            str(payload.get("currentPassword", "")),
            str(payload.get("newPassword", "")),
        )
    except AuthError as exc:
        return JSONResponse(status_code=400, content=err(exc.code, exc.message, details=exc.details))
    return ok({"updated": True, "user": user})


@app.put("/api/v1/auth/profile")
def update_profile(payload: Dict[str, Any], authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    token = _extract_token(authorization)
    session = get_session(token or "")
    if not session:
        return JSONResponse(status_code=401, content=err("UNAUTHORIZED", "A valid session is required."))
    try:
        user = update_user_profile(session["user"]["email"], name=str(payload.get("name", "")))
    except AuthError as exc:
        return JSONResponse(status_code=400, content=err(exc.code, exc.message, details=exc.details))
    return ok({"updated": True, "user": user})


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


@app.get("/api/v1/orders/scenario")
def get_order_scenario(
    store_id: Optional[str] = None,
    product_id: Optional[str] = None,
    periods: int = 14,
    demand_scale: float = 1.0,
    lead_time_days: int = 1,
    holding_cost: float = 0.15,
    stockout_cost: float = 1.5,
) -> Dict[str, Any]:
    result = scenario_simulation(
        store_id=store_id,
        product_id=product_id,
        periods=periods,
        demand_scale=demand_scale,
        lead_time_days=lead_time_days,
        holding_cost=holding_cost,
        stockout_cost=stockout_cost,
    )
    return ok(result)


@app.get("/api/v1/promotions/impact")
def get_promotion_impact(promo_id: str = "all", store_id: Optional[str] = None, sku: Optional[str] = None) -> Dict[str, Any]:
    promo_id = promo_id.lower().strip()
    result = estimate_promo_effect(promo_id=promo_id, store_id=store_id, sku=sku)
    promo = {
        "id": result.promo_id,
        "name": result.promo_name,
        "lift": result.lift_pct,
        "confidence": result.confidence,
        "baseline": result.baseline,
        "withPromo": result.with_promo,
        "incrementalUnits": result.incremental_units,
        "ateUnits": result.ate_units,
        "methods": result.methods,
        "diagnostics": result.diagnostics,
        "cohort": result.cohort,
    }
    response = {"found": True, "promotion": promo, "availablePromotions": available_promotion_segments()}
    if result.warning:
        response["warning"] = result.warning
    return ok(response)


@app.get("/api/v1/promotions/summary")
def get_promotions_summary(store_id: Optional[str] = None, sku: Optional[str] = None) -> Dict[str, Any]:
    return ok({"items": promotion_summary(store_id=store_id, sku=sku), "availablePromotions": available_promotion_segments()})


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


@app.get("/api/v1/graph/meta")
def get_graph_meta() -> Dict[str, Any]:
    return ok(graph_meta())


@app.get("/api/v1/rl/rewards")
def get_rl_rewards(store_id: Optional[str] = None) -> Dict[str, Any]:
    metrics = evaluate_policies(store_id=store_id, refresh=bool(store_id))
    return ok({"data": metrics.get("reward_curve", [])})


@app.get("/api/v1/rl/metrics")
def get_rl_metrics() -> Dict[str, Any]:
    metrics = load_rl_metrics()
    series = evaluate_policies().get("series", [])
    return ok({**metrics, "series": series})


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


@app.get("/api/v1/explainability/summary")
def get_explainability_summary(store_id: Optional[str] = None, sku: Optional[str] = None) -> Dict[str, Any]:
    return ok(build_explainability_summary(store_id=store_id, product_id=sku))


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
    authorization: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    session = _session_from_header(authorization)
    if not session:
        return JSONResponse(status_code=401, content=err("UNAUTHORIZED", "A valid session is required."))
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
    append_audit_event("dataset.upload", actor=session["user"]["email"], target=record["datasetId"], details={"filename": record["filename"], "status": record["status"]})
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
def get_datasets(page: int = 1, page_size: int = 50, include_archived: bool = False) -> Dict[str, Any]:
    active_dataset = get_active_dataset()
    return ok(
        {
            "items": list_datasets(page=page, page_size=page_size, include_archived=include_archived),
            "activeDatasetId": active_dataset.get("datasetId") if active_dataset else None,
            "page": page,
            "pageSize": page_size,
            "total": dataset_count(include_archived=include_archived),
            "includeArchived": include_archived,
        }
    )


@app.post("/api/v1/datasets/{dataset_id}/activate")
def activate_uploaded_dataset(dataset_id: str, authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    session = _session_from_header(authorization)
    if not session:
        return JSONResponse(status_code=401, content=err("UNAUTHORIZED", "A valid session is required."))
    if session["user"].get("role") != "admin":
        return JSONResponse(status_code=403, content=err("FORBIDDEN", "Admin role required."))
    try:
        record = activate_dataset(dataset_id)
    except Exception as exc:
        return JSONResponse(
            status_code=404,
            content=err("DATASET_ACTIVATION_FAILED", str(exc), details={"datasetId": dataset_id}),
        )
    append_audit_event("dataset.activate", actor=session["user"]["email"], target=dataset_id)
    return ok(record)


@app.delete("/api/v1/datasets/{dataset_id}")
def remove_dataset(dataset_id: str, authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    session = _session_from_header(authorization)
    if not session:
        return JSONResponse(status_code=401, content=err("UNAUTHORIZED", "A valid session is required."))
    if session["user"].get("role") != "admin":
        return JSONResponse(status_code=403, content=err("FORBIDDEN", "Admin role required."))
    try:
        record = delete_dataset(dataset_id)
    except Exception as exc:
        return JSONResponse(
            status_code=404,
            content=err("DATASET_DELETE_FAILED", str(exc), details={"datasetId": dataset_id}),
        )
    append_audit_event("dataset.delete", actor=session["user"]["email"], target=dataset_id, details={"filename": record.get("filename")})
    return ok({"deleted": True, "dataset": record, "activeDatasetId": get_active_dataset().get("datasetId") if get_active_dataset() else None})


@app.post("/api/v1/datasets/{dataset_id}/archive")
def archive_uploaded_dataset(dataset_id: str, archived: bool = True, authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    session = _session_from_header(authorization)
    if not session:
        return JSONResponse(status_code=401, content=err("UNAUTHORIZED", "A valid session is required."))
    if session["user"].get("role") != "admin":
        return JSONResponse(status_code=403, content=err("FORBIDDEN", "Admin role required."))
    try:
        record = archive_dataset(dataset_id, archived=archived)
    except Exception as exc:
        return JSONResponse(
            status_code=404,
            content=err("DATASET_ARCHIVE_FAILED", str(exc), details={"datasetId": dataset_id}),
        )
    append_audit_event("dataset.archive" if archived else "dataset.restore", actor=session["user"]["email"], target=dataset_id)
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


@app.get("/api/v1/drift/report")
def get_drift_report(baseline_days: int = 60, recent_days: int = 14, rows: int = 5000) -> Dict[str, Any]:
    return ok(generate_drift_report(baseline_days=baseline_days, recent_days=recent_days, rows=rows))


@app.post("/api/v1/drift/scan")
def scan_drift(baseline_days: int = 60, recent_days: int = 14, rows: int = 5000) -> Dict[str, Any]:
    return ok(record_drift_scan(baseline_days=baseline_days, recent_days=recent_days, rows=rows))


@app.get("/api/v1/drift/history")
def get_drift_history(limit: int = 20) -> Dict[str, Any]:
    return ok({"items": list_drift_history(limit=limit)})


@app.get("/api/v1/monitoring/status")
def get_monitoring_status() -> Dict[str, Any]:
    return ok(model_status())


@app.get("/api/v1/audit/logs")
def get_audit_logs(limit: int = 50, authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    session = _session_from_header(authorization)
    if not session:
        return JSONResponse(status_code=401, content=err("UNAUTHORIZED", "A valid session is required."))
    if session["user"].get("role") != "admin":
        return JSONResponse(status_code=403, content=err("FORBIDDEN", "Admin role required."))
    return ok({"items": list_audit_events(limit=limit)})
