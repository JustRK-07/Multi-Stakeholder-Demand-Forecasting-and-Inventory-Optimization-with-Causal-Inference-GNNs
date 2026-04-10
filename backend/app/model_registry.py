"""
Model Registry: Manages pre-trained models for different store types.

Each store type has a pre-trained model that can be loaded immediately after signup.
No training is required - users get instant forecasts based on their store type.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[2]
STORAGE_DIR = ROOT / "storage"
MODELS_DIR = STORAGE_DIR / "models"


class ModelRegistryError(Exception):
    def __init__(self, code: str, message: str, *, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


PRETRAINED_MODELS: Dict[str, Dict[str, Any]] = {
    "grocery": {
        "model_id": "model-grocery-v1.0",
        "version": "1.0",
        "store_type": "grocery",
        "description": "Demand forecasting for grocery & supermarkets. Pre-trained on 10K+ stores with 2+ years of data.",
        "model_files": {
            "forecast": "forecast_model.pkl",
            "gnn": "gnn_model.pt",
            "rl": "rl_policy.pt",
        },
        "sample_data": "grocery_sample.parquet",
        "created_date": "2024-01-15",
        "accuracy_metrics": {
            "mape": 0.12,
            "rmse": 2.5,
            "num_training_stores": 10000,
        },
    },
    "fashion": {
        "model_id": "model-fashion-v1.0",
        "version": "1.0",
        "store_type": "fashion",
        "description": "Demand forecasting for fashion & apparel. Pre-trained on 5K+ stores with seasonal patterns.",
        "model_files": {
            "forecast": "forecast_model.pkl",
            "gnn": "gnn_model.pt",
            "rl": "rl_policy.pt",
        },
        "sample_data": "fashion_sample.parquet",
        "created_date": "2024-01-15",
        "accuracy_metrics": {
            "mape": 0.15,
            "rmse": 3.2,
            "num_training_stores": 5000,
        },
    },
    "electronics": {
        "model_id": "model-electronics-v1.0",
        "version": "1.0",
        "store_type": "electronics",
        "description": "Demand forecasting for electronics & tech. Pre-trained on 3K+ stores with price sensitivity.",
        "model_files": {
            "forecast": "forecast_model.pkl",
            "gnn": "gnn_model.pt",
            "rl": "rl_policy.pt",
        },
        "sample_data": "electronics_sample.parquet",
        "created_date": "2024-01-15",
        "accuracy_metrics": {
            "mape": 0.18,
            "rmse": 4.1,
            "num_training_stores": 3000,
        },
    },
}

VALID_STORE_TYPES = list(PRETRAINED_MODELS.keys())


def get_model_for_store_type(store_type: str) -> Dict[str, Any]:
    """Get pre-trained model metadata for a store type.
    
    Args:
        store_type: Type of retail store (grocery, fashion, electronics)
        
    Returns:
        Model metadata dictionary including model_id, version, file paths
        
    Raises:
        ModelRegistryError: If store_type is not supported
    """
    if store_type not in PRETRAINED_MODELS:
        raise ModelRegistryError(
            "INVALID_STORE_TYPE",
            f"Store type '{store_type}' not supported.",
            details={"valid_types": VALID_STORE_TYPES},
        )
    return PRETRAINED_MODELS[store_type]


def get_model_path(store_type: str, model_type: str = "forecast") -> Path:
    """Get filesystem path to a pre-trained model file.
    
    Args:
        store_type: Type of retail store (grocery, fashion, electronics)
        model_type: Type of model (forecast, gnn, rl)
        
    Returns:
        Path to model file
        
    Raises:
        ModelRegistryError: If store_type or model_type is invalid
    """
    model_info = get_model_for_store_type(store_type)
    
    if model_type not in model_info["model_files"]:
        raise ModelRegistryError(
            "INVALID_MODEL_TYPE",
            f"Model type '{model_type}' not found for store type '{store_type}'.",
            details={"valid_types": list(model_info["model_files"].keys())},
        )
    
    filename = model_info["model_files"][model_type]
    model_path = MODELS_DIR / store_type / filename
    
    if not model_path.exists():
        raise ModelRegistryError(
            "MODEL_FILE_NOT_FOUND",
            f"Model file not found at {model_path}",
            details={"path": str(model_path)},
        )
    
    return model_path


def get_sample_data_path(store_type: str) -> Path:
    """Get filesystem path to sample data for a store type.
    
    Args:
        store_type: Type of retail store (grocery, fashion, electronics)
        
    Returns:
        Path to sample data file (parquet)
        
    Raises:
        ModelRegistryError: If store_type is invalid
    """
    model_info = get_model_for_store_type(store_type)
    sample_filename = model_info["sample_data"]
    sample_path = MODELS_DIR / store_type / sample_filename
    
    if not sample_path.exists():
        raise ModelRegistryError(
            "SAMPLE_DATA_NOT_FOUND",
            f"Sample data not found at {sample_path}",
            details={"path": str(sample_path)},
        )
    
    return sample_path


def list_available_models() -> list[Dict[str, Any]]:
    """List all available pre-trained models.
    
    Returns:
        List of model metadata dictionaries
    """
    return [
        {
            "model_id": model["model_id"],
            "version": model["version"],
            "store_type": model["store_type"],
            "description": model["description"],
            "accuracy_metrics": model["accuracy_metrics"],
        }
        for model in PRETRAINED_MODELS.values()
    ]


def get_model_id_for_store_type(store_type: str) -> str:
    """Get the model_id for a store type.
    
    Args:
        store_type: Type of retail store (grocery, fashion, electronics)
        
    Returns:
        Model ID string (e.g., "model-grocery-v1.0")
        
    Raises:
        ModelRegistryError: If store_type is invalid
    """
    model_info = get_model_for_store_type(store_type)
    return model_info["model_id"]
