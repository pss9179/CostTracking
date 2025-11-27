"""
Test Vapi call with llmobserve tracking.
Makes a real outbound call and verifies cost breakdown tracking.
"""
import os
import time
import sys

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sdk/python'))

# Load env vars
from dotenv import load_dotenv
load_dotenv()

# Get Vapi config from env
VAPI_API_KEY = os.getenv("VAPI_PRIVATE_KEY")
ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID")
PHONE_NUMBER_ID = os.getenv("VAPI_PHONE_NUMBER_ID")

print(f"VAPI_API_KEY: {VAPI_API_KEY[:10]}...")
print(f"ASSISTANT_ID: {ASSISTANT_ID}")
print(f"PHONE_NUMBER_ID: {PHONE_NUMBER_ID}")

# Configure llmobserve BEFORE using it
from llmobserve import config as llmobserve_config
from llmobserve.transport import flush_events
from llmobserve import set_log_level

llmobserve_config.configure(
    api_key="llmo_sk_5d1b22c46c63e0943b4bda5eac3d293f95cb06d5831b182a",
    collector_url="https://llmobserve-api-production-d791.up.railway.app",
)
set_log_level("DEBUG")

# Import Vapi server SDK
from vapi import Vapi

# Initialize Vapi client
client = Vapi(token=VAPI_API_KEY)

# First, let's get the assistant config to see what providers are configured
print("\n=== Assistant Configuration ===")
assistant = client.assistants.get(id=ASSISTANT_ID)

stt_provider = None
stt_model = None
tts_provider = None
tts_model = None
llm_provider = None
llm_model = None

if hasattr(assistant, 'transcriber') and assistant.transcriber:
    stt_provider = getattr(assistant.transcriber, 'provider', 'unknown')
    stt_model = getattr(assistant.transcriber, 'model', 'default')
    print(f"STT Provider: {stt_provider}")
    print(f"STT Model: {stt_model}")

if hasattr(assistant, 'voice') and assistant.voice:
    tts_provider = getattr(assistant.voice, 'provider', 'unknown')
    tts_model = getattr(assistant.voice, 'voiceId', None) or getattr(assistant.voice, 'model', 'default')
    print(f"TTS Provider: {tts_provider}")
    print(f"TTS Model/Voice: {tts_model}")

if hasattr(assistant, 'model') and assistant.model:
    llm_provider = getattr(assistant.model, 'provider', 'unknown')
    llm_model = getattr(assistant.model, 'model', 'unknown')
    print(f"LLM Provider: {llm_provider}")
    print(f"LLM Model: {llm_model}")

# Make outbound call to user's number
print("\n=== Creating outbound call to 630-853-9929 ===")
print("📞 Your phone will ring shortly. Pick up and talk for ~30 seconds!")
print("=" * 50)

