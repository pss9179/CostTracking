"""
Test sending Vapi call data to LOCAL collector with FULL usage metrics.
"""
import os
import time
import sys

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sdk/python'))

# Configure llmobserve for LOCAL collector
from llmobserve import config as llmobserve_config
from llmobserve.transport import flush_events
from llmobserve import set_log_level

llmobserve_config.configure(
    api_key="llmo_sk_5d1b22c46c63e0943b4bda5eac3d293f95cb06d5831b182a",
    collector_url="http://localhost:8000",  # LOCAL
)
set_log_level("DEBUG")

# Manually track the call data from the ACTUAL Vapi call
from llmobserve.instrumentation.vapi_instrumentor import track_vapi_call

print("=== Sending Vapi call data to LOCAL collector ===")
print("=== WITH FULL USAGE METRICS ===")

# Data from the actual Vapi call - with FULL usage metrics now
call_id = "019ac28b-08d6-7aa6-a39b-d9ce2264679b"
assistant_id = "3573b8dd-f031-4338-8cef-f8cc548dc415"
duration = 26.761

# FULL cost breakdown including usage metrics
cost_breakdown = {
    "stt": 0.0052,
    "llm": 0.0087,
    "tts": 0.0510,
    "transport": 0.0,
    "vapi": 0.0223,
    "total": 0.0891,
    # USAGE METRICS - these are the key for alternative cost calculation!
    "llm_prompt_tokens": 972,
    "llm_completion_tokens": 254,
    "tts_characters": 1019,
}

# Provider/model info from assistant config
stt_provider = "deepgram"
stt_model = "nova-3"
tts_provider = "vapi"
tts_model = "default"
llm_provider = "openai"
llm_model = "gpt-4o"

track_vapi_call(
    method_name="calls.get",
    call_duration_seconds=duration,
    latency_ms=0,
    status="ok",
    call_id=call_id,
    assistant_id=assistant_id,
    is_voice_call=True,
    cost_breakdown=cost_breakdown,
    transcript="Test call transcript - user spoke for ~27 seconds",
    stt_provider=stt_provider,
    stt_model=stt_model,
    tts_provider=tts_provider,
    tts_model=tts_model,
    llm_provider=llm_provider,
    llm_model=llm_model,
)
print("Events tracked with usage metrics:")
print(f"  - LLM: {cost_breakdown['llm_prompt_tokens']} prompt + {cost_breakdown['llm_completion_tokens']} completion tokens")
print(f"  - TTS: {cost_breakdown['tts_characters']} characters")
print(f"  - STT: {duration:.1f} seconds")

# Flush events
print("\n=== Flushing events to LOCAL collector ===")
flush_events()
time.sleep(2)

print("\n✅ Done! Check http://localhost:3000/voice-agents")
print("The 'What If Calculator' should now show REAL alternative costs!")
