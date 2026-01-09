"""
FastAPI main application for Skyline Collector.
"""
import asyncio
import logging
from fastapi import FastAPI, Request, Header
from typing import Optional
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
    version="0.3.7-data-isolation-fix"  # Complete data isolation fix - all endpoints use tenant_id/clerk_user_id filtering
)

# CORS middleware - configure based on environment
import os
ALLOWED_ORIGINS_ENV = os.getenv("ALLOWED_ORIGINS", "*")

# Build list of allowed origins
allow_origins = []
if ALLOWED_ORIGINS_ENV == "*":
    # Development: allow common origins
    allow_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]
else:
    # Production: specific domains (comma-separated)
    allow_origins = [origin.strip() for origin in ALLOWED_ORIGINS_ENV.split(",")]

# Always add known production domains
production_origins = [
    "https://app.llmobserve.com",
    "https://llmobserve.com",
    "https://www.llmobserve.com",
    "https://skyline-ui.vercel.app",
    "https://llmobserve.vercel.app",
]
for origin in production_origins:
    if origin not in allow_origins:
        allow_origins.append(origin)

# Also add localhost for local development
localhost_origins = ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"]
for origin in localhost_origins:
    if origin not in allow_origins:
        allow_origins.append(origin)

logger.info(f"CORS allowed origins: {allow_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,  # Explicit origins (not "*" since we use credentials)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,  # Cache CORS preflight for 24 hours (reduces OPTIONS requests)
)

# =============================================================================
# CDN CACHING HEADERS
# Add Cache-Control headers to enable Cloudflare edge caching
# This allows Cloudflare to cache API responses and serve them instantly
# =============================================================================
from starlette.middleware.base import BaseHTTPMiddleware

class CacheControlMiddleware(BaseHTTPMiddleware):
    """Add cache control headers for CDN caching."""
    
    # Endpoints that can be cached (read-only, non-personalized)
    CACHEABLE_PATTERNS = [
        "/stats/dashboard-all",
        "/stats/by-provider",
        "/stats/by-model",
        "/stats/by-section",
        "/stats/daily",
        "/stats/timeseries",
        "/stats/by-customer",
        "/runs/latest",
    ]
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Only cache GET requests
        if request.method != "GET":
            return response
        
        # Check if this endpoint is cacheable
        path = request.url.path
        is_cacheable = any(pattern in path for pattern in self.CACHEABLE_PATTERNS)
        
        # Only cache successful responses
        if is_cacheable and 200 <= response.status_code < 300:
            # Cache for 5 minutes at CDN edge, allow stale for 10 minutes while revalidating
            # This means:
            # - First 5 min: Serve from cache (instant)
            # - Next 10 min: Serve stale cache while fetching fresh in background (still instant)
            # - After 15 min: Next request fetches fresh (may be slow if Railway is cold)
            # s-maxage is for CDN (Cloudflare), max-age is for browser
            response.headers["Cache-Control"] = "public, s-maxage=300, max-age=60, stale-while-revalidate=600"
            # Vary by Authorization to ensure different users get different cached responses
            response.headers["Vary"] = "Authorization"
        else:
            # Don't cache errors or non-cacheable endpoints
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        
        return response

app.add_middleware(CacheControlMiddleware)

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
db_keepalive_task = None

async def db_keepalive_loop():
    """Periodically ping the database to keep connections warm."""
    from db import engine
    from sqlalchemy import text
    import time
    
    while True:
        try:
            await asyncio.sleep(60)  # Ping every 60 seconds
            start = time.time()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            elapsed = (time.time() - start) * 1000
            logger.debug(f"[DB Keepalive] Ping completed in {elapsed:.0f}ms")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning(f"[DB Keepalive] Ping failed: {e}")

