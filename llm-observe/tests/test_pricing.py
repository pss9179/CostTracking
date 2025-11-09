"""Tests for pricing calculations."""

import pytest
from llmobserve.pricing import PricingRegistry


def test_pricing_registry_get_price():
    """Test getting price for a model."""
    registry = PricingRegistry()
    
    # Test exact match
    price = registry.get_price("gpt-4o")
    assert price is not None
    assert "prompt" in price
    assert "completion" in price
    
    # Test partial match
    price = registry.get_price("gpt-4o-2024-08-06")
    assert price is not None
    
    # Test unknown model
    price = registry.get_price("unknown-model")
    assert price is None


def test_pricing_registry_cost_for():
    """Test cost calculation."""
    registry = PricingRegistry()
    
    # Test with known model
    cost = registry.cost_for("gpt-3.5-turbo", 1000, 500)
    assert cost > 0
    
    # Test with unknown model (should return 0)
    cost = registry.cost_for("unknown-model", 1000, 500)
    assert cost == 0.0
    
    # Test edge cases
    cost = registry.cost_for("gpt-3.5-turbo", 0, 0)
    assert cost == 0.0


def test_pricing_registry_update_prices():
    """Test updating prices."""
    registry = PricingRegistry()
    
    new_prices = {"custom-model": {"prompt": 1.0, "completion": 2.0}}
    registry.update_prices(new_prices)
    
    price = registry.get_price("custom-model")
    assert price == {"prompt": 1.0, "completion": 2.0}

