"""
Phase 3: Updated forecast endpoints using pre-trained models.

Routes forecast requests to either:
1. Pre-trained models (for users with assigned models)
2. Legacy trained models (for backward compatibility)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .auth_store import get_session
from .api_response import err, ok
from .pretrained_forecast import generate_forecast, get_model_metadata, ModelLoadError
from .ml.forecast_model import (
    forecast as forecast_units,
    forecast_multi,
    recent_actuals,
    training_summary,
)


def get_user_store_type(token: Optional[str] = None) -> Optional[str]:
    """Extract user's store type from session token."""
    if not token:
        return None
    
    try:
        session = get_session(token)
        if session and session.get("user"):
            return session["user"].get("storeType")
    except Exception:
        pass
    
    return None


def format_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format forecast rows for API response."""
    data: List[Dict[str, Any]] = []
    for row in rows:
        # Handle both old format (with 'date' key) and new format (with 'date' key)
        d = row.get("date")
        if isinstance(d, str):
            d = datetime.fromisoformat(d)
        elif not isinstance(d, datetime):
            continue
        
        item: Dict[str, Any] = {
            "date": d.strftime("%b %d"),
            "predicted": int(round(row.get("predicted") or row.get("forecast", 0))),
            "lowerBound": int(round(row.get("lowerBound") or row.get("lower_bound", 0))),
            "upperBound": int(round(row.get("upperBound") or row.get("upper_bound", 0))),
        }
        data.append(item)
    return data


def get_forecasts_v3(
    store_id: str,
    horizon: int = 30,
    product_id: Optional[str] = None,
    multi: bool = False,
    include_actuals: bool = True,
    gnn_adjust: bool = True,
    auth_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Enhanced forecast endpoint (Phase 3).
    
    Routes to pre-trained models if user has assigned model,
    otherwise falls back to legacy trained models.
    """
    
    selected_store_id = store_id
    selected_product_id = product_id
    
    # Try to get user's store type from session
    user_store_type = get_user_store_type(auth_token)
    use_pretrained = user_store_type is not None
    
    payload: Dict[str, Any] = {
        "horizon": horizon,
        "storeId": selected_store_id,
        "productId": selected_product_id,
        "gnnAdjust": gnn_adjust,
        "modelSource": "pretrained" if use_pretrained else "trained",
    }
    
    try:
        if use_pretrained:
            # Use pre-trained model for this store type
            if multi:
                # Generate for multiple horizons
                payload["horizons"] = {}
                for h in [7, 14, 30]:
                    forecasts = generate_forecast(
                        store_type=user_store_type,
                        store_id=store_id,
                        product_id=product_id,
                        horizon=h,
                    )
                    payload["horizons"][str(h)] = format_rows(forecasts)
            else:
                # Single horizon forecast
                forecasts = generate_forecast(
                    store_type=user_store_type,
                    store_id=store_id,
                    product_id=product_id,
                    horizon=horizon,
                )
                payload["data"] = format_rows(forecasts)
            
            # Add model metadata
            payload["modelInfo"] = get_model_metadata(user_store_type)
            payload["metrics"] = payload["modelInfo"].get("accuracy_metrics", {})
        
        else:
            # Fall back to legacy model (for backward compatibility)
            summary = training_summary()
            payload["modelInfo"] = summary["metadata"]
            payload["metrics"] = summary["metrics"]
            
            if multi:
                horizon_map = forecast_multi(store_id, product_id=product_id, gnn_adjust=gnn_adjust)
                payload["horizons"] = {str(k): format_rows(v) for k, v in horizon_map.items()}
            else:
                forecast_rows = forecast_units(store_id, horizon=horizon, product_id=product_id, gnn_adjust=gnn_adjust)
                payload["data"] = format_rows(forecast_rows)
        
        # Include actuals if requested (from sample data)
        if include_actuals and use_pretrained:
            try:
                from .pretrained_forecast import get_model
                model = get_model(user_store_type)
                if model.sample_data is not None:
                    recent = model.sample_data.tail(10)
                    payload["actuals"] = [
                        {"date": d.strftime("%b %d"), "actual": int(round(v))}
                        for d, v in zip(recent["date"].tolist(), recent["sales_qty"].tolist())
                    ]
            except Exception:
                payload["actuals"] = []
        
        return ok(payload)
    
    except Exception as e:
        return err("FORECAST_ERROR", str(e))
