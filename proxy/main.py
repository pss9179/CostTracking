"""
LLMObserve Universal Proxy Server

Lightweight FastAPI proxy that captures HTTP traffic,
parses provider responses, calculates costs, and emits events.
"""
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import time
import uuid
import logging
from typing import Optional

from providers import detect_provider, extract_endpoint, parse_usage
from pricing import calculate_cost
from graphql_parser import (
    is_graphql_request,
    parse_graphql_request,
    extract_graphql_endpoint,
    parse_graphql_response,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llmobserve.proxy")

app = FastAPI(
    title="LLMObserve Proxy",
    description="Universal proxy for AI/API cost observability",
    version="0.1.0"
)

# Global config
COLLECTOR_URL = None


def set_collector_url(url: str):
    """Set the collector URL for event emission."""
    global COLLECTOR_URL
    COLLECTOR_URL = url


async def emit_event(event: dict):
    """Emit event to collector."""
    if not COLLECTOR_URL:
        logger.warning("[proxy] Collector URL not set, skipping event emission")
        return
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{COLLECTOR_URL}/events/",
                json=[event],
                timeout=5.0
            )
    except Exception as e:
        logger.error(f"[proxy] Failed to emit event: {e}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "llmobserve-proxy"}


@app.post("/proxy")
@app.get("/proxy")
@app.put("/proxy")
@app.delete("/proxy")
@app.patch("/proxy")
async def proxy_request(request: Request):
    """
    Universal proxy endpoint.
    
    Receives requests from SDK with context headers,
    forwards to actual API, parses response, emits event.
    """
    # Extract context from headers
    run_id = request.headers.get("X-LLMObserve-Run-ID", "")
    span_id = request.headers.get("X-LLMObserve-Span-ID", str(uuid.uuid4()))
    parent_span_id = request.headers.get("X-LLMObserve-Parent-Span-ID", "")
    section = request.headers.get("X-LLMObserve-Section", "default")
    section_path = request.headers.get("X-LLMObserve-Section-Path", "default")
    customer_id = request.headers.get("X-LLMObserve-Customer-ID", "")
    target_url = request.headers.get("X-LLMObserve-Target-URL")
    
    if not target_url:
        return JSONResponse(
            status_code=400,
            content={"error": "Missing X-LLMObserve-Target-URL header"}
        )
    
    # Read request body
    request_body = await request.body()
    request_json = None
    try:
        request_json = await request.json() if request_body else None
    except:
        pass
    
    # Detect GraphQL requests
    content_type = request.headers.get("Content-Type", "")
    is_graphql = is_graphql_request(content_type, request_body, request_json)
    graphql_info = {}
    
    if is_graphql:
        graphql_info = parse_graphql_request(request_body, request_json)
        logger.debug(f"[proxy] GraphQL request detected: {graphql_info.get('operation_type')} {graphql_info.get('operation_name')}")
    
    # Detect provider
    provider = detect_provider(target_url)
    
    # Extract endpoint (use GraphQL endpoint if GraphQL request)
    if is_graphql and graphql_info.get("query"):
        endpoint = extract_graphql_endpoint(graphql_info["query"], target_url)
    else:
        endpoint = extract_endpoint(target_url, request.method)
    
    # Forward request to actual API
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Copy headers (remove LLMObserve headers)
            forward_headers = {
                k: v for k, v in request.headers.items()
                if not k.startswith("X-LLMObserve") and k.lower() != "host"
            }
            
            # Forward request
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=forward_headers,
                content=request_body
            )
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Parse response
        response_json = None
        try:
            response_json = response.json()
        except:
            pass
        
        # Parse GraphQL response if applicable
        graphql_response_info = {}
        if is_graphql and response_json:
            graphql_response_info = parse_graphql_response(response_json)
        
        # Extract usage
        usage = parse_usage(provider, response_json or {}, request_json)
        
        # Calculate cost
        cost_usd = calculate_cost(provider, usage)
        
        # Determine span type
        if is_graphql:
            span_type = "graphql_call"
        elif provider in ["openai", "anthropic", "google", "cohere", "mistral", "groq"]:
            span_type = "llm_call"
        else:
            span_type = "api_call"
        
        # Build event metadata
        event_metadata = {
            "http_status": response.status_code,
            "provider": provider,
        }
        
        # Add GraphQL metadata if applicable
        if is_graphql:
            event_metadata.update({
                "graphql_operation_type": graphql_info.get("operation_type"),
                "graphql_operation_name": graphql_info.get("operation_name"),
                "graphql_field_count": graphql_info.get("field_count", 0),
                "graphql_complexity_score": graphql_info.get("complexity_score", 0),
                "graphql_response_data_size": graphql_response_info.get("data_size", 0),
                "graphql_response_error_count": graphql_response_info.get("error_count", 0),
            })
        
        # Emit event to collector
        event = {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id if parent_span_id else None,
            "section": section,
            "section_path": section_path,
            "span_type": span_type,
            "provider": provider,
            "endpoint": endpoint,
            "model": usage.get("model"),
            "cost_usd": cost_usd,
            "latency_ms": latency_ms,
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cached_tokens": usage.get("cached_tokens", 0),
            "status": "ok" if response.status_code < 400 else "error",
            "customer_id": customer_id if customer_id else None,
            "event_metadata": event_metadata,
        }
        
        # Emit event (non-blocking)
        await emit_event(event)
        
        # Return response to SDK
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        
        logger.error(f"[proxy] Error forwarding request: {e}")
        
        # Determine span type for error
        error_span_type = "graphql_call" if is_graphql else "api_call"
        
        # Build error event metadata
        error_metadata = {"error": str(e)}
        if is_graphql:
            error_metadata.update({
                "graphql_operation_type": graphql_info.get("operation_type"),
                "graphql_operation_name": graphql_info.get("operation_name"),
            })
        
        # Emit error event
        error_event = {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id if parent_span_id else None,
            "section": section,
            "section_path": section_path,
            "span_type": error_span_type,
            "provider": provider,
            "endpoint": endpoint,
            "model": None,
            "cost_usd": 0.0,
            "latency_ms": latency_ms,
            "input_tokens": 0,
            "output_tokens": 0,
            "status": "error",
            "customer_id": customer_id if customer_id else None,
            "event_metadata": error_metadata,
        }
        
        await emit_event(error_event)
        
        # Return error
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.on_event("startup")
async def startup():
    """Startup event."""
    import os
    collector_url = os.getenv("LLMOBSERVE_COLLECTOR_URL", "http://localhost:8000")
    set_collector_url(collector_url)
    logger.info(f"[proxy] Started with collector URL: {collector_url}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)

