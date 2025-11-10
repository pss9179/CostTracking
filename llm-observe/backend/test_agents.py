"""
Test script with 2 LangChain agents that use tools and reasoning.
Demonstrates proper LangChain integration with LLMObserveHandler callbacks.
"""

import asyncio
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from opentelemetry import baggage
import opentelemetry.context

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, rely on system env vars

# LangChain imports
from langchain.agents import AgentExecutor, initialize_agent, AgentType
from langchain.tools import Tool
from langchain.chat_models import ChatOpenAI

# LLMObserve imports
from llmobserve.exporter import get_exporter
from llmobserve.langchain_handler import AgentObserveHandler
from llmobserve.tracer import get_tracer, get_current_trace_id, get_current_span_id


# ============================================================================
# Mock Services (simulating real APIs)
# ============================================================================

class MockPineconeIndex:
    """Mock Pinecone index for vector search."""
    
    def query(self, vector: List[float], top_k: int = 5, **kwargs):
        """Mock query - simulates vector search."""
        time.sleep(0.1)
        return {
            "matches": [
                {"id": f"doc_{i}", "score": 0.9 - i*0.1, "metadata": {"text": f"Document {i}"}}
                for i in range(top_k)
            ]
        }
    
    def upsert(self, vectors: List[Dict], **kwargs):
        """Mock upsert - simulates storing vectors."""
        time.sleep(0.1)
        return {"upserted_count": len(vectors)}


class MockVapiClient:
    """Mock Vapi client for voice calls."""
    
    def create_call(self, phone_number: str, assistant_id: str, **kwargs):
        """Mock create call."""
        time.sleep(0.2)
        return {"call_id": f"call_{int(time.time())}", "status": "queued"}
    
    def get_call_status(self, call_id: str):
        """Mock get call status."""
        time.sleep(0.1)
        return {"status": "completed", "duration": 45}


class MockGoogleCalendarAPI:
    """Mock Google Calendar API."""
    
    def list_events(self, calendar_id: str = "primary", **kwargs):
        """Mock list events."""
        time.sleep(0.1)
        return {
            "items": [
                {
                    "id": f"event_{i}",
                    "summary": f"Meeting {i}",
                    "start": {"dateTime": "2024-01-01T10:00:00Z"}
                }
                for i in range(5)
            ]
        }
    
    def create_event(self, calendar_id: str = "primary", event: Dict = None):
        """Mock create event."""
        time.sleep(0.1)
        return {"id": "new_event_123", "summary": event.get("summary", "New Event")}


class MockGmailAPI:
    """Mock Gmail API."""
    
    def list_messages(self, query: str = "", **kwargs):
        """Mock list messages."""
        time.sleep(0.1)
        return {
            "messages": [
                {"id": f"msg_{i}", "threadId": f"thread_{i}", "snippet": f"Email {i} preview"}
                for i in range(10)
            ]
        }
    
    def get_message(self, message_id: str):
        """Mock get message."""
        time.sleep(0.05)
        return {
            "id": message_id,
            "snippet": "Mock email snippet",
            "payload": {"headers": [{"name": "Subject", "value": "Test Email"}]}
        }


# ============================================================================
# LangChain Tools
# ============================================================================

# Global instances for tools to use
_pinecone_index = MockPineconeIndex()
_vapi_client = MockVapiClient()
_gcal_api = MockGoogleCalendarAPI()
_gmail_api = MockGmailAPI()
_exporter = get_exporter()


