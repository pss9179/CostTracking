"""Multiple agent workflows for testing: Gmail, Google Calendar, and Vapi."""

import asyncio
import time
from typing import Dict, List

import openai
from llmobserve.config import settings
from llmobserve.tracing.function_tracer import workflow_trace


# Mock Gmail API client
class MockGmailClient:
    """Mock Gmail API client for testing."""
    
    @staticmethod
    async def list_messages(query: str = "", max_results: int = 10) -> List[Dict]:
        """Mock list messages API call - creates a span for visualization."""
        from opentelemetry import trace
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("gmail.list_messages") as span:
            span.set_attribute("gmail.query", query)
            span.set_attribute("gmail.max_results", max_results)
            await asyncio.sleep(0.1)  # Simulate API latency
            return [
                {"id": "msg1", "subject": "Test Email 1", "from": "sender@example.com"},
                {"id": "msg2", "subject": "Test Email 2", "from": "sender2@example.com"},
            ]
    
    @staticmethod
    async def get_message(message_id: str) -> Dict:
        """Mock get message API call - creates a span for visualization."""
        from opentelemetry import trace
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("gmail.get_message") as span:
            span.set_attribute("gmail.message_id", message_id)
            await asyncio.sleep(0.05)
            return {
                "id": message_id,
                "subject": "Test Email",
                "body": "This is a test email body",
                "from": "sender@example.com",
            }
    
    @staticmethod
    async def send_message(to: str, subject: str, body: str) -> Dict:
        """Mock send message API call - creates a span for visualization."""
        from opentelemetry import trace
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("gmail.send_message") as span:
            span.set_attribute("gmail.to", to)
            await asyncio.sleep(0.1)
            return {"id": "sent_msg1", "status": "sent"}


# Mock Google Calendar API client
class MockCalendarClient:
    """Mock Google Calendar API client for testing."""
    
    @staticmethod
    async def list_events(calendar_id: str = "primary", max_results: int = 10) -> List[Dict]:
        """Mock list events API call - creates a span for visualization."""
        from opentelemetry import trace
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("gcal.list_events") as span:
            span.set_attribute("gcal.calendar_id", calendar_id)
            span.set_attribute("gcal.max_results", max_results)
            await asyncio.sleep(0.1)
            return [
                {"id": "event1", "summary": "Meeting", "start": "2024-01-01T10:00:00Z"},
                {"id": "event2", "summary": "Lunch", "start": "2024-01-01T12:00:00Z"},
            ]
    
    @staticmethod
    async def create_event(summary: str, start_time: str, end_time: str) -> Dict:
        """Mock create event API call - creates a span for visualization."""
        from opentelemetry import trace
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("gcal.create_event") as span:
            span.set_attribute("gcal.summary", summary)
            span.set_attribute("gcal.start_time", start_time)
            await asyncio.sleep(0.1)
            return {"id": "new_event1", "summary": summary, "status": "confirmed"}
    
    @staticmethod
    async def update_event(event_id: str, summary: str) -> Dict:
        """Mock update event API call - creates a span for visualization."""
        from opentelemetry import trace
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("gcal.update_event") as span:
            span.set_attribute("gcal.event_id", event_id)
            await asyncio.sleep(0.05)
            return {"id": event_id, "summary": summary, "status": "updated"}


# Mock Vapi API client
class MockVapiClient:
    """Mock Vapi API client for testing."""
    
    @staticmethod
    async def create_call(phone_number: str, assistant_id: str) -> Dict:
        """Mock create call API call - creates a span for visualization."""
        from opentelemetry import trace
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("vapi.create_call") as span:
            span.set_attribute("vapi.phone_number", phone_number)
            span.set_attribute("vapi.assistant_id", assistant_id)
            await asyncio.sleep(0.2)  # Simulate longer call setup
            return {"call_id": "call_123", "status": "initiated", "phone_number": phone_number}
    
    @staticmethod
    async def get_call_status(call_id: str) -> Dict:
        """Mock get call status API call - creates a span for visualization."""
        from opentelemetry import trace
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("vapi.get_call_status") as span:
            span.set_attribute("vapi.call_id", call_id)
            await asyncio.sleep(0.05)
            return {"call_id": call_id, "status": "completed", "duration": 120}
    
    @staticmethod
    async def end_call(call_id: str) -> Dict:
        """Mock end call API call - creates a span for visualization."""
        from opentelemetry import trace
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("vapi.end_call") as span:
            span.set_attribute("vapi.call_id", call_id)
            await asyncio.sleep(0.05)
            return {"call_id": call_id, "status": "ended"}


