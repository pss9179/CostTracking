"""
Framework middleware for context cleanup and management.

Ensures context is properly reset between requests to avoid cross-contamination.
"""
from typing import Callable, Optional
from llmobserve import context
import uuid


class ObservabilityMiddleware:
    """
    FastAPI/Starlette middleware to manage observability context per request.
    
    Usage:
        from fastapi import FastAPI
        from llmobserve.middleware import ObservabilityMiddleware
        
        app = FastAPI()
        app.add_middleware(ObservabilityMiddleware)
    
    Features:
    - Resets context before each request (prevents cross-contamination)
    - Auto-generates run_id per request
    - Extracts customer_id from headers (X-Customer-ID)
    """
    
    def __init__(
        self,
        app,
        auto_run_id: bool = True,
        customer_header: str = "X-Customer-ID"
    ):
        self.app = app
        self.auto_run_id = auto_run_id
        self.customer_header = customer_header
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Reset context before request
        context.set_run_id(str(uuid.uuid4()) if self.auto_run_id else None)
        context.set_customer_id(None)
        
        # Clear section stack
        stack = context._get_section_stack()
        stack.clear()
        
        # Extract customer from headers
        headers = dict(scope.get("headers", []))
        
        customer_id = headers.get(self.customer_header.lower().encode(), b"").decode()
        if customer_id:
            context.set_customer_id(customer_id)
        
        # Process request
        await self.app(scope, receive, send)


def flask_before_request():
    """
    Flask before_request hook to reset context.
    
    Usage:
        from flask import Flask, request
        from llmobserve.middleware import flask_before_request
        
        app = Flask(__name__)
        app.before_request(flask_before_request)
        
        # Optional: Extract from headers in your routes
        @app.route("/api/process")
        def process():
            customer_id = request.headers.get("X-Customer-ID")
            if customer_id:
                from llmobserve import set_customer_id
                set_customer_id(customer_id)
            # ... your code
    """
    # Reset context
    context.set_run_id(str(uuid.uuid4()))
    context.set_customer_id(None)
    
    # Clear section stack
    stack = context._get_section_stack()
    stack.clear()


def django_middleware(get_response):
    """
    Django middleware to reset context.
    
    Usage:
        # In settings.py
        MIDDLEWARE = [
            'llmobserve.middleware.django_middleware',
            # ... other middleware
        ]
    """
    def middleware(request):
        # Reset context
        context.set_run_id(str(uuid.uuid4()))
        context.set_customer_id(None)
        
        # Clear section stack
        stack = context._get_section_stack()
        stack.clear()
        
        # Extract from headers
        customer_id = request.headers.get("X-Customer-ID")
        if customer_id:
            context.set_customer_id(customer_id)
        
        response = get_response(request)
        return response
    
    return middleware