def create_pinecone_tools():
    """Create Pinecone tools for LangChain agent."""
    
    def query_pinecone(query: str) -> str:
        """Query Pinecone vector database for customer context.
        
        Args:
            query: Search query text
            
        Returns:
            JSON string with matching documents
        """
        start_time = time.time()
        # Convert query to vector (simplified - in real app, use embedding model)
        vector = [0.1] * 1536
        results = _pinecone_index.query(vector=vector, top_k=5)
        duration_ms = (time.time() - start_time) * 1000
        
        # Record cost with trace/span IDs from OpenTelemetry context
        tenant_id = baggage.get_baggage("tenant_id") or "default"
        workflow_id = baggage.get_baggage("workflow_id")
        trace_id = get_current_trace_id()
        span_id = get_current_span_id()
        _exporter.record_cost(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            provider="pinecone",
            operation="query",
            cost_usd=0.0001,
            duration_ms=duration_ms,
            trace_id=trace_id,
            span_id=span_id,
        )
        
        return str(results)
    
    def upsert_pinecone(vectors_json: str) -> str:
        """Store vectors in Pinecone.
        
        Args:
            vectors_json: JSON string with vectors to store
            
        Returns:
            Confirmation message
        """
        start_time = time.time()
        # Parse and upsert (simplified)
        vectors = [{"id": "conv_1", "values": [0.2] * 1536}]
        results = _pinecone_index.upsert(vectors=vectors)
        duration_ms = (time.time() - start_time) * 1000
        
        # Record cost with trace/span IDs from OpenTelemetry context
        tenant_id = baggage.get_baggage("tenant_id") or "default"
        workflow_id = baggage.get_baggage("workflow_id")
        trace_id = get_current_trace_id()
        span_id = get_current_span_id()
        _exporter.record_cost(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            provider="pinecone",
            operation="upsert",
            cost_usd=0.0002,
            duration_ms=duration_ms,
            trace_id=trace_id,
            span_id=span_id,
        )
        
        return f"Stored {results['upserted_count']} vectors"
    
    return [
        Tool(
            name="query_customer_context",
            func=query_pinecone,
            description="Query Pinecone vector database for customer context and support history. Input should be a search query string.",
        ),
        Tool(
            name="store_conversation",
            func=upsert_pinecone,
            description="Store conversation embeddings in Pinecone for future retrieval. Input should be JSON string with vectors.",
        ),
    ]


def create_vapi_tools():
    """Create Vapi tools for LangChain agent."""
    
    def create_voice_call(phone_number: str) -> str:
        """Create a voice call using Vapi.
        
        Args:
            phone_number: Phone number to call
            
        Returns:
            Call ID and status
        """
        start_time = time.time()
        result = _vapi_client.create_call(
            phone_number=phone_number,
            assistant_id="support_agent_1"
        )
        duration_ms = (time.time() - start_time) * 1000
        
        # Record cost with trace/span IDs from OpenTelemetry context
        tenant_id = baggage.get_baggage("tenant_id") or "default"
        workflow_id = baggage.get_baggage("workflow_id")
        trace_id = get_current_trace_id()
        span_id = get_current_span_id()
        _exporter.record_cost(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            provider="vapi",
            operation="create_call",
            cost_usd=0.05,
            duration_ms=duration_ms,
            trace_id=trace_id,
            span_id=span_id,
        )
        
        return f"Call created: {result['call_id']}, status: {result['status']}"
    
    def check_call_status(call_id: str) -> str:
        """Check status of a voice call.
        
        Args:
            call_id: Call ID to check
            
        Returns:
            Call status
        """
        start_time = time.time()
        result = _vapi_client.get_call_status(call_id)
        duration_ms = (time.time() - start_time) * 1000
        
        # Record cost with trace/span IDs from OpenTelemetry context
        tenant_id = baggage.get_baggage("tenant_id") or "default"
        workflow_id = baggage.get_baggage("workflow_id")
        trace_id = get_current_trace_id()
        span_id = get_current_span_id()
        _exporter.record_cost(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            provider="vapi",
            operation="get_status",
            cost_usd=0.001,
            duration_ms=duration_ms,
            trace_id=trace_id,
            span_id=span_id,
        )
        
        return f"Call {call_id}: {result['status']}, duration: {result['duration']}s"
    
    return [
        Tool(
            name="create_voice_call",
            func=create_voice_call,
            description="Create a voice call to a customer using Vapi. Input should be a phone number.",
        ),
        Tool(
            name="check_call_status",
            func=check_call_status,
            description="Check the status of a voice call. Input should be a call ID.",
        ),
    ]


