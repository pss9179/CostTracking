"""Model pricing registry and cost calculation."""

import json
from pathlib import Path
from typing import Optional, Dict, Any


class PricingRegistry:
    """Registry for LLM model pricing."""

    def __init__(self, prices: Optional[Dict[str, Any]] = None):
        """Initialize with prices dict or load defaults."""
        if prices:
            self._prices = prices
        else:
            self._prices = self._default_model_prices()

    @staticmethod
    def _default_model_prices() -> dict:
        """Default model pricing for LLMs, vector DBs, embeddings, and inference APIs."""
        return {
            # OpenAI models (per 1M tokens)
            "gpt-4o": {"prompt": 2.50, "completion": 10.00},
            "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
            "gpt-4-turbo": {"prompt": 10.00, "completion": 30.00},
            "gpt-4": {"prompt": 30.00, "completion": 60.00},
            "gpt-3.5-turbo": {"prompt": 0.50, "completion": 1.50},
            "text-embedding-3-small": {"prompt": 0.02, "completion": 0.0},
            # Anthropic models (per 1M tokens)
            "claude-3-5-sonnet": {"prompt": 3.00, "completion": 15.00},
            "claude-3-opus": {"prompt": 15.00, "completion": 75.00},
            "claude-3-haiku": {"prompt": 0.25, "completion": 1.25},
            # Vector Database pricing
            "pinecone-query": {"request": 0.000096},
            "pinecone-upsert": {"vector": 0.0000012},
        }

    def get_price(self, model: str) -> Optional[dict]:
        """Get pricing for a model (prompt and completion per 1M tokens)."""
        # Try exact match first
        if model in self._prices:
            return self._prices[model]

        # Try partial match (e.g., "gpt-4o-2024-08-06" -> "gpt-4o")
        for key, value in self._prices.items():
            if model.startswith(key):
                return value

        return None

    def cost_for(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """
        Calculate cost in USD for a model call.

        Args:
            model: Model name (e.g., "gpt-4o")
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Cost in USD (0.0 if pricing not found)
        """
        price = self.get_price(model)
        if not price:
            return 0.0

        prompt_cost = (prompt_tokens / 1_000_000) * price.get("prompt", 0.0)
        completion_cost = (completion_tokens / 1_000_000) * price.get("completion", 0.0)

        return prompt_cost + completion_cost

    def cost_for_vector_db(
        self,
        provider: str,
        operation: str,
        request_size: int = 1,
    ) -> float:
        """
        Calculate cost in USD for a vector database operation.

        Args:
            provider: Provider name (e.g., "pinecone")
            operation: Operation type (e.g., "query", "upsert")
            request_size: Number of requests/vectors (default: 1)

        Returns:
            Cost in USD (0.0 if pricing not found)
        """
        # Build pricing key: "{provider}-{operation}"
        pricing_key = f"{provider}-{operation}"
        price = self.get_price(pricing_key)
        if not price:
            return 0.0

        # Support both "request" and "vector" pricing structures
        if "request" in price:
            price_per_unit = price["request"]
            return request_size * price_per_unit
        elif "vector" in price:
            price_per_vector = price["vector"]
            return request_size * price_per_vector
        else:
            return 0.0

    def update_prices(self, prices: dict) -> None:
        """Update pricing registry."""
        self._prices.update(prices)


def get_price(provider: str, model: Optional[str] = None, usage: Optional[Dict[str, int]] = None) -> float:
    """
    Helper function to get price for a provider/model combination.

    Args:
        provider: Provider name (e.g., "openai", "pinecone")
        model: Model name (e.g., "gpt-4o") - optional for LLMs
        usage: Usage dict with keys like "prompt_tokens", "completion_tokens", "request_size"

    Returns:
        Cost in USD
    """
    registry = pricing_registry
    
    # Handle vector DB operations
    if provider in ["pinecone", "weaviate", "qdrant"] and usage and "operation" in usage:
        return registry.cost_for_vector_db(
            provider=provider,
            operation=usage["operation"],
            request_size=usage.get("request_size", 1)
        )
    
    # Handle LLM operations
    if model and usage:
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        return registry.cost_for(model, prompt_tokens, completion_tokens)
    
    return 0.0


# Global pricing registry
pricing_registry = PricingRegistry()
