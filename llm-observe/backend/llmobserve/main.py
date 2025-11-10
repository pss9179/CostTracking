"""FastAPI application main entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from llmobserve.api.routes import router
from llmobserve.exporter import get_exporter
from llmobserve.middleware import tenant_middleware
from llmobserve.tracer import init_tracer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Startup
    # Don't call init_db() here - let tests control database setup
    # In production, init_db() should be called explicitly
    try:
        from llmobserve.db import init_db
        init_db()
    except Exception:
        pass  # Allow tests to skip this
    
    init_tracer()
    get_exporter()  # Start exporter
    
    yield
    
    # Shutdown
    exporter = get_exporter()
    exporter.stop()


app = FastAPI(
    title="LLMObserve",
    description="Lightweight AI usage and cost tracking",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tenant/workflow middleware
app.middleware("http")(tenant_middleware)

# API routes
app.include_router(router, prefix="/api", tags=["api"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "LLMObserve API", "version": "0.1.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