def create_google_calendar_tools():
    """Create Google Calendar tools for LangChain agent."""
    
    def list_calendar_events(query: str = "") -> str:
        """List calendar events.
        
        Args:
            query: Optional query string
            
        Returns:
            JSON string with calendar events
        """
        start_time = time.time()
        results = _gcal_api.list_events()
        duration_ms = (time.time() - start_time) * 1000
        
        # Record cost with trace/span IDs from OpenTelemetry context
        tenant_id = baggage.get_baggage("tenant_id") or "default"
        workflow_id = baggage.get_baggage("workflow_id")
        trace_id = get_current_trace_id()
        span_id = get_current_span_id()
        _exporter.record_cost(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            provider="google",
            operation="calendar_list_events",
            cost_usd=0.0,
            duration_ms=duration_ms,
            trace_id=trace_id,
            span_id=span_id,
        )
        
        return str(results)
    
    def create_calendar_event(event_json: str) -> str:
        """Create a calendar event.
        
        Args:
            event_json: JSON string with event details
            
        Returns:
            Created event ID
        """
        start_time = time.time()
        event = {"summary": "Follow-up from email", "start": {"dateTime": "2024-01-02T14:00:00Z"}}
        result = _gcal_api.create_event(event=event)
        duration_ms = (time.time() - start_time) * 1000
        
        # Record cost with trace/span IDs from OpenTelemetry context
        tenant_id = baggage.get_baggage("tenant_id") or "default"
        workflow_id = baggage.get_baggage("workflow_id")
        trace_id = get_current_trace_id()
        span_id = get_current_span_id()
        _exporter.record_cost(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            provider="google",
            operation="calendar_create_event",
            cost_usd=0.0,
            duration_ms=duration_ms,
            trace_id=trace_id,
            span_id=span_id,
        )
        
        return f"Event created: {result['id']}"
    
    return [
        Tool(
            name="list_calendar_events",
            func=list_calendar_events,
            description="List calendar events. Input can be empty or a query string.",
        ),
        Tool(
            name="create_calendar_event",
            func=create_calendar_event,
            description="Create a calendar event. Input should be JSON string with event details.",
        ),
    ]


def create_gmail_tools():
    """Create Gmail tools for LangChain agent."""
    
    def list_emails(query: str) -> str:
        """List emails from Gmail.
        
        Args:
            query: Gmail search query (e.g., 'is:unread')
            
        Returns:
            JSON string with email messages
        """
        start_time = time.time()
        results = _gmail_api.list_messages(query=query)
        duration_ms = (time.time() - start_time) * 1000
        
        # Record cost with trace/span IDs from OpenTelemetry context
        tenant_id = baggage.get_baggage("tenant_id") or "default"
        workflow_id = baggage.get_baggage("workflow_id")
        trace_id = get_current_trace_id()
        span_id = get_current_span_id()
        _exporter.record_cost(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            provider="google",
            operation="gmail_list_messages",
            cost_usd=0.0,
            duration_ms=duration_ms,
            trace_id=trace_id,
            span_id=span_id,
        )
        
        return str(results)
    
    def get_email(message_id: str) -> str:
        """Get detailed email content.
        
        Args:
            message_id: Email message ID
            
        Returns:
            Email content
        """
        start_time = time.time()
        result = _gmail_api.get_message(message_id)
        duration_ms = (time.time() - start_time) * 1000
        
        # Record cost with trace/span IDs from OpenTelemetry context
        tenant_id = baggage.get_baggage("tenant_id") or "default"
        workflow_id = baggage.get_baggage("workflow_id")
        trace_id = get_current_trace_id()
        span_id = get_current_span_id()
        _exporter.record_cost(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            provider="google",
            operation="gmail_get_message",
            cost_usd=0.0,
            duration_ms=duration_ms,
            trace_id=trace_id,
            span_id=span_id,
        )
        
        return str(result)
    
    return [
        Tool(
            name="list_emails",
            func=list_emails,
            description="List emails from Gmail. Input should be a Gmail search query like 'is:unread'.",
        ),
        Tool(
            name="get_email",
            func=get_email,
            description="Get detailed email content. Input should be an email message ID.",
        ),
    ]


# ============================================================================
# LangChain Agent Workflows
# ============================================================================

