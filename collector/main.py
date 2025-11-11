"""
FastAPI main application for LLM Observe Collector.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db import init_db, run_migrations
from routers import events, runs, insights, pricing, stats, tenants, auth, dashboard

# Create FastAPI app
app = FastAPI(
    title="LLM Observe Collector",
    description="Cost observability collector for LLM and API usage",
    version="0.1.0"
)

# CORS middleware - allow all origins for MVP
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def on_startup():
    """Initialize database tables on startup."""
    init_db()
    run_migrations()


# Health check
@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "llmobserve-collector"}


# Include routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(events.router)
app.include_router(runs.router)
app.include_router(insights.router)
app.include_router(pricing.router)
app.include_router(stats.router)
app.include_router(tenants.router)

