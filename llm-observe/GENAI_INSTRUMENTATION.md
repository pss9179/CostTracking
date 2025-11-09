# OpenTelemetry GenAI Instrumentation

This document describes how to use the official OpenTelemetry GenAI instrumentation library with this observability platform.

## Overview

The platform now supports two modes of OpenAI instrumentation:

1. **Custom Instrumentation (Default)**: Uses our custom `OpenAIInstrumentor` with custom span attributes
2. **Official GenAI Instrumentation**: Uses `opentelemetry-instrumentation-openai` which follows GenAI semantic conventions

## Installation

The required packages are already included in `pyproject.toml`:

```bash
pip install opentelemetry-instrumentation-openai>=0.45.0
pip install opentelemetry-instrumentation>=0.45.0
```

Or install all dependencies:

```bash
pip install -e ".[dev]"
```

## Configuration

Add to your `.env` file:

```bash
# Use official OpenTelemetry GenAI instrumentation
USE_GENAI_INSTRUMENTOR=true  # Set to 'true' to enable, 'false' (default) to use custom
```

## What Gets Captured

When `USE_GENAI_INSTRUMENTOR=true`, the official instrumentation automatically captures:

### Standard GenAI Semantic Conventions

- **Token Usage**: `gen_ai.token.count` (prompt, completion, total)
- **Model Information**: `gen_ai.model.name`
- **Request Parameters**: 
  - `gen_ai.request.parameters.temperature`
  - `gen_ai.request.parameters.top_p`
  - `gen_ai.request.parameters.max_tokens`
  - `gen_ai.request.parameters.n` (number of completions)
- **Latency**: Automatically calculated span duration
- **Request/Response Content**: If enabled via instrumentation configuration

### Custom Attributes (Still Added)

Our `SpanEnricher` still adds:
- Cost calculations (`llm.cost_usd`)
- Tenant ID (`workflow.tenant_id`)
- Custom metadata for our dashboard

## Code Examples

### _generate_query Function

```python
async def _generate_query(topic: str) -> str:
    """
    Generate a search query using GPT.
    
    With USE_GENAI_INSTRUMENTOR=true:
    - Official OpenTelemetry GenAI instrumentation automatically captures:
      * Token usage (gen_ai.token.count)
      * Model name (gen_ai.model.name)
      * Temperature, top_p, max_tokens (gen_ai.request.parameters.*)
      * Latency (automatically calculated)
      * Request/response content (if enabled)
    
    With USE_GENAI_INSTRUMENTOR=false (default):
    - Custom OpenAI instrumentor captures similar data with custom attributes
    
    The span automatically inherits from the current context (root workflow span).
    """
    import openai
    
    client = openai.OpenAI(api_key=settings.openai_api_key)
    
    # Auto-instrumentation (official or custom) will automatically:
    # 1. Create a span for this API call
    # 2. Capture token usage, model, parameters, latency
    # 3. Link it to the parent span (workflow root)
    # 4. Enrich with cost and other metadata
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a search query generator."},
            {"role": "user", "content": f"Generate a search query for: {topic}"},
        ],
        max_tokens=50,
        temperature=0.7,  # Will be captured by GenAI instrumentor
        top_p=1.0,  # Will be captured by GenAI instrumentor
    )
    
    return response.choices[0].message.content
```

### _summarize_results Function

```python
async def _summarize_results(query: str, retrieval_results: list) -> str:
    """
    Summarize retrieval results using GPT.
    
    Same auto-instrumentation behavior as _generate_query.
    """
    import openai
    
    client = openai.OpenAI(api_key=settings.openai_api_key)
    
    context = "\n".join([
        result.get("metadata", {}).get("text", str(result))
        for result in retrieval_results[:3]
    ])
    
    # Auto-instrumentation captures all parameters automatically
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a summarization assistant."},
            {"role": "user", "content": f"Query: {query}\n\nContext:\n{context[:500]}\n\nSummarize."},
        ],
        max_tokens=150,
        temperature=0.5,  # Will be captured by GenAI instrumentor
        top_p=0.9,  # Will be captured by GenAI instrumentor
    )
    
    return response.choices[0].message.content
```

## Trace Tree Structure

The trace hierarchy remains the same regardless of instrumentation mode:

```
agent.workflow (root span)
├── llm.request (GPT query generation)
├── pinecone.query (vector search)
└── llm.request (GPT summarization)
```

All spans automatically inherit from the parent workflow span, maintaining proper parent-child relationships.

## Pinecone Instrumentation

**Note**: Pinecone instrumentation remains manual/custom regardless of the `USE_GENAI_INSTRUMENTOR` setting. This is because there isn't an official GenAI instrumentor for Pinecone yet. Our custom `PineconeInstrumentor` continues to work as before.

## Switching Between Modes

1. **To use official GenAI instrumentation:**
   ```bash
   echo "USE_GENAI_INSTRUMENTOR=true" >> .env
   ```

2. **To use custom instrumentation (default):**
   ```bash
   echo "USE_GENAI_INSTRUMENTOR=false" >> .env
   # Or simply remove/comment out the line
   ```

3. **Restart the backend:**
   ```bash
   make dev-backend
   ```

## Benefits of Official GenAI Instrumentation

1. **Standard Semantic Conventions**: Follows OpenTelemetry GenAI semantic conventions for interoperability
2. **Automatic Parameter Capture**: Captures temperature, top_p, max_tokens, etc. automatically
3. **Better Tooling Support**: Works seamlessly with GenAI-aware observability tools
4. **Future-Proof**: Aligns with OpenTelemetry's direction for GenAI observability

## Troubleshooting

### Instrumentation Not Working

1. **Check installation:**
   ```bash
   pip list | grep opentelemetry-instrumentation-openai
   ```

2. **Check logs:**
   Look for "Using official OpenTelemetry GenAI instrumentation" in startup logs

3. **Verify .env:**
   ```bash
   grep USE_GENAI_INSTRUMENTOR .env
   ```

### Spans Not Appearing

- Ensure the backend is restarted after changing `USE_GENAI_INSTRUMENTOR`
- Check that OpenAI calls are being made within an active OpenTelemetry context
- Verify spans are being written to the database (check logs)

## References

- [OpenTelemetry GenAI Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/genai/)
- [opentelemetry-instrumentation-openai](https://pypi.org/project/opentelemetry-instrumentation-openai/)

