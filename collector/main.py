"""
FastAPI main application for LLM Observe Collector.
"""
import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db import init_db, run_migrations
from routers import (
    events,
    runs,
    insights,
    pricing,
    stats,
    dashboard,
    api_keys,
    users,
    auth_simple,
    clerk_webhook,
    clerk_api_keys,
    caps,
)
from cap_monitor import run_cap_monitor

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LLM Observe Collector",
    description="Cost observability collector for LLM and API usage",
    version="0.2.0"  # SaaS version
)

# CORS middleware - allow all origins for MVP
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Background task for cap monitoring
cap_monitor_task = None

# Initialize database on startup
@app.on_event("startup")
async def on_startup():
    """Initialize database tables and start background services."""
    init_db()
    run_migrations()
    
    # Start cap monitor in background
    global cap_monitor_task
    cap_monitor_task = asyncio.create_task(run_cap_monitor(check_interval_seconds=300))
    logger.info("Started cap monitor background service")

@app.on_event("shutdown")
async def on_shutdown():
    """Cleanup background services."""
    global cap_monitor_task
    if cap_monitor_task:
        cap_monitor_task.cancel()
        try:
            await cap_monitor_task
        except asyncio.CancelledError:
            pass
        logger.info("Stopped cap monitor background service")


# Health check
@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "llmobserve-collector", "version": "0.2.0"}


# Include routers
app.include_router(clerk_webhook.router)  # Clerk webhook (no auth required)
app.include_router(clerk_api_keys.router)  # Clerk-authenticated API keys
app.include_router(auth_simple.router)  # Simple email/password auth (legacy)
app.include_router(users.router)  # User management
app.include_router(api_keys.router)  # API key management
app.include_router(caps.router)  # Spending caps & alerts
app.include_router(dashboard.router)
app.include_router(events.router)
app.include_router(runs.router)
app.include_router(insights.router)
app.include_router(pricing.router)
app.include_router(stats.router)

