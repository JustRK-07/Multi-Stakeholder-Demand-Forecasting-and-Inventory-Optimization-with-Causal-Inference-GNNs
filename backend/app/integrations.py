"""
Live Data Integrations - Phase 3

Shopify, Square POS, and Webhook integration handlers.
Supports OAuth, data sync, and automatic updates.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import requests

logger = logging.getLogger(__name__)


class IntegrationError(Exception):
    pass


@dataclass
class IntegrationConfig:
    """Integration configuration."""
    integration_type: str  # shopify, square, webhook
    api_key: str
    api_secret: Optional[str] = None
    user_id: Optional[int] = None
    store_id: Optional[str] = None
    last_sync: Optional[str] = None
    sync_interval_hours: int = 24
    status: str = "disconnected"  # connected, disconnected, error


# In-memory integration registry (would be in PostgreSQL in production)
_integrations_registry: Dict[str, Dict[str, Any]] = {}


class ShopifyIntegration:
    """Shopify OAuth and data sync."""
    
    OAUTH_AUTHORIZE_URL = "https://shopify.com/oauth/authorize"
    TOKEN_URL = "https://shopify.com/oauth/access_token"
    
    @staticmethod
    def get_oauth_url(shop_domain: str, api_key: str, redirect_uri: str, scopes: List[str]) -> str:
        """Generate Shopify OAuth authorization URL."""
        scope_str = " ".join(scopes)
        return (
            f"https://{shop_domain}/admin/oauth/authorize?"
            f"client_id={api_key}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={scope_str}"
            f"&state={uuid4()}"
        )
    
    @staticmethod
    def exchange_code_for_token(
        shop_domain: str,
        api_key: str,
        api_secret: str,
        code: str,
    ) -> Dict[str, Any]:
        """Exchange OAuth code for access token."""
        try:
            response = requests.post(
                f"https://{shop_domain}/admin/oauth/access_token",
                json={
                    "client_id": api_key,
                    "client_secret": api_secret,
                    "code": code,
                },
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise IntegrationError(f"Failed to exchange code: {e}")
    
    @staticmethod
    def fetch_sales_data(
        shop_domain: str,
        access_token: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch sales orders from Shopify."""
        try:
            headers = {
                "X-Shopify-Access-Token": access_token,
                "Content-Type": "application/json",
            }
            
            params = {"limit": 250, "status": "any"}
            if start_date:
                params["created_at_min"] = start_date
            if end_date:
                params["created_at_max"] = end_date
            
            response = requests.get(
                f"https://{shop_domain}/admin/api/2024-01/orders.json",
                headers=headers,
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            
            orders = response.json().get("orders", [])
            
            # Transform to standard format
            sales_records = []
            for order in orders:
                for line_item in order.get("line_items", []):
                    sales_records.append({
                        "date": order["created_at"][:10],
                        "store_id": "shopify",
                        "product_id": line_item.get("product_id"),
                        "sales_qty": line_item.get("quantity", 0),
                        "price": float(line_item.get("price", 0)),
                        "promotion": 1 if order.get("discount_codes") else 0,
                        "external_order_id": order["id"],
                    })
            
            return sales_records
        except requests.RequestException as e:
            raise IntegrationError(f"Failed to fetch Shopify data: {e}")


class SquareIntegration:
    """Square POS OAuth and data sync."""
    
    OAUTH_AUTHORIZE_URL = "https://connect.squareupdat.com/oauth2/authorize"
    TOKEN_URL = "https://connect.squareupddat.com/oauth2/token"
    
    @staticmethod
    def get_oauth_url(client_id: str, redirect_uri: str, scopes: List[str]) -> str:
        """Generate Square OAuth authorization URL."""
        scope_str = " ".join(scopes)
        return (
            f"https://connect.squareup.com/oauth2/authorize?"
            f"client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={scope_str}"
            f"&response_type=code"
            f"&state={uuid4()}"
        )
    
    @staticmethod
    def exchange_code_for_token(
        client_id: str,
        client_secret: str,
        code: str,
        redirect_uri: str,
    ) -> Dict[str, Any]:
        """Exchange OAuth code for access token."""
        try:
            response = requests.post(
                "https://connect.squareup.com/oauth2/token",
                json={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise IntegrationError(f"Failed to exchange code: {e}")
    
    @staticmethod
    def fetch_sales_data(
        access_token: str,
        location_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch transactions from Square."""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            
            params = {
                "begin_time": start_date or "2023-01-01T00:00:00Z",
                "end_time": end_date or datetime.now(timezone.utc).isoformat(),
                "sort_order": "DESC",
            }
            
            response = requests.get(
                f"https://connect.squareup.com/v2/locations/{location_id}/transactions",
                headers=headers,
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            
            transactions = response.json().get("transactions", [])
            
            # Transform to standard format
            sales_records = []
            for txn in transactions:
                if txn.get("tenders"):
                    sales_records.append({
                        "date": txn.get("created_at")[:10],
                        "store_id": f"square-{location_id}",
                        "product_id": "pos_transaction",
                        "sales_qty": 1,
                        "price": float(txn.get("total_money", {}).get("amount", 0)) / 100,
                        "promotion": 0,  # Not available in Square API easily
                        "external_transaction_id": txn["id"],
                    })
            
            return sales_records
        except requests.RequestException as e:
            raise IntegrationError(f"Failed to fetch Square data: {e}")


class WebhookIntegration:
    """Custom webhook receiver for sales data."""
    
    @staticmethod
    def verify_webhook_signature(
        payload: str,
        signature: str,
        secret: str,
    ) -> bool:
        """Verify webhook signature."""
        computed_sig = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(computed_sig, signature)
    
    @staticmethod
    def process_webhook_data(
        data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Process webhook data into standard format."""
        records = []
        
        # Handle array or single record
        items = data.get("items", [data] if "date" in data else [])
        
        for item in items:
            record = {
                "date": item.get("date", datetime.now(timezone.utc).isoformat()[:10]),
                "store_id": item.get("store_id", "webhook"),
                "product_id": item.get("product_id", "unknown"),
                "sales_qty": int(item.get("sales_qty", 0)),
                "price": float(item.get("price", 0)),
                "promotion": int(item.get("promotion", 0)),
            }
            records.append(record)
        
        return records


def register_integration(
    user_id: int,
    integration_type: str,
    api_key: str,
    api_secret: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """Register a new integration."""
    
    integration_id = str(uuid4())
    config = IntegrationConfig(
        integration_type=integration_type,
        api_key=api_key,
        api_secret=api_secret,
        user_id=user_id,
        **kwargs,
    )
    
    _integrations_registry[integration_id] = {
        "config": config,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_error": None,
    }
    
    logger.info(f"Registered {integration_type} integration: {integration_id}")
    return integration_id


def sync_integration(integration_id: str) -> Dict[str, Any]:
    """Sync data from a registered integration."""
    
    if integration_id not in _integrations_registry:
        raise IntegrationError(f"Integration not found: {integration_id}")
    
    registry_entry = _integrations_registry[integration_id]
    config = registry_entry["config"]
    
    try:
        if config.integration_type == "shopify":
            # Requires shop_domain and access_token in config
            raise NotImplementedError("Shopify sync requires shop_domain")
        
        elif config.integration_type == "square":
            # Requires access_token and location_id
            raise NotImplementedError("Square sync requires access_token and location_id")
        
        elif config.integration_type == "webhook":
            # Webhooks are push-based, not pull-based
            raise IntegrationError("Webhooks are push-based, use POST /integrations/webhook/{id}")
        
        else:
            raise IntegrationError(f"Unknown integration type: {config.integration_type}")
    
    except Exception as e:
        registry_entry["last_error"] = str(e)
        logger.error(f"Sync failed for {integration_id}: {e}")
        raise


def list_integrations(user_id: int) -> List[Dict[str, Any]]:
    """List all integrations for a user."""
    
    integrations = []
    for integration_id, entry in _integrations_registry.items():
        config = entry["config"]
        if config.user_id == user_id:
            integrations.append({
                "id": integration_id,
                "type": config.integration_type,
                "status": config.status,
                "last_sync": config.last_sync,
                "last_error": entry.get("last_error"),
                "created_at": entry["created_at"],
            })
    
    return integrations


def get_integration(integration_id: str) -> Optional[IntegrationConfig]:
    """Get integration config by ID."""
    
    if integration_id in _integrations_registry:
        return _integrations_registry[integration_id]["config"]
    
    return None
