# LLM Cost Observability Stack

An MVP observability stack for tracking LLM and API costs with automatic instrumentation.

## Architecture

```
┌─────────────────┐
│   Your App      │
│  + llmobserve   │  ← Auto-instruments OpenAI & Pinecone
│     SDK         │
└────────┬────────┘
         │ POST /events
         ↓
┌─────────────────┐
│  Collector API  │  ← FastAPI + SQLite
│   (port 8000)   │  ← Computes insights
└────────┬────────┘
         │ GET /runs, /insights
         ↓
┌─────────────────┐
│   Dashboard     │  ← Next.js + shadcn/ui
│   (port 3000)   │  ← Shows costs, anomalies
└─────────────────┘
```

## Components

- **`/collector`** - FastAPI backend with SQLite for event storage and insights
- **`/sdk/python`** - Python SDK (`llmobserve`) with auto-instrumentation
- **`/web`** - Next.js dashboard for visualizing costs and runs
- **`/scripts`** - Test scripts for generating sample data
- **`/shared`** - Shared schemas and types

## Quick Start

### 1. Install Dependencies

```bash
# Install all components
make install

# Or install individually:
make install-api    # Collector API
make install-sdk    # Python SDK
make install-web    # Next.js dashboard
```

### 2. Start the Collector API

```bash
make dev-api
```

The API will start on `http://localhost:8000`. Database auto-migrates on startup.

### 3. Generate Test Data

```bash
make seed
```

This runs a test script that simulates LLM calls with varying patterns to trigger insights.

### 4. Start the Dashboard

```bash
make dev-web
```

Open `http://localhost:3000` to view the dashboard.

## Using the SDK

### Basic Usage

```python
from llmobserve import observe, section
from openai import OpenAI

# Initialize observability
observe(collector_url="http://localhost:8000")

# Use sections to label different parts of your flow
with section("retrieval"):
    # Your Pinecone queries here
    pass

with section("reasoning"):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    # Automatically tracked!
```

### Hierarchical Tracing (Optional)

**NEW:** Track nested agent, tool, and step calls with semantic labels:

```python
from llmobserve import observe, section, trace

observe("http://localhost:8000")

# Nested sections with semantic labels
with section("agent:researcher"):
    with section("tool:web_search"):
        # OpenAI call for search
        client.chat.completions.create(...)
    
    with section("step:analyze_results"):
        # OpenAI call for analysis
        client.chat.completions.create(...)

# Or use the @trace decorator
@trace(agent="researcher")
async def research_agent(query: str):
    result = await search_web(query)
    return await analyze(result)
```

**Dashboard displays interactive tree:**
```
agent:researcher (expand/collapse)
├─ tool:web_search       $0.002  [ok]
└─ step:analyze_results  $0.001  [ok]
```

**Learn more:** See [`docs/semantic_sections.md`](./docs/semantic_sections.md) for complete guide.

## API Endpoints

### Collector API (port 8000)

- `GET /health` - Health check
- `POST /events` - Ingest trace events (batch)
- `GET /runs/latest` - List recent runs with totals
- `GET /runs/{run_id}` - Detailed breakdown for a run
- `GET /insights/daily` - Auto-generated insights for last 24h
- `GET /pricing` - Current pricing registry
- `PUT /pricing` - Update pricing registry

## Data Model

Events are stored with these key fields:

- `run_id` - Groups all calls in one user request
- `section` - Label (e.g., "retrieval", "reasoning")
- `span_type` - One of: llm, vector_db, api, other
- `provider` - e.g., openai, pinecone
- `model` - e.g., gpt-4o, text-embedding-3-small
- `input_tokens`, `output_tokens`, `cost_usd`, `latency_ms`

## Insights

The collector automatically detects:

1. **Section Spike** - Section cost > 2× vs 7-day average
2. **Model Inefficiency** - Expensive model used where cheaper works
3. **Token Bloat** - Input tokens ↑ > 1.5× vs 7-day average
4. **Retry/Loop** - Same endpoint called > 3× per run (p95)

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
OPENAI_API_KEY=sk-...          # Optional - test script mocks if missing
PINECONE_API_KEY=...           # Optional - test script mocks if missing
COLLECTOR_URL=http://localhost:8000
LLMOBSERVE_DISABLED=1          # Set to disable instrumentation
```

## Development

All Python code uses type hints. TypeScript uses strict mode.

To modify pricing, edit `collector/pricing/registry.json` or use `PUT /pricing`.

## License

MIT

