"""
FastAPI main application for LLM Observe Collector.
"""
import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
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
    provider_tiers,
)
from cap_monitor import run_cap_monitor

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LLM Observe Collector",
    description="Cost observability collector for LLM and API usage",
    version="0.2.0"  # SaaS version
)

# CORS middleware - configure based on environment
import os
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
if ALLOWED_ORIGINS == ["*"]:
    # Development: allow all
    allow_origins = ["*"]
else:
    # Production: specific domains
    allow_origins = [origin.strip() for origin in ALLOWED_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],  # Explicitly allow localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add CORS headers to error responses
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )
    return response

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )
    return response

# Background task for cap monitoring
cap_monitor_task = None

# Initialize database on startup
@app.on_event("startup")
async def on_startup():
    """Initialize database tables and start background services."""
    try:
        init_db()
        run_migrations()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        # Don't crash the app - it might connect later
        # Healthcheck will still work
    
    # Start cap monitor in background
    try:
        global cap_monitor_task
        cap_monitor_task = asyncio.create_task(run_cap_monitor(check_interval_seconds=300))
        logger.info("Started cap monitor background service")
    except Exception as e:
        logger.error(f"Failed to start cap monitor: {e}", exc_info=True)

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
app.include_router(provider_tiers.router)  # Provider tier configuration
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

