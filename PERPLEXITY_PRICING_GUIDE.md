# Perplexity API Pricing Guide

## Overview

Perplexity has a unique dual pricing model that combines:
1. **Token-based costs** (input/output tokens)
2. **Request-based fees** (varies by context size for most models)
3. **Special token types** (citation, reasoning, search queries for Deep Research)

## Supported Models

### 1. Search API
```python
from llmobserve.pricing import compute_cost

# Search API is request-based only (no tokens)
cost = compute_cost(
    provider="perplexity",
    model="search-api"
)
# Returns: $0.005 per request ($5 per 1,000 requests)
```

### 2. Sonar Models (Token + Request Fees)

**Context Size Tiers:**
- `low`: Low context usage
- `medium`: Medium context usage  
- `high`: High context usage

```python
# Sonar with low context
cost = compute_cost(
    provider="perplexity",
    model="sonar",
    input_tokens=1000,
    output_tokens=500,
    context_size="low"
)
# Returns: (1000 * $0.000001) + (500 * $0.000001) + ($5 / 1000)
#        = $0.001 + $0.0005 + $0.005 = $0.0065

# Sonar with high context
cost = compute_cost(
    provider="perplexity",
    model="sonar",
    input_tokens=1000,
    output_tokens=500,
    context_size="high"
)
# Returns: (1000 * $0.000001) + (500 * $0.000001) + ($12 / 1000)
#        = $0.001 + $0.0005 + $0.012 = $0.0135
```

### 3. Sonar Pro (Higher Token Costs)
```python
cost = compute_cost(
    provider="perplexity",
    model="sonar-pro",
    input_tokens=1000,
    output_tokens=500,
    context_size="medium"
)
# Returns: (1000 * $0.000003) + (500 * $0.000015) + ($10 / 1000)
#        = $0.003 + $0.0075 + $0.01 = $0.0205
```

### 4. Sonar Reasoning Models
```python
# Sonar Reasoning
cost = compute_cost(
    provider="perplexity",
    model="sonar-reasoning",
    input_tokens=1000,
    output_tokens=2000,
    context_size="low"
)
# Returns: (1000 * $0.000001) + (2000 * $0.000005) + ($5 / 1000)
#        = $0.001 + $0.01 + $0.005 = $0.016

# Sonar Reasoning Pro
cost = compute_cost(
    provider="perplexity",
    model="sonar-reasoning-pro",
    input_tokens=1000,
    output_tokens=2000,
    context_size="medium"
)
# Returns: (1000 * $0.000002) + (2000 * $0.000008) + ($8 / 1000)
#        = $0.002 + $0.016 + $0.008 = $0.026
```

### 5. Sonar Deep Research (Most Complex)

Deep Research has **5 cost components**:
1. Input tokens
2. Output tokens
3. Citation tokens
4. Reasoning tokens
5. Search queries

```python
cost = compute_cost(
    provider="perplexity",
    model="sonar-deep-research",
    input_tokens=5000,
    output_tokens=3000,
    citation_tokens=1000,
    reasoning_tokens=2000,
    search_queries=10
)
# Returns:
# Input:     5000 * $0.000002 = $0.010
# Output:    3000 * $0.000008 = $0.024
# Citations: 1000 * $0.000002 = $0.002
# Reasoning: 2000 * $0.000003 = $0.006
# Searches:    10 * ($5/1000) = $0.050
# Total: $0.092
```

## Important Notes

### No Request Fees for Deep Research
Unlike other Sonar models, Deep Research does **NOT** have context-size-based request fees. It only has:
- Token costs (input/output/citation/reasoning)
- Search query costs

### Context Size Detection
Your instrumentor should detect context size from the API response metadata. If not available, default to `"medium"` for cost estimation.

### Extracting Special Token Counts
For Deep Research, you'll need to parse the API response to extract:
```json
{
  "usage": {
    "prompt_tokens": 5000,
    "completion_tokens": 3000,
    "citation_tokens": 1000,      // ← Extract this
    "reasoning_tokens": 2000,     // ← Extract this
    "search_queries": 10          // ← Extract this
  }
}
```

## Integration with Instrumentor

When instrumenting Perplexity API calls, extract and pass all relevant parameters:

```python
from llmobserve.pricing import compute_cost

def track_perplexity_call(response):
    usage = response.get("usage", {})
    model = response.get("model", "sonar")
    
    # Extract token counts
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    
    # Extract special tokens (Deep Research)
    citation_tokens = usage.get("citation_tokens", 0)
    reasoning_tokens = usage.get("reasoning_tokens", 0)
    search_queries = usage.get("search_queries", 0)
    
    # Detect context size (if available in response metadata)
    context_size = response.get("context_size", "medium")  # Default to medium
    
    # Compute cost
    cost = compute_cost(
        provider="perplexity",
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        context_size=context_size,
        citation_tokens=citation_tokens,
        reasoning_tokens=reasoning_tokens,
        search_queries=search_queries
    )
    
    return cost
```

## Pricing Summary Table

| Model | Input | Output | Request Fee (Low/Med/High) | Special Tokens |
|-------|-------|--------|---------------------------|----------------|
| Search API | N/A | N/A | $5/1k requests | N/A |
| Sonar | $1/M | $1/M | $5/$8/$12 per 1k | N/A |
| Sonar Pro | $3/M | $15/M | $6/$10/$14 per 1k | N/A |
| Sonar Reasoning | $1/M | $5/M | $5/$8/$12 per 1k | N/A |
| Sonar Reasoning Pro | $2/M | $8/M | $6/$10/$14 per 1k | N/A |
| Deep Research | $2/M | $8/M | None | Citations ($2/M), Reasoning ($3/M), Searches ($5/1k) |

## Testing

See `scripts/test_perplexity_pricing.py` for comprehensive test cases.