try:
    call = client.calls.create(
        assistant_id=ASSISTANT_ID,
        phone_number_id=PHONE_NUMBER_ID,
        customer={
            "number": "+16308539929",  # User's number
        }
    )
    print(f"Call created! ID: {call.id}")
    print(f"Call status: {call.status}")
    
    # Poll for call completion (max 3 minutes)
    call_id = call.id
    print("\n=== Waiting for call to complete ===")
    
    max_wait = 180  # 3 minutes
    poll_interval = 5  # 5 seconds
    waited = 0
    
    while waited < max_wait:
        time.sleep(poll_interval)
        waited += poll_interval
        
        # Get updated call info
        call_details = client.calls.get(id=call_id)
        status = call_details.status
        print(f"  [{waited}s] Status: {status}")
        
        if status in ["ended", "failed", "busy", "no-answer"]:
            break
    
    # Get final call details with cost breakdown
    print("\n=== Final call details ===")
    final_call = client.calls.get(id=call_id)
    
    print(f"Call ID: {final_call.id}")
    print(f"Status: {final_call.status}")
    
    # Try to get duration
    duration = None
    if hasattr(final_call, 'duration'):
        duration = final_call.duration
        print(f"Duration: {duration} seconds")
    elif hasattr(final_call, 'ended_at') and hasattr(final_call, 'started_at'):
        if final_call.ended_at and final_call.started_at:
            from datetime import datetime
            ended = final_call.ended_at if isinstance(final_call.ended_at, datetime) else datetime.fromisoformat(str(final_call.ended_at).replace('Z', '+00:00'))
            started = final_call.started_at if isinstance(final_call.started_at, datetime) else datetime.fromisoformat(str(final_call.started_at).replace('Z', '+00:00'))
            duration = (ended - started).total_seconds()
            print(f"Duration (calculated): {duration} seconds")
    
    # Cost breakdown - manually track since auto-instrumentation might not catch everything
    cost_breakdown = {}
    if hasattr(final_call, 'cost_breakdown') and final_call.cost_breakdown:
        cb = final_call.cost_breakdown
        cost_breakdown = {
            "stt": getattr(cb, 'stt', 0) or 0,
            "llm": getattr(cb, 'llm', 0) or 0,
            "tts": getattr(cb, 'tts', 0) or 0,
            "transport": getattr(cb, 'transport', 0) or 0,
            "vapi": getattr(cb, 'vapi', 0) or 0,
            "total": getattr(cb, 'total', 0) or 0,
            "llm_prompt_tokens": getattr(cb, 'llmPromptTokens', None),
            "llm_completion_tokens": getattr(cb, 'llmCompletionTokens', None),
            "tts_characters": getattr(cb, 'ttsCharacters', None),
        }
        print(f"\nCost Breakdown:")
        print(f"  STT: ${cost_breakdown['stt']:.4f}")
        print(f"  LLM: ${cost_breakdown['llm']:.4f}")
        print(f"  TTS: ${cost_breakdown['tts']:.4f}")
        print(f"  Transport: ${cost_breakdown['transport']:.4f}")
        print(f"  Vapi Fee: ${cost_breakdown['vapi']:.4f}")
        print(f"  TOTAL: ${cost_breakdown['total']:.4f}")
        if cost_breakdown.get('llm_prompt_tokens'):
            print(f"  LLM Prompt Tokens: {cost_breakdown['llm_prompt_tokens']}")
        if cost_breakdown.get('llm_completion_tokens'):
            print(f"  LLM Completion Tokens: {cost_breakdown['llm_completion_tokens']}")
        if cost_breakdown.get('tts_characters'):
            print(f"  TTS Characters: {cost_breakdown['tts_characters']}")
    elif hasattr(final_call, 'costBreakdown') and final_call.costBreakdown:
        cb = final_call.costBreakdown
        cost_breakdown = {
            "stt": getattr(cb, 'stt', 0) or 0,
            "llm": getattr(cb, 'llm', 0) or 0,
            "tts": getattr(cb, 'tts', 0) or 0,
            "transport": getattr(cb, 'transport', 0) or 0,
            "vapi": getattr(cb, 'vapi', 0) or 0,
            "total": getattr(cb, 'total', 0) or 0,
        }
        print(f"\nCost Breakdown:")
        print(f"  STT: ${cost_breakdown['stt']:.4f}")
        print(f"  LLM: ${cost_breakdown['llm']:.4f}")
        print(f"  TTS: ${cost_breakdown['tts']:.4f}")
        print(f"  Transport: ${cost_breakdown['transport']:.4f}")
        print(f"  Vapi Fee: ${cost_breakdown['vapi']:.4f}")
        print(f"  TOTAL: ${cost_breakdown['total']:.4f}")
    elif hasattr(final_call, 'cost'):
        cost_breakdown = {"total": final_call.cost}
        print(f"\nTotal Cost: ${final_call.cost:.4f}")
    
    # Manually track the call if cost breakdown exists
    if cost_breakdown and cost_breakdown.get('total', 0) > 0:
        from llmobserve.instrumentation.vapi_instrumentor import track_vapi_call
        
        transcript = None
        if hasattr(final_call, 'transcript'):
            transcript = final_call.transcript
        elif hasattr(final_call, 'messages') and final_call.messages:
            try:
                messages = final_call.messages
                transcript_parts = []
                for msg in messages[:20]:
                    role = getattr(msg, 'role', None)
                    content = getattr(msg, 'content', None)
                    if role and content:
                        transcript_parts.append(f"{role}: {content}")
                transcript = "\n".join(transcript_parts)[:1000]
            except:
                pass
        
        print(f"\n=== Sending to llmobserve ===")
        track_vapi_call(
            method_name="calls.get",
            call_duration_seconds=duration,
            latency_ms=0,
            status="ok",
            call_id=call_id,
            assistant_id=ASSISTANT_ID,
            is_voice_call=True,
            cost_breakdown=cost_breakdown,
            transcript=transcript,
            stt_provider=stt_provider,
            stt_model=stt_model,
            tts_provider=tts_provider,
            tts_model=tts_model,
            llm_provider=llm_provider,
            llm_model=llm_model,
        )
        print("Events tracked!")
    
    # Flush events
    print("\n=== Flushing events to collector ===")
    flush_events()
    time.sleep(2)  # Give time for flush
    
    print("\n" + "=" * 50)
    print("✅ Test complete! Check the dashboard at:")
    print("   https://llmobserve.com/voice-agents")
    print("   or http://localhost:3000/voice-agents")
    print("=" * 50)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    
    # Still try to flush any events
    flush_events()
