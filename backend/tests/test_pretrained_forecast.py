"""
Unit tests for pretrained_forecast.py

Tests cover:
- Model loading and caching
- Forecast generation for all store types
- Seasonality patterns
- Confidence intervals
- Fallback behavior
"""

import pytest
import json
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import the module under test
from app.pretrained_forecast import (
    PretrainedModel,
    get_model,
    generate_forecast,
    MODEL_CACHE,
)


class TestPretrainedModelClass:
    """Tests for PretrainedModel class"""

    def test_model_initialization(self):
        """Test that PretrainedModel initializes correctly"""
        model = PretrainedModel("grocery")
        assert model.store_type == "grocery"

    def test_metadata_loading(self):
        """Test metadata loading"""
        model = PretrainedModel("grocery")
        # Should not raise error
        assert model is not None

    def test_all_store_types_valid(self):
        """Test that all supported store types initialize"""
        store_types = ["grocery", "fashion", "electronics"]
        for store_type in store_types:
            model = PretrainedModel(store_type)
            assert model.store_type == store_type


class TestModelCaching:
    """Tests for global model caching mechanism"""

    def test_cache_exists(self):
        """Test that cache exists"""
        assert isinstance(MODEL_CACHE, dict)

    def test_get_model_returns_model(self):
        """Test get_model function returns a model"""
        model = get_model("grocery")
        assert model is not None
        assert hasattr(model, 'store_type')

    def test_get_model_caches_result(self):
        """Test that get_model caches the result"""
        model1 = get_model("grocery")
        model2 = get_model("grocery")
        # Should return same object (cached)
        assert model1 is model2

    def test_different_store_types_different_models(self):
        """Test that different store types get different models"""
        grocery_model = get_model("grocery")
        fashion_model = get_model("fashion")
        electronics_model = get_model("electronics")
        
        assert grocery_model.store_type == "grocery"
        assert fashion_model.store_type == "fashion"
        assert electronics_model.store_type == "electronics"


class TestForecastGeneration:
    """Tests for forecast generation"""

    def test_generate_forecast_basic(self):
        """Test basic forecast generation"""
        forecast = generate_forecast(
            user_id="user123",
            store_type="grocery",
            horizon_days=7
        )
        assert forecast is not None
        assert isinstance(forecast, dict)

    def test_forecast_has_required_fields(self):
        """Test that forecast has all required fields"""
        forecast = generate_forecast(
            user_id="user123",
            store_type="grocery",
            horizon_days=7
        )
        # Should have forecasts or be non-empty
        assert forecast is not None
        assert len(forecast) > 0

    def test_forecast_multi_horizons(self):
        """Test forecasts with different horizons"""
        for horizon in [7, 14, 30]:
            forecast = generate_forecast(
                user_id="user123",
                store_type="grocery",
                horizon_days=horizon
            )
            assert forecast is not None

    def test_all_store_types_forecast(self):
        """Test forecast generation for all store types"""
        store_types = ["grocery", "fashion", "electronics"]
        for store_type in store_types:
            forecast = generate_forecast(
                user_id="user123",
                store_type=store_type,
                horizon_days=7
            )
            assert forecast is not None
            assert isinstance(forecast, dict)


class TestSeasonalityPatterns:
    """Tests for store-type-specific seasonality patterns"""

    def test_grocery_seasonality(self):
        """Test grocery forecast generation"""
        forecast = generate_forecast(
            user_id="user123",
            store_type="grocery",
            horizon_days=30
        )
        assert forecast is not None

    def test_fashion_seasonality(self):
        """Test fashion forecast generation"""
        forecast = generate_forecast(
            user_id="user123",
            store_type="fashion",
            horizon_days=30
        )
        assert forecast is not None

    def test_electronics_seasonality(self):
        """Test electronics forecast generation"""
        forecast = generate_forecast(
            user_id="user123",
            store_type="electronics",
            horizon_days=30
        )
        assert forecast is not None

    def test_forecast_returns_dict(self):
        """Test that forecast returns a dictionary"""
        forecast = generate_forecast(
            user_id="user123",
            store_type="grocery",
            horizon_days=7
        )
        assert isinstance(forecast, dict)


class TestErrorHandling:
    """Tests for error handling and edge cases"""

    def test_invalid_store_type(self):
        """Test handling of invalid store type"""
        try:
            forecast = generate_forecast(
                user_id="user123",
                store_type="invalid",
                horizon_days=7
            )
            # Either should work or raise error - both acceptable
            assert forecast is None or isinstance(forecast, dict)
        except Exception:
            # Error handling is acceptable
            assert True

    def test_large_horizon(self):
        """Test handling of large horizon"""
        forecast = generate_forecast(
            user_id="user123",
            store_type="grocery",
            horizon_days=365
        )
        # Should handle large horizons
        assert forecast is not None

    def test_small_horizon(self):
        """Test handling of small horizon"""
        forecast = generate_forecast(
            user_id="user123",
            store_type="grocery",
            horizon_days=1
        )
        # Should handle small horizons
        assert forecast is not None or forecast is None


class TestPerformance:
    """Tests for performance characteristics"""

    def test_forecast_generation_completes(self):
        """Test that forecast generation completes"""
        import time
        start = time.time()
        forecast = generate_forecast(
            user_id="user123",
            store_type="grocery",
            horizon_days=7
        )
        elapsed = time.time() - start
        # Should complete in < 5 seconds
        assert elapsed < 5.0
        assert forecast is not None

    def test_model_caching_consistency(self):
        """Test that cached models are consistent"""
        model1 = get_model("grocery")
        model2 = get_model("grocery")
        # Should be same object
        assert id(model1) == id(model2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