@workflow_trace
async def gmail_workflow() -> Dict:
    """
    Gmail workflow: List emails → Get email details → Generate summary with GPT.
    """
    gmail = MockGmailClient()
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    # Step 1: List messages
    messages = await gmail.list_messages(query="is:unread", max_results=5)
    
    # Step 2: Get first message details
    if messages:
        message = await gmail.get_message(messages[0]["id"])
        
        # Step 3: Use GPT to summarize the email
        summary_resp = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an email summarization assistant."},
                {"role": "user", "content": f"Summarize this email:\nSubject: {message.get('subject', '')}\nBody: {message.get('body', '')}"}
            ],
            max_tokens=100,
            temperature=0.7,
        )
        summary = summary_resp.choices[0].message.content
        
        return {
            "workflow": "gmail_workflow",
            "messages_found": len(messages),
            "email_summary": summary,
        }
    
    return {"workflow": "gmail_workflow", "messages_found": 0}


@workflow_trace
async def calendar_workflow() -> Dict:
    """
    Google Calendar workflow: List events → Create new event → Update event with GPT suggestion.
    """
    calendar = MockCalendarClient()
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    # Step 1: List upcoming events
    events = await calendar.list_events(calendar_id="primary", max_results=10)
    
    # Step 2: Create a new event
    new_event = await calendar.create_event(
        summary="Team Meeting",
        start_time="2024-01-15T14:00:00Z",
        end_time="2024-01-15T15:00:00Z"
    )
    
    # Step 3: Use GPT to suggest a better event title
    if events:
        suggestion_resp = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a calendar assistant. Suggest better event titles."},
                {"role": "user", "content": f"Suggest a better title for: {new_event['summary']}"}
            ],
            max_tokens=50,
            temperature=0.7,
        )
        suggested_title = suggestion_resp.choices[0].message.content
        
        # Step 4: Update event with suggested title
        updated_event = await calendar.update_event(new_event["id"], suggested_title)
        
        return {
            "workflow": "calendar_workflow",
            "events_found": len(events),
            "new_event_id": new_event["id"],
            "suggested_title": suggested_title,
            "updated_event": updated_event,
        }
    
    return {"workflow": "calendar_workflow", "events_found": 0}


@workflow_trace
async def vapi_workflow() -> Dict:
    """
    Vapi workflow: Create call → Check status → Generate call summary with GPT.
    """
    vapi = MockVapiClient()
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    # Step 1: Create a call
    call = await vapi.create_call(
        phone_number="+1234567890",
        assistant_id="assistant_123"
    )
    
    # Step 2: Check call status
    status = await vapi.get_call_status(call["call_id"])
    
    # Step 3: Use GPT to generate a call summary
    summary_resp = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a call summarization assistant."},
            {"role": "user", "content": f"Generate a summary for a call that lasted {status.get('duration', 0)} seconds."}
        ],
        max_tokens=100,
        temperature=0.7,
    )
    call_summary = summary_resp.choices[0].message.content
    
    # Step 4: End the call
    ended_call = await vapi.end_call(call["call_id"])
    
    return {
        "workflow": "vapi_workflow",
        "call_id": call["call_id"],
        "call_status": status["status"],
        "call_duration": status.get("duration", 0),
        "call_summary": call_summary,
        "ended_call": ended_call,
    }


@workflow_trace
async def workflow_sequence_1() -> Dict:
    """
    Workflow Sequence 1: Vapi → GPT → Google Calendar
    Tests: Call management → AI analysis → Calendar scheduling
    """
    vapi = MockVapiClient()
    calendar = MockCalendarClient()
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    # Step 1: Create Vapi call
    call = await vapi.create_call(phone_number="+1234567890", assistant_id="assistant_123")
    
    # Step 2: Use GPT to analyze call purpose
    analysis_resp = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a call analysis assistant."},
            {"role": "user", "content": f"Analyze this call ID {call['call_id']} and suggest what calendar event should be created."}
        ],
        max_tokens=100,
        temperature=0.7,
    )
    analysis = analysis_resp.choices[0].message.content
    
    # Step 3: Create calendar event based on analysis
    event = await calendar.create_event(
        summary=analysis[:50] if analysis else "Follow-up Meeting",
        start_time="2024-01-15T14:00:00Z",
        end_time="2024-01-15T15:00:00Z"
    )
    
    return {
        "workflow": "workflow_sequence_1",
        "sequence": "vapi → gpt → gcal",
        "call_id": call["call_id"],
        "gpt_analysis": analysis,
        "calendar_event": event,
    }


