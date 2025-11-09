# LLM Observability Demo

Production-leaning LLM observability demo using OpenTelemetry + Supabase. Demonstrates auto-instrumentation of GPT calls without manual span code, with multi-tenant support, privacy controls, and a modern Next.js dashboard.

## Features

- **Auto-instrumentation**: GPT calls are automatically traced via OpenTelemetry without manual span code
- **Multi-tenant**: Tenant isolation via `x-tenant-id` header with Supabase RLS support
- **Privacy-first**: Prompts/responses hashed by default; toggle plaintext via `ALLOW_CONTENT_CAPTURE`
- **Cost tracking**: Automatic cost calculation based on model pricing
- **Modern dashboard**: Next.js 15 with shadcn/ui, React Query, and Recharts
- **OpenTelemetry-native**: Full OTel integration with Console + OTLP exporters

## Architecture

```
┌─────────────┐
│  Next.js UI │  (Dashboard + Trace Viewer)
└──────┬──────┘
       │ HTTP
┌──────▼──────┐
│  FastAPI    │  (REST API + Tenant Middleware)
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
┌──▼──┐ ┌──▼────────┐
│ GPT │ │ Supabase  │  (Postgres via SQLModel)
└─────┘ └───────────┘
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- Supabase project (or PostgreSQL database)
- OpenAI API key

### Backend Setup

1. **Clone and navigate to project:**
   ```bash
   cd llm-observe
   ```

2. **Create `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Initialize backend:**
   ```bash
   make init
   ```

4. **Run database migrations:**
   ```bash
   cd backend
   source ../venv/bin/activate
   alembic upgrade head
   ```

5. **Start backend:**
   ```bash
   make dev-backend
   ```

Backend runs on `http://localhost:8000`

### Frontend Setup

1. **Navigate to UI directory:**
   ```bash
   cd ui
   ```

2. **Install dependencies:**
   ```bash
   pnpm install
   ```

3. **Start dev server:**
   ```bash
   pnpm dev
   ```

UI runs on `http://localhost:3000`

## Usage

### Running the Demo

1. **Start both backend and UI** (in separate terminals)

2. **Visit dashboard:** `http://localhost:3000`

3. **Run demo agent workflow:**
   - Click "Run Demo" button
   - This executes an agent with 2 tool calls (search + reason)
   - Each tool calls GPT and is auto-instrumented
   - View traces and metrics in the dashboard

4. **Run fake app:**
   - Click "Run Fake App" button
   - This validates auto-instrumentation works without manual spans
   - Check console/UI for traces

### API Endpoints

- `GET /health` - Health check
- `POST /demo/run` - Run agent workflow
- `POST /demo/fake_app` - Run fake app
- `GET /spans` - List spans (tenant-scoped)
- `GET /traces/{trace_id}` - Get trace details
- `GET /traces` - List traces (tenant-scoped)
- `GET /metrics` - Get aggregated metrics

### Multi-tenancy

Set `x-tenant-id` header in requests:

```bash
curl -H "x-tenant-id: tenant-123" http://localhost:8000/spans
```

The UI proxy automatically forwards this header from browser requests.

## Privacy

By default, prompts and responses are **hashed** (SHA-256) and only hashes are stored. To enable content capture:

```env
ALLOW_CONTENT_CAPTURE=true
```

When enabled, prompt/response content is stored (truncated to 500/1000 chars for prompts/responses).

## Database Schema

### SpanSummary

- `trace_id`, `span_id`, `parent_span_id` - Trace hierarchy
- `model`, `prompt_tokens`, `completion_tokens`, `total_tokens` - Usage
- `cost_usd` - Calculated cost
- `tenant_id` - Multi-tenant isolation
- `start_time`, `duration_ms` - Timing

### Trace

- `trace_id` - Unique trace identifier
- `tenant_id` - Multi-tenant isolation
- `total_cost_usd`, `total_tokens`, `span_count` - Aggregated metrics
- `root_span_name` - Workflow name

## Production Hardening TODOs

1. **Tail sampling**: Implement tail-based sampling for high-volume traces
2. **Provider registry**: Extend instrumentor registry for Anthropic, Cohere, etc.
3. **Pricing sync**: Auto-sync model pricing from provider APIs
4. **Batching**: Batch span writes to database for better throughput
5. **RLS policies**: Document and implement Supabase RLS policies for tenant isolation
6. **Rate limiting**: Add rate limiting to API endpoints
7. **Caching**: Add Redis caching for frequently accessed traces/metrics
8. **Alerting**: Set up alerts for cost thresholds or error rates
9. **Export formats**: Support Jaeger, Zipkin export formats
10. **Metrics**: Add Prometheus metrics endpoint

## Development

### Running Tests

```bash
make test
```

### Linting

```bash
make lint
make format
```

### Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Tech Stack

**Backend:**
- FastAPI
- OpenTelemetry (API + SDK + OTLP)
- SQLModel (Supabase/Postgres)
- structlog
- Pydantic v2

**Frontend:**
- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui
- React Query
- Recharts

**Testing:**
- pytest
- pytest-cov

**Linting:**
- ruff
- black
- mypy

## License

MIT

