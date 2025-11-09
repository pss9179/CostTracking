"""FastAPI application main entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from llmobserve.config import settings
from llmobserve.storage.db import init_db
from llmobserve.storage.repo import SpanRepository
from llmobserve.tracing.enrichers import SpanEnricher, add_tenant_baggage
from llmobserve.tracing.instrumentors.base import instrumentor_registry
from llmobserve.tracing.instrumentors.openai_instr import OpenAIInstrumentor
from llmobserve.tracing.instrumentors.pinecone_instr import PineconeInstrumentor
from llmobserve.tracing.otel_setup import setup_tracing

from .routers import demo, health, spans

# TODO: Production hardening
# 1. Add rate limiting middleware
# 2. Implement authentication/authorization
# 3. Add Prometheus metrics endpoint
# 4. Implement health check with dependency checks (DB, etc.)
# 5. Add request ID middleware for better tracing
# 6. Support Supabase RLS policies for tenant isolation
# 7. Add export formats (Jaeger, Zipkin) via OTLP
# 8. Implement alerting for cost thresholds

# Global span repository and enricher
span_repo = SpanRepository()
span_enricher = SpanEnricher(span_repo=span_repo)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Startup
    setup_tracing()
    
    # Initialize database
    init_db()
    
    # Register and apply instrumentors
    openai_instr = OpenAIInstrumentor(span_enricher=span_enricher)
    instrumentor_registry.register(openai_instr)
    
    pinecone_instr = PineconeInstrumentor(span_enricher=span_enricher)
    instrumentor_registry.register(pinecone_instr)
    
    instrumentor_registry.instrument_all()
    
    yield
    
    # Shutdown
    span_enricher.shutdown()
    instrumentor_registry.uninstrument_all()


app = FastAPI(
    title="LLM Observability Demo",
    description="OpenTelemetry-based LLM observability with auto-instrumentation",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    """Extract tenant_id from header and add to context."""
    tenant_id = request.headers.get(settings.tenant_header, "default")
    add_tenant_baggage(tenant_id)
    
    # Add to request state for access in routes
    request.state.tenant_id = tenant_id
    
    response = await call_next(request)
    return response


# Register routers
app.include_router(health.router, tags=["health"])
app.include_router(demo.router, prefix="/demo", tags=["demo"])
app.include_router(spans.router, prefix="/spans", tags=["spans"])

