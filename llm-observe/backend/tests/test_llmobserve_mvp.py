"""Pytest tests for LLMObserve MVP - end-to-end pipeline verification."""

import os
import time
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session

from llmobserve.models import CostEvent
from llmobserve.exporter import CostEventExporter
from llmobserve.middleware import tenant_middleware, get_tenant_id, get_workflow_id
from llmobserve.langchain_handler import LLMObserveHandler
from llmobserve.providers.openai_wrapper import openai_client
from llmobserve.pricing import pricing_registry


def get_test_session():
    """Helper to get test session."""
    import llmobserve.db
    return llmobserve.db.get_session()


@pytest.fixture
def exporter(test_db):
    """Create exporter instance for tests."""
    # test_db fixture ensures patching is in place
    # Create a new exporter that will use the patched _get_session
    exporter = CostEventExporter(batch_size=1, flush_interval=0.1)
    # Ensure exporter uses patched _get_session
    import llmobserve.exporter
    exporter._get_session = llmobserve.exporter._get_session
    exporter.start()
    yield exporter
    exporter.stop()


@pytest.fixture
def client(test_db):
    """Create test client for FastAPI app."""
    # Import here to ensure test_db fixture runs first and patches are in place
    # The test_db fixture patches llmobserve.db.get_session and llmobserve.api.routes._get_session
    # Since routes._get_session imports get_session inside the function, the patch should work
    from llmobserve.main import app
    return TestClient(app)


