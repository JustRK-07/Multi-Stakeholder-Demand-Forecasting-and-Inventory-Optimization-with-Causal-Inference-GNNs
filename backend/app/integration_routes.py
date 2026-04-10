"""
Integration API Routes - Phase 3

Endpoints for OAuth flows, integration management, and data sync.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from sqlalchemy.orm import Session

from .api_response import err, ok
from .auth_store import get_session
from .database import User, SessionLocal
from .integrations import (
    IntegrationError,
    ShopifyIntegration,
    SquareIntegration,
    WebhookIntegration,
    get_integration,
    list_integrations,
    register_integration,
    sync_integration,
)

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


def _get_user_from_token(authorization: Optional[str]) -> Optional[User]:
    """Extract user from Authorization header."""
    if not authorization:
        return None
    
    try:
        token = authorization.replace("Bearer ", "")
        session = get_session(token)
        if session and session.get("user"):
            db = SessionLocal()
            user = db.query(User).filter(User.email == session["user"]["email"]).first()
            db.close()
            return user
    except Exception:
        pass
    
    return None


@router.get("/available")
def get_available_integrations() -> Dict[str, Any]:
    """List available integration types."""
    return ok({
        "integrations": [
            {
                "type": "shopify",
                "name": "Shopify",
                "description": "Connect your Shopify store",
                "icon": "🛒",
                "scopes": ["read_orders", "read_products"],
            },
            {
                "type": "square",
                "name": "Square POS",
                "description": "Connect your Square POS system",
                "icon": "🏪",
                "scopes": ["MERCHANT_PROFILE_READ", "ORDERS_READ"],
            },
            {
                "type": "webhook",
                "name": "Custom Webhook",
                "description": "Send custom sales data via webhook",
                "icon": "🔌",
                "scopes": [],
            },
        ]
    })


@router.get("/list")
def list_user_integrations(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """List all integrations for current user."""
    
    user = _get_user_from_token(authorization)
    if not user:
        return err("UNAUTHORIZED", "Authentication required")
    
    try:
        integrations = list_integrations(user.id)
        return ok({"integrations": integrations})
    except Exception as e:
        return err("LIST_ERROR", str(e))


@router.post("/shopify/oauth/start")
def shopify_oauth_start(
    shop_domain: str = Query(...),
    redirect_uri: str = Query(...),
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """Start Shopify OAuth flow."""
    
    user = _get_user_from_token(authorization)
    if not user:
        return err("UNAUTHORIZED", "Authentication required")
    
    try:
        # In production, store these in database with session
        oauth_url = ShopifyIntegration.get_oauth_url(
            shop_domain=shop_domain,
            api_key="YOUR_SHOPIFY_API_KEY",  # From env
            redirect_uri=redirect_uri,
            scopes=["read_orders", "read_products"],
        )
        
        return ok({
            "oauth_url": oauth_url,
            "state": "state-value-from-session",  # Store in session
        })
    except Exception as e:
        return err("OAUTH_ERROR", str(e))


@router.post("/shopify/oauth/callback")
def shopify_oauth_callback(
    code: str = Query(...),
    shop_domain: str = Query(...),
    state: str = Query(...),
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """Handle Shopify OAuth callback."""
    
    user = _get_user_from_token(authorization)
    if not user:
        return err("UNAUTHORIZED", "Authentication required")
    
    try:
        # In production, verify state matches session
        token_response = ShopifyIntegration.exchange_code_for_token(
            shop_domain=shop_domain,
            api_key="YOUR_SHOPIFY_API_KEY",
            api_secret="YOUR_SHOPIFY_API_SECRET",
            code=code,
        )
        
        access_token = token_response.get("access_token")
        if not access_token:
            return err("TOKEN_ERROR", "Failed to get access token")
        
        # Register integration
        integration_id = register_integration(
            user_id=user.id,
            integration_type="shopify",
            api_key=access_token,
            store_id=shop_domain,
        )
        
        return ok({
            "integration_id": integration_id,
            "status": "connected",
            "message": "Shopify integration connected successfully",
        })
    
    except IntegrationError as e:
        return err("OAUTH_ERROR", str(e))


@router.post("/square/oauth/start")
def square_oauth_start(
    redirect_uri: str = Query(...),
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """Start Square OAuth flow."""
    
    user = _get_user_from_token(authorization)
    if not user:
        return err("UNAUTHORIZED", "Authentication required")
    
    try:
        oauth_url = SquareIntegration.get_oauth_url(
            client_id="YOUR_SQUARE_CLIENT_ID",
            redirect_uri=redirect_uri,
            scopes=["MERCHANT_PROFILE_READ", "ORDERS_READ"],
        )
        
        return ok({
            "oauth_url": oauth_url,
            "state": "state-value-from-session",
        })
    except Exception as e:
        return err("OAUTH_ERROR", str(e))


@router.post("/square/oauth/callback")
def square_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    redirect_uri: str = Query(...),
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """Handle Square OAuth callback."""
    
    user = _get_user_from_token(authorization)
    if not user:
        return err("UNAUTHORIZED", "Authentication required")
    
    try:
        token_response = SquareIntegration.exchange_code_for_token(
            client_id="YOUR_SQUARE_CLIENT_ID",
            client_secret="YOUR_SQUARE_CLIENT_SECRET",
            code=code,
            redirect_uri=redirect_uri,
        )
        
        access_token = token_response.get("access_token")
        if not access_token:
            return err("TOKEN_ERROR", "Failed to get access token")
        
        integration_id = register_integration(
            user_id=user.id,
            integration_type="square",
            api_key=access_token,
        )
        
        return ok({
            "integration_id": integration_id,
            "status": "connected",
            "message": "Square integration connected successfully",
        })
    
    except IntegrationError as e:
        return err("OAUTH_ERROR", str(e))


@router.post("/webhook/{integration_id}")
def webhook_receive(
    integration_id: str,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """Receive webhook data."""
    
    try:
        integration = get_integration(integration_id)
        if not integration:
            return err("NOT_FOUND", "Integration not found")
        
        if integration.integration_type != "webhook":
            return err("INVALID_TYPE", "Integration is not a webhook")
        
        # Process webhook data
        records = WebhookIntegration.process_webhook_data(data)
        
        # In production, store these records
        return ok({
            "records_received": len(records),
            "message": "Webhook data received successfully",
        })
    
    except Exception as e:
        return err("WEBHOOK_ERROR", str(e))


@router.post("/sync/{integration_id}")
def trigger_sync(
    integration_id: str,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """Trigger manual sync for an integration."""
    
    user = _get_user_from_token(authorization)
    if not user:
        return err("UNAUTHORIZED", "Authentication required")
    
    try:
        sync_integration(integration_id)
        
        return ok({
            "integration_id": integration_id,
            "status": "syncing",
            "message": "Sync started",
        })
    
    except IntegrationError as e:
        return err("SYNC_ERROR", str(e))


@router.delete("/{integration_id}")
def disconnect_integration(
    integration_id: str,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """Disconnect an integration."""
    
    user = _get_user_from_token(authorization)
    if not user:
        return err("UNAUTHORIZED", "Authentication required")
    
    try:
        # In production, delete from database
        integration = get_integration(integration_id)
        if not integration:
            return err("NOT_FOUND", "Integration not found")
        
        return ok({
            "integration_id": integration_id,
            "status": "disconnected",
            "message": "Integration disconnected",
        })
    
    except Exception as e:
        return err("DELETE_ERROR", str(e))


@router.get("/{integration_id}")
def get_integration_status(
    integration_id: str,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """Get status of an integration."""
    
    user = _get_user_from_token(authorization)
    if not user:
        return err("UNAUTHORIZED", "Authentication required")
    
    try:
        integration = get_integration(integration_id)
        if not integration:
            return err("NOT_FOUND", "Integration not found")
        
        return ok({
            "integration_id": integration_id,
            "type": integration.integration_type,
            "status": integration.status,
            "last_sync": integration.last_sync,
            "sync_interval_hours": integration.sync_interval_hours,
        })
    
    except Exception as e:
        return err("STATUS_ERROR", str(e))