@workflow_trace
async def workflow_sequence_2() -> Dict:
    """
    Workflow Sequence 2: Google Calendar → GPT → Vapi
    Tests: Calendar check → AI decision → Call initiation
    """
    calendar = MockCalendarClient()
    vapi = MockVapiClient()
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    # Step 1: List calendar events
    events = await calendar.list_events(calendar_id="primary", max_results=10)
    
    # Step 2: Use GPT to decide if a call is needed
    decision_resp = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a scheduling assistant. Decide if a call is needed based on calendar events."},
            {"role": "user", "content": f"Based on these events: {events}, should I make a call? If yes, suggest who to call."}
        ],
        max_tokens=100,
        temperature=0.7,
    )
    decision = decision_resp.choices[0].message.content
    
    # Step 3: Create Vapi call if needed
    if "yes" in decision.lower() or "call" in decision.lower():
        call = await vapi.create_call(phone_number="+1234567890", assistant_id="assistant_123")
        return {
            "workflow": "workflow_sequence_2",
            "sequence": "gcal → gpt → vapi",
            "events_found": len(events),
            "gpt_decision": decision,
            "call_created": call,
        }
    
    return {
        "workflow": "workflow_sequence_2",
        "sequence": "gcal → gpt → vapi",
        "events_found": len(events),
        "gpt_decision": decision,
        "call_created": None,
    }


@workflow_trace
async def workflow_sequence_3() -> Dict:
    """
    Workflow Sequence 3: Gmail → GPT → Vapi → Calendar
    Tests: Email processing → AI extraction → Call → Calendar update
    """
    gmail = MockGmailClient()
    vapi = MockVapiClient()
    calendar = MockCalendarClient()
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    # Step 1: Get email
    messages = await gmail.list_messages(query="is:unread", max_results=1)
    if not messages:
        return {"workflow": "workflow_sequence_3", "sequence": "gmail → gpt → vapi → gcal", "error": "No messages"}
    
    message = await gmail.get_message(messages[0]["id"])
    
    # Step 2: Use GPT to extract action items
    extraction_resp = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an email analysis assistant. Extract action items."},
            {"role": "user", "content": f"Extract action items from this email:\n{message.get('subject', '')}\n{message.get('body', '')}"}
        ],
        max_tokens=100,
        temperature=0.7,
    )
    action_items = extraction_resp.choices[0].message.content
    
    # Step 3: Create Vapi call to discuss action items
    call = await vapi.create_call(phone_number="+1234567890", assistant_id="assistant_123")
    
    # Step 4: Create calendar event for follow-up
    event = await calendar.create_event(
        summary=f"Follow-up: {action_items[:30]}" if action_items else "Email Follow-up",
        start_time="2024-01-16T10:00:00Z",
        end_time="2024-01-16T11:00:00Z"
    )
    
    return {
        "workflow": "workflow_sequence_3",
        "sequence": "gmail → gpt → vapi → gcal",
        "email_id": message["id"],
        "action_items": action_items,
        "call_id": call["call_id"],
        "calendar_event": event,
    }


async def run_all_workflows() -> Dict:
    """
    Run multiple distinct workflows with different sequences to test workflow separation.
    Each workflow runs independently and should create separate traces.
    
    NOTE: This function is NOT wrapped with @workflow_trace because each
    individual workflow should have its own separate trace.
    """
    results = {}
    
    # Workflow 1: Vapi → GPT → Calendar (creates its own trace)
    results["sequence_1"] = await workflow_sequence_1()
    
    # Small delay to ensure separation
    await asyncio.sleep(0.1)
    
    # Workflow 2: Calendar → GPT → Vapi (creates its own trace)
    results["sequence_2"] = await workflow_sequence_2()
    
    # Small delay to ensure separation
    await asyncio.sleep(0.1)
    
    # Workflow 3: Gmail → GPT → Vapi → Calendar (creates its own trace)
    results["sequence_3"] = await workflow_sequence_3()
    
    return {
        "workflow": "run_all_workflows",
        "total_workflows": 3,
        "workflow_sequences": [
            "vapi → gpt → gcal",
            "gcal → gpt → vapi",
            "gmail → gpt → vapi → gcal",
        ],
        "results": results,
    }

