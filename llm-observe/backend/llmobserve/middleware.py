"""FastAPI middleware for tenant and workflow context."""

import uuid
from typing import Callable, Optional

from fastapi import Request
from opentelemetry import baggage

from llmobserve.config import settings


async def tenant_middleware(request: Request, call_next: Callable):
    """
    Middleware to extract tenant_id and workflow_id from headers and inject into context.

    Extracts:
    - tenant_id from x-tenant-id header (defaults to "default")
    - workflow_id from x-workflow-id header (or generates from path)
    """
    # Extract tenant_id
    tenant_id = request.headers.get(settings.tenant_header, "default")
    
    # Extract or generate workflow_id
    workflow_id = request.headers.get("x-workflow-id")
    if not workflow_id:
        # Generate from path: /api/workflows/my-workflow -> my-workflow
        path_parts = request.url.path.strip("/").split("/")
        if len(path_parts) >= 3 and path_parts[0] == "api" and path_parts[1] == "workflows":
            workflow_id = path_parts[2]
        else:
            # Generate unique ID for this request
            workflow_id = f"workflow-{uuid.uuid4().hex[:8]}"
    
    # Inject into OpenTelemetry baggage
    ctx = baggage.set_baggage("tenant_id", tenant_id)
    ctx = baggage.set_baggage("workflow_id", workflow_id)
    
    # Also store in request state for easy access
    request.state.tenant_id = tenant_id
    request.state.workflow_id = workflow_id
    
    # Continue with request
    response = await call_next(request)
    
    return response


def get_tenant_id() -> str:
    """Get tenant_id from current context."""
    return baggage.get_baggage("tenant_id") or "default"


def get_workflow_id() -> Optional[str]:
    """Get workflow_id from current context."""
    return baggage.get_baggage("workflow_id")

