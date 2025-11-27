"""Check what Vapi actually returns for a completed call."""
import os
from dotenv import load_dotenv
load_dotenv()

from vapi import Vapi

client = Vapi(token=os.getenv("VAPI_PRIVATE_KEY"))

# Get the call we just made
call_id = "019ac28b-08d6-7aa6-a39b-d9ce2264679b"
call = client.calls.get(id=call_id)

print("=== Raw costBreakdown fields ===")
if hasattr(call, 'cost_breakdown') and call.cost_breakdown:
    cb = call.cost_breakdown
    print(f"stt: {getattr(cb, 'stt', 'N/A')}")
    print(f"llm: {getattr(cb, 'llm', 'N/A')}")
    print(f"tts: {getattr(cb, 'tts', 'N/A')}")
    print(f"transport: {getattr(cb, 'transport', 'N/A')}")
    print(f"vapi: {getattr(cb, 'vapi', 'N/A')}")
    print(f"total: {getattr(cb, 'total', 'N/A')}")
    print()
    print("=== Usage metrics (what we need for comparisons) ===")
    print(f"llmPromptTokens: {getattr(cb, 'llmPromptTokens', getattr(cb, 'llm_prompt_tokens', 'NOT FOUND'))}")
    print(f"llmCompletionTokens: {getattr(cb, 'llmCompletionTokens', getattr(cb, 'llm_completion_tokens', 'NOT FOUND'))}")
    print(f"ttsCharacters: {getattr(cb, 'ttsCharacters', getattr(cb, 'tts_characters', 'NOT FOUND'))}")
    
    # Check all attributes
    print()
    print("=== ALL attributes on costBreakdown ===")
    for attr in dir(cb):
        if not attr.startswith('_'):
            val = getattr(cb, attr, None)
            if not callable(val):
                print(f"  {attr}: {val}")
else:
    print("No cost_breakdown found")

# Also check call duration
print()
print("=== Call duration ===")
print(f"duration attr: {getattr(call, 'duration', 'NOT FOUND')}")
print(f"started_at: {getattr(call, 'started_at', 'N/A')}")
print(f"ended_at: {getattr(call, 'ended_at', 'N/A')}")