def agent_1_workflow(tenant_id: str, workflow_id: str):
    """Agent 1: Customer Support Agent using LangChain with Pinecone and Vapi tools."""
    
    # Set OpenTelemetry context
    ctx1 = baggage.set_baggage("tenant_id", tenant_id)
    ctx2 = baggage.set_baggage("workflow_id", workflow_id, context=ctx1)
    token = opentelemetry.context.attach(ctx2)
    
    try:
        # Create workflow-level span wrapping entire agent execution
        tracer = get_tracer()
        with tracer.start_as_current_span(
            f"workflow:{workflow_id}",
            attributes={
                "tenant_id": tenant_id,
                "workflow_id": workflow_id,
                "agent_type": "customer_support",
            }
        ) as workflow_span:
            # Create LLM with AgentObserveHandler callback (includes organizational spans)
            llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0,
                callbacks=[AgentObserveHandler(agent_name="CustomerSupportAgent")],
            )
            
            # Create tools
            tools = create_pinecone_tools() + create_vapi_tools()
            
            # Create agent using initialize_agent (ReAct agent)
            agent_executor = initialize_agent(
                tools=tools,
                llm=llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                handle_parsing_errors=True,
            )
            
            # Run agent with a customer support question
            print(f"\n[Agent 1] Starting customer support workflow...")
            result = agent_executor.run(
                "A customer is asking about their recent order. First, search for their order history using query_customer_context, then provide a helpful response. If needed, offer to call them using create_voice_call."
            )
            
            print(f"[Agent 1] Agent response: {str(result)[:100]}...")
            
    finally:
        opentelemetry.context.detach(token)


def agent_2_workflow(tenant_id: str, workflow_id: str):
    """Agent 2: Calendar & Email Assistant using LangChain with Google Calendar and Gmail tools."""
    
    # Set OpenTelemetry context
    ctx1 = baggage.set_baggage("tenant_id", tenant_id)
    ctx2 = baggage.set_baggage("workflow_id", workflow_id, context=ctx1)
    token = opentelemetry.context.attach(ctx2)
    
    try:
        # Create workflow-level span wrapping entire agent execution
        tracer = get_tracer()
        with tracer.start_as_current_span(
            f"workflow:{workflow_id}",
            attributes={
                "tenant_id": tenant_id,
                "workflow_id": workflow_id,
                "agent_type": "calendar_email_assistant",
            }
        ) as workflow_span:
            # Create LLM with AgentObserveHandler callback (includes organizational spans)
            llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0,
                callbacks=[AgentObserveHandler(agent_name="CalendarEmailAssistant")],
            )
            
            # Create tools
            tools = create_google_calendar_tools() + create_gmail_tools()
            
            # Create agent using initialize_agent (ReAct agent)
            agent_executor = initialize_agent(
                tools=tools,
                llm=llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                handle_parsing_errors=True,
            )
            
            # Run agent with a calendar/email task
            print(f"\n[Agent 2] Starting calendar & email workflow...")
            result = agent_executor.run(
                "Summarize my calendar events using list_calendar_events and unread emails using list_emails with query 'is:unread'. If there's an email about scheduling a meeting, create a calendar event for it using create_calendar_event."
            )
            
            print(f"[Agent 2] Agent response: {str(result)[:100]}...")
            
    finally:
        opentelemetry.context.detach(token)


async def main():
    """Run both LangChain agents with different tenants and workflows."""
    
    # Initialize exporter
    exporter = get_exporter()
    exporter.start()
    
    print("=" * 80)
    print("Starting LangChain Multi-Agent Test Workflow")
    print("=" * 80)
    
    # Run Agent 1: Customer Support
    tenant_1 = "acme-corp"
    workflow_1 = "customer-support-001"
    print(f"\n[Main] Starting Agent 1 workflow: {workflow_1} for tenant: {tenant_1}")
    agent_1_workflow(tenant_1, workflow_1)
    
    # Small delay between agents
    await asyncio.sleep(0.5)
    
    # Run Agent 2: Calendar & Email Assistant
    tenant_2 = "tech-startup"
    workflow_2 = "calendar-email-assistant-001"
    print(f"\n[Main] Starting Agent 2 workflow: {workflow_2} for tenant: {tenant_2}")
    agent_2_workflow(tenant_2, workflow_2)
    
    # Flush exporter
    print("\n[Main] Flushing exporter...")
    exporter._flush_queue()
    await asyncio.sleep(1.0)
    
    print("\n" + "=" * 80)
    print("LangChain Multi-Agent Test Workflow Complete!")
    print("=" * 80)
    print(f"\nCheck the dashboard at http://localhost:3000 to see the traces!")
    
    exporter.stop()


if __name__ == "__main__":
    # Initialize database
    from llmobserve.db import init_db
    init_db()
    
    # Initialize tracer
    from llmobserve.tracer import init_tracer
    init_tracer()
    
    asyncio.run(main())
