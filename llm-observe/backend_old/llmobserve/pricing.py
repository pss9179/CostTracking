"""Model pricing registry and cost calculation."""

from typing import Optional

from llmobserve.config import settings

# TODO: Production hardening
# 1. Auto-sync model pricing from provider APIs (OpenAI, Anthropic, etc.)
# 2. Cache pricing data with TTL
# 3. Support multiple pricing tiers (prompt/completion, different regions)
# 4. Add pricing history/versioning


class PricingRegistry:
    """Registry for LLM model pricing."""

    def __init__(self):
        """Initialize with prices from config."""
        self._prices = settings.load_model_prices()

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
            provider: Provider name (e.g., "weaviate", "qdrant")
            operation: Operation type (e.g., "query", "search", "upsert")
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
            # Price per request (e.g., $0.096 per 1K queries = 0.000096 per query)
            price_per_unit = price["request"]
            return request_size * price_per_unit
        elif "vector" in price:
            # Price per vector (e.g., $0.12 per 100K vectors = 0.0000012 per vector)
            price_per_vector = price["vector"]
            return request_size * price_per_vector
        else:
            return 0.0

    def update_prices(self, prices: dict) -> None:
        """Update pricing registry."""
        self._prices.update(prices)


# Global pricing registry
pricing_registry = PricingRegistry()

