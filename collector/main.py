"""
FastAPI main application for Skyline Collector.
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
    voice_stats,
    settings,
    dashboard,
    api_keys,
    users,
    auth_simple,
    clerk_webhook,
    clerk_api_keys,
    caps,
    provider_tiers,
    stripe,
    projects,
    migrations,
)
from cap_monitor import run_cap_monitor

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Skyline Collector",
    description="Cost observability collector for LLM and API usage",
    version="0.2.0"  # SaaS version
)

# CORS middleware - configure based on environment
import os
ALLOWED_ORIGINS_ENV = os.getenv("ALLOWED_ORIGINS", "*")
if ALLOWED_ORIGINS_ENV == "*":
    # Development: allow all
    allow_origins = ["*"]
else:
    # Production: specific domains (comma-separated)
    allow_origins = [origin.strip() for origin in ALLOWED_ORIGINS_ENV.split(",")]
    # Always include localhost for local development
    allow_origins.extend(["http://localhost:3000", "http://localhost:3001"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,  # Use calculated origins from env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,  # Cache CORS preflight for 24 hours (reduces OPTIONS requests)
)

# Add CORS headers to error responses
def get_cors_headers(request: Request) -> dict:
    """Get CORS headers based on request origin and allowed origins."""
    origin = request.headers.get("origin")
    headers = {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }
    
    # If allow_origins includes "*", allow any origin
    if "*" in allow_origins:
        headers["Access-Control-Allow-Origin"] = origin or "*"
    elif origin and origin in allow_origins:
        headers["Access-Control-Allow-Origin"] = origin
    elif origin:
        # Origin not in allowed list, but we'll allow it for error responses
        headers["Access-Control-Allow-Origin"] = origin
    
    return headers

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=get_cors_headers(request)
    )
    return response

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=get_cors_headers(request)
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


# Warm endpoint - wakes up container AND database connection
@app.get("/warm", tags=["health"])
def warm_check():
    """
    Warm endpoint that touches the database.
    Use this to wake up both the Railway container AND the PostgreSQL connection pool.
    """
    from db import engine
    from sqlalchemy import text
    import time
    
    start = time.time()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_time = (time.time() - start) * 1000
        return {"status": "ok", "db_warm": True, "db_time_ms": round(db_time, 1)}
    except Exception as e:
        return {"status": "ok", "db_warm": False, "error": str(e)}


# Include routers
app.include_router(clerk_webhook.router)  # Clerk webhook (no auth required)
app.include_router(clerk_api_keys.router)  # Clerk-authenticated API keys
app.include_router(provider_tiers.router)  # Provider tier configuration
app.include_router(auth_simple.router)  # Simple email/password auth (legacy)
app.include_router(users.router)  # User management
app.include_router(api_keys.router)  # API key management
app.include_router(caps.router)  # Spending caps & alerts
app.include_router(stripe.router)  # Stripe subscription management
app.include_router(dashboard.router)
app.include_router(events.router)
app.include_router(runs.router)
app.include_router(insights.router)
app.include_router(pricing.router)
app.include_router(stats.router)
app.include_router(voice_stats.router)  # Voice AI stats
app.include_router(settings.router)  # User settings (pricing plans)
app.include_router(projects.router)  # Projects
app.include_router(migrations.router)  # Database migrations