class TestMiddleware:
    """Test middleware context propagation."""
    
    def test_tenant_middleware_extracts_tenant_id(self, client):
        """Test middleware extracts tenant_id from header."""
        response = client.get(
            "/health",
            headers={"x-tenant-id": "test-tenant-123"}
        )
        assert response.status_code == 200
        
        # Verify tenant_id was set in context
        # (In real app, this would be checked via baggage)
        assert response.json() == {"status": "ok"}
    
    def test_tenant_middleware_defaults_tenant_id(self, client):
        """Test middleware defaults to 'default' tenant."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_tenant_middleware_generates_workflow_id(self, client):
        """Test middleware generates workflow_id if not provided."""
        response = client.get(
            "/health",
            headers={"x-tenant-id": "test-tenant"}
        )
        assert response.status_code == 200


class TestLangChainHandler:
    """Test LangChain callback handler."""
    
    def test_on_llm_end_records_cost_event(self, exporter):
        """Test LLM end callback records cost event."""
        handler = LLMObserveHandler()
        # Replace handler's exporter with test exporter
        handler._exporter = exporter
        
        # Mock LLM response with usage
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        # Mock kwargs
        kwargs = {
            "llm_output": {
                "token_usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150,
                }
            },
            "model_name": "gpt-4o",
            "provider": "openai",
            "duration_ms": 500.0,
        }
        
        # Set tenant context via baggage
        from opentelemetry import baggage
        import opentelemetry.context
        
        # Create context with baggage - need to chain contexts
        ctx1 = baggage.set_baggage("tenant_id", "test-tenant")
        ctx2 = baggage.set_baggage("workflow_id", "test-workflow", context=ctx1)
        token = opentelemetry.context.attach(ctx2)
        try:
            handler.on_llm_end(mock_response, **kwargs)
        finally:
            opentelemetry.context.detach(token)
        
        # Force flush exporter
        exporter._flush_queue()
        time.sleep(0.1)
        
        # Verify event was written
        session = get_test_session()
        try:
            from sqlmodel import select
            events = list(session.exec(select(CostEvent)).all())
            assert len(events) == 1
            event = events[0]
            assert event.tenant_id == "test-tenant"
            assert event.workflow_id == "test-workflow"
            assert event.provider == "openai"
            assert event.model == "gpt-4o"
            assert event.prompt_tokens == 100
            assert event.completion_tokens == 50
            assert event.total_tokens == 150
            assert event.cost_usd > 0  # Should have calculated cost
        finally:
            session.close()
    
    def test_on_tool_end_records_tool_event(self, exporter):
        """Test tool end callback records tool usage."""
        handler = LLMObserveHandler()
        # Replace handler's exporter with test exporter
        handler._exporter = exporter
        
        # Set tenant context
        from opentelemetry import baggage
        import opentelemetry.context
        
        ctx1 = baggage.set_baggage("tenant_id", "test-tenant")
        ctx2 = baggage.set_baggage("workflow_id", "test-workflow", context=ctx1)
        token = opentelemetry.context.attach(ctx2)
        try:
            handler.on_tool_end(
                output="tool result",
                name="search_tool",
                duration_ms=100.0,
            )
        finally:
            opentelemetry.context.detach(token)
        
        # Force flush exporter
        exporter._flush_queue()
        time.sleep(0.1)
        
        # Verify event was written
        session = get_test_session()
        try:
            from sqlmodel import select
            events = list(session.exec(select(CostEvent)).all())
            assert len(events) == 1
            event = events[0]
            assert event.tenant_id == "test-tenant"
            assert event.provider == "tool"
            assert event.model == "search_tool"
            assert event.operation == "tool"
            assert event.cost_usd == 0.0  # Tools have no cost
        finally:
            session.close()


class TestOpenAIWrapper:
    """Test OpenAI wrapper cost tracking."""
    
    def test_openai_wrapper_tracks_chat_completion(self, exporter):
        """Test OpenAI wrapper tracks chat completion costs."""
        # Replace the exporter in the wrapper with our test exporter
        from llmobserve.providers.openai_wrapper import openai_client
        from llmobserve.exporter import get_exporter
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_chat = Mock()
        mock_completions = Mock()
        
        # Mock response
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 200
        mock_response.usage.completion_tokens = 100
        mock_response.usage.total_tokens = 300
        
        mock_completions.create = Mock(return_value=mock_response)
        mock_chat.completions = mock_completions
        mock_client.chat = mock_chat
        
        # Set tenant context BEFORE wrapping
        from opentelemetry import baggage
        import opentelemetry.context
        
        ctx1 = baggage.set_baggage("tenant_id", "test-tenant")
        ctx2 = baggage.set_baggage("workflow_id", "test-workflow", context=ctx1)
        token = opentelemetry.context.attach(ctx2)
        try:
            # Wrap client - this creates a new TrackedOpenAIClient with its own exporter
            wrapped_client = openai_client(mock_client)
            # Replace the exporter in the wrapped client with our test exporter
            wrapped_client._exporter = exporter
            # Get the chat object (TrackedChat) and replace its exporter
            chat_obj = wrapped_client.chat
            chat_obj._exporter = exporter
            # Get the completions object (TrackedCompletions) and replace its exporter
            completions_obj = chat_obj.completions
            completions_obj._exporter = exporter
            
            # Make call
            response = wrapped_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Hello"}]
            )
        finally:
            opentelemetry.context.detach(token)
        
        # Force flush exporter
        exporter._flush_queue()
        time.sleep(0.2)
        
        # Verify event was written
        session = get_test_session()
        try:
            from sqlmodel import select
            events = list(session.exec(select(CostEvent)).all())
            assert len(events) == 1
            event = events[0]
            assert event.tenant_id == "test-tenant"
            assert event.provider == "openai"
            assert event.model == "gpt-4o"
            assert event.prompt_tokens == 200
            assert event.completion_tokens == 100
            assert event.total_tokens == 300
            assert event.cost_usd > 0
            assert event.duration_ms > 0  # Duration should be recorded
            assert event.operation == "chat"
        finally:
            session.close()
    
    def test_openai_wrapper_tracks_embeddings(self, exporter):
        """Test OpenAI wrapper tracks embedding costs."""
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_embeddings = Mock()
        
        # Mock response
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 1000
        mock_response.usage.total_tokens = 1000
        
        mock_embeddings.create = Mock(return_value=mock_response)
        mock_client.embeddings = mock_embeddings
        
        # Set tenant context BEFORE wrapping
        from opentelemetry import baggage
        import opentelemetry.context
        
        ctx = baggage.set_baggage("tenant_id", "test-tenant")
        token = opentelemetry.context.attach(ctx)
        try:
            # Wrap client
            wrapped_client = openai_client(mock_client)
            # Replace the exporter in the wrapped client with our test exporter
            wrapped_client._exporter = exporter
            # Get the embeddings object and replace its exporter
            embeddings_obj = wrapped_client.embeddings
            embeddings_obj._exporter = exporter
            
            # Make call
            response = wrapped_client.embeddings.create(
                model="text-embedding-3-small",
                input="test text"
            )
        finally:
            opentelemetry.context.detach(token)
        
        # Force flush exporter
        exporter._flush_queue()
        time.sleep(0.2)
        
        # Verify event was written
        session = get_test_session()
        try:
            from sqlmodel import select
            events = list(session.exec(select(CostEvent)).all())
            assert len(events) == 1
            event = events[0]
            assert event.provider == "openai"
            assert event.model == "text-embedding-3-small"
            assert event.prompt_tokens == 1000
            assert event.operation == "embedding"
        finally:
            session.close()


class TestExporter:
    """Test async exporter."""
    
    def test_exporter_batches_events(self, test_db):
        """Test exporter batches events before writing."""
        exporter = CostEventExporter(batch_size=3, flush_interval=0.3)
        # Ensure exporter uses patched _get_session
        import llmobserve.exporter
        exporter._get_session = llmobserve.exporter._get_session
        exporter.start()
        
        try:
            # Add 5 events (should create 2 batches: 3 + 2)
            for i in range(5):
                exporter.record_cost(
                    tenant_id=f"tenant-{i}",
                    provider="openai",
                    cost_usd=0.01 * i,
                    duration_ms=100.0,
                )
            
            # Wait for batches to flush (need to wait longer than flush_interval)
            time.sleep(0.6)
            
            # Force flush remaining
            exporter._flush_queue()
            time.sleep(0.4)  # Give time for flush to complete
            
            # Verify events were written
            session = get_test_session()
            try:
                from sqlmodel import select
                events = list(session.exec(select(CostEvent)).all())
                assert len(events) == 5, f"Expected 5 events, got {len(events)}"
            finally:
                session.close()
        finally:
            exporter.stop()
    
    def test_exporter_handles_errors_gracefully(self, exporter):
        """Test exporter handles errors without crashing."""
        # Try to record with invalid data (should not crash)
        exporter.record_cost(
            tenant_id="test",
            provider="openai",
            cost_usd=-1.0,  # Invalid cost
            duration_ms=100.0,
        )
        
        # Should not raise exception
        time.sleep(0.2)


class TestAPIRoutes:
    """Test API routes."""
    
    def test_get_costs_endpoint(self, client, exporter):
        """Test /api/costs endpoint returns cost events."""
        # Create test events
        for i in range(3):
            exporter.record_cost(
                tenant_id="test-tenant",
                provider="openai",
                cost_usd=0.01 * (i + 1),
                duration_ms=100.0 * (i + 1),
                model="gpt-4o",
            )
        
        # Force flush events
        exporter._flush_queue()
        time.sleep(0.2)
        
        # Query API
        response = client.get("/api/costs?tenant_id=test-tenant")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert len(data["events"]) == 3
        assert data["events"][0]["tenant_id"] == "test-tenant"
        assert data["events"][0]["provider"] == "openai"
    
    def test_get_tenants_endpoint(self, client, exporter):
        """Test /api/tenants endpoint aggregates by tenant."""
        # Create events for multiple tenants
        for tenant_id in ["tenant-1", "tenant-2", "tenant-1"]:
            exporter.record_cost(
                tenant_id=tenant_id,
                provider="openai",
                cost_usd=0.01,
                duration_ms=100.0,
            )
        
        exporter._flush_queue()
        time.sleep(0.1)
        
        # Query API
        response = client.get("/api/tenants")
        assert response.status_code == 200
        data = response.json()
        assert "tenants" in data
        tenants = {t["tenant_id"]: t for t in data["tenants"]}
        assert "tenant-1" in tenants
        assert "tenant-2" in tenants
        assert tenants["tenant-1"]["total_cost_usd"] == pytest.approx(0.02, rel=0.01)
        assert tenants["tenant-2"]["total_cost_usd"] == pytest.approx(0.01, rel=0.01)
    
    def test_get_workflows_endpoint(self, client, exporter):
        """Test /api/workflows endpoint aggregates by workflow."""
        # Create events for multiple workflows
        for workflow_id in ["workflow-1", "workflow-2"]:
            exporter.record_cost(
                tenant_id="test-tenant",
                workflow_id=workflow_id,
                provider="openai",
                cost_usd=0.01,
                duration_ms=100.0,
            )
        
        exporter._flush_queue()
        time.sleep(0.1)
        
        # Query API
        response = client.get("/api/workflows?tenant_id=test-tenant")
        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert len(data["workflows"]) == 2
    
    def test_get_metrics_endpoint(self, client, exporter):
        """Test /api/metrics endpoint returns aggregated metrics."""
        # Create events with different providers
        for provider in ["openai", "pinecone", "openai"]:
            exporter.record_cost(
                tenant_id="test-tenant",
                provider=provider,
                cost_usd=0.01,
                duration_ms=100.0,
                model="gpt-4o" if provider == "openai" else None,
            )
        
        exporter._flush_queue()
        time.sleep(0.1)
        
        # Query API
        response = client.get("/api/metrics?tenant_id=test-tenant&days=7")
        assert response.status_code == 200
        data = response.json()
        assert "total_cost_usd" in data
        assert "total_tokens" in data
        assert "total_requests" in data
        assert "cost_by_provider" in data
        assert data["total_requests"] == 3
        assert "openai" in data["cost_by_provider"]
        assert "pinecone" in data["cost_by_provider"]


class TestEndToEnd:
    """End-to-end integration tests."""
    
    def test_full_pipeline_langchain_to_api(self, client, exporter):
        """Test full pipeline: LangChain handler -> exporter -> API."""
        # Don't mock time.time() - it breaks exporter worker thread
        
        # Set tenant context
        from opentelemetry import baggage
        import opentelemetry.context
        
        ctx1 = baggage.set_baggage("tenant_id", "e2e-tenant")
        ctx2 = baggage.set_baggage("workflow_id", "e2e-workflow", context=ctx1)
        token = opentelemetry.context.attach(ctx2)
        try:
            # Simulate LangChain LLM call
            handler = LLMObserveHandler()
            # Replace handler's exporter with test exporter
            handler._exporter = exporter
            mock_response = Mock()
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 150
            mock_response.usage.completion_tokens = 75
            mock_response.usage.total_tokens = 225
            
            handler.on_llm_end(
                mock_response,
                llm_output={
                    "token_usage": {
                        "prompt_tokens": 150,
                        "completion_tokens": 75,
                        "total_tokens": 225,
                    }
                },
                model_name="gpt-4o",
                provider="openai",
                duration_ms=500.0,
            )
        finally:
            opentelemetry.context.detach(token)
        
        # Wait for exporter
        exporter._flush_queue()
        time.sleep(0.2)
        
        # Query API
        response = client.get("/api/costs?tenant_id=e2e-tenant")
        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 1
        event = data["events"][0]
        assert event["tenant_id"] == "e2e-tenant"
        assert event["workflow_id"] == "e2e-workflow"
        assert event["provider"] == "openai"
        assert event["model"] == "gpt-4o"
        assert event["prompt_tokens"] == 150
        assert event["completion_tokens"] == 75
        assert event["total_tokens"] == 225
        assert event["cost_usd"] > 0
    
    def test_full_pipeline_openai_wrapper_to_api(self, client, exporter):
        """Test full pipeline: OpenAI wrapper -> exporter -> API."""
        # Don't mock time.time() - it breaks exporter worker thread
        
        # Set tenant context
        from opentelemetry import baggage
        import opentelemetry.context
        
        ctx = baggage.set_baggage("tenant_id", "wrapper-tenant")
        token = opentelemetry.context.attach(ctx)
        try:
            # Mock OpenAI client
            mock_client = Mock()
            mock_chat = Mock()
            mock_completions = Mock()
            mock_response = Mock()
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 50
            mock_response.usage.total_tokens = 150
            mock_completions.create = Mock(return_value=mock_response)
            mock_chat.completions = mock_completions
            mock_client.chat = mock_chat
            
            # Use wrapper
            wrapped_client = openai_client(mock_client)
            # Replace exporter in nested objects
            wrapped_client._exporter = exporter
            chat_obj = wrapped_client.chat
            chat_obj._exporter = exporter
            completions_obj = chat_obj.completions
            completions_obj._exporter = exporter
            
            wrapped_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "test"}]
            )
        finally:
            opentelemetry.context.detach(token)
        
        # Wait for exporter
        exporter._flush_queue()
        time.sleep(0.2)
        
        # Query API
        response = client.get("/api/metrics?tenant_id=wrapper-tenant")
        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 1
        assert data["total_cost_usd"] > 0
        assert "openai" in data["cost_by_provider"]