# Initialize database on startup
@app.on_event("startup")
async def on_startup():
    """Initialize database tables and start background services."""
    import time
    from db import engine
    from sqlalchemy import text
    
    startup_start = time.time()
    
    try:
        init_db()
        run_migrations()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        # Don't crash the app - it might connect later
        # Healthcheck will still work
    
    # Warm the database connection pool
    try:
        db_start = time.time()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_elapsed = (time.time() - db_start) * 1000
        logger.info(f"Database connection warmed in {db_elapsed:.0f}ms")
    except Exception as e:
        logger.warning(f"Database warm-up failed: {e}")
    
    # Start cap monitor in background
    try:
        global cap_monitor_task
        cap_monitor_task = asyncio.create_task(run_cap_monitor(check_interval_seconds=300))
        logger.info("Started cap monitor background service")
    except Exception as e:
        logger.error(f"Failed to start cap monitor: {e}", exc_info=True)
    
    # Start database keepalive in background
    try:
        global db_keepalive_task
        db_keepalive_task = asyncio.create_task(db_keepalive_loop())
        logger.info("Started database keepalive background service")
    except Exception as e:
        logger.error(f"Failed to start db keepalive: {e}", exc_info=True)
    
    total_startup = (time.time() - startup_start) * 1000
    logger.info(f"Startup complete in {total_startup:.0f}ms")

@app.on_event("shutdown")
async def on_shutdown():
    """Cleanup background services."""
    global cap_monitor_task, db_keepalive_task
    
    if cap_monitor_task:
        cap_monitor_task.cancel()
        try:
            await cap_monitor_task
        except asyncio.CancelledError:
            pass
        logger.info("Stopped cap monitor background service")
    
    if db_keepalive_task:
        db_keepalive_task.cancel()
        try:
            await db_keepalive_task
        except asyncio.CancelledError:
            pass
        logger.info("Stopped database keepalive background service")


# Debug endpoint to decode JWT
@app.get("/debug/jwt-decode", tags=["debug"])
async def debug_jwt_decode(authorization: Optional[str] = Header(None, alias="Authorization")):
    """Decode JWT token to see what clerk_user_id it contains."""
    import base64
    import json
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "No Bearer token provided"}
    
    token = authorization[7:]
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return {"error": "Invalid JWT format"}
        
        payload = parts[1]
        padding = len(payload) % 4
        if padding:
            payload += '=' * (4 - padding)
        
        decoded = base64.urlsafe_b64decode(payload)
        token_data = json.loads(decoded)
        
        clerk_user_id = token_data.get("sub") or token_data.get("user_id")
        
        return {
            "clerk_user_id_extracted": clerk_user_id,
            "email": token_data.get("email"),
            "sub": token_data.get("sub"),
            "user_id": token_data.get("user_id"),
            "name": token_data.get("name"),
            "all_claims": list(token_data.keys())
        }
    except Exception as e:
        return {"error": str(e)}

# Health check - supports both GET and HEAD for UptimeRobot monitoring
@app.api_route("/health", methods=["GET", "HEAD"], tags=["health"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "llmobserve-collector", "version": "0.3.6-uptimerobot"}

@app.get("/debug/auth-test", tags=["debug"])
async def debug_auth_test(request: Request):
    """Debug endpoint to test auth detection."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "No Authorization header"}
    
    parts = auth_header.split()
    if len(parts) != 2:
        return {"error": f"Invalid header format, parts={len(parts)}"}
    
    token = parts[1]
    return {
        "token_length": len(token),
        "token_prefix": token[:20] if len(token) >= 20 else token,
        "starts_with_llmo_sk": token.startswith("llmo_sk_"),
        "repr_first_20": repr(token[:20]),
        "version": "debug-20250108",
    }


# Warm endpoint - wakes up container AND database connection
@app.api_route("/warm", methods=["GET", "HEAD"], tags=["health"])
def warm_check():
    """
    Warm endpoint that touches the database.
    Use this to wake up both the Railway container AND the PostgreSQL connection pool.
    
    This endpoint is designed to be hit by UptimeRobot or similar services every 5 minutes
    to prevent Railway cold starts (which can take 30+ seconds).
    """
    from db import engine
    from sqlalchemy import text
    import time
    
    start = time.time()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_time = (time.time() - start) * 1000
        return {
            "status": "ok", 
            "db_warm": True, 
            "db_time_ms": round(db_time, 1),
            "message": "Container and database are warm"
        }
    except Exception as e:
        return {
            "status": "degraded", 
            "db_warm": False, 
            "error": str(e),
            "message": "Container is warm but database connection failed"
        }


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

