"""
Test DIY voice call with Deepgram STT + OpenAI LLM + ElevenLabs TTS.
Uses diy_voice_call() context manager for cross-platform tracking.
"""
import os
import time
import sys
import base64
import requests

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sdk/python'))

# Load env vars
from dotenv import load_dotenv
load_dotenv()

# API Keys
DEEPGRAM_API_KEY = "0349ba610576e709df23e5cb2e420189b5a785a4"
ELEVENLABS_API_KEY = "sk_d7096f809fecdd454ddfb01b9e77fc43663282fb64b8707d"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print("=" * 60)
print("🧪 DIY Voice Call Test")
print("=" * 60)
print(f"Deepgram Key: {DEEPGRAM_API_KEY[:10]}...")
print(f"ElevenLabs Key: {ELEVENLABS_API_KEY[:10]}...")
print(f"OpenAI Key: {OPENAI_API_KEY[:20]}...")
print()

# Configure llmobserve
from llmobserve import config as llmobserve_config
from llmobserve.transport import flush_events
from llmobserve import set_log_level, diy_voice_call
from openai import OpenAI

llmobserve_config.configure(
    api_key="llmo_sk_5d1b22c46c63e0943b4bda5eac3d293f95cb06d5831b182a",
    collector_url="http://localhost:8000",  # LOCAL collector
)
set_log_level("DEBUG")

# Initialize clients
openai_client = OpenAI(api_key=OPENAI_API_KEY)

print("\n=== Step 1: STT with Deepgram ===")
# Create a simple test audio file (sine wave) or use a real audio file
# For testing, we'll create a minimal WAV file
import wave
import struct
import math

# Generate a simple 1-second test tone
sample_rate = 16000
duration = 1.0
frequency = 440.0  # A4 note

audio_data = []
for i in range(int(sample_rate * duration)):
    value = int(32767.0 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
    audio_data.append(struct.pack('<h', value))

# Save to temporary WAV file
audio_file_path = "/tmp/test_audio.wav"
with wave.open(audio_file_path, 'wb') as wav_file:
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)   # 16-bit
    wav_file.setframerate(sample_rate)
    wav_file.writeframes(b''.join(audio_data))

print(f"Created test audio file: {audio_file_path}")

# Use diy_voice_call context manager
with diy_voice_call(customer_id="test_user_123") as call_id:
    print(f"Voice Call ID: {call_id}")
    print(f"Platform: diy (automatically set)")
    
    # Step 1: STT with Deepgram
    print("\n--- Transcribing with Deepgram ---")
    deepgram_start = time.time()
    
    with open(audio_file_path, 'rb') as audio_file:
        deepgram_response = requests.post(
            'https://api.deepgram.com/v1/listen',
            headers={
                'Authorization': f'Token {DEEPGRAM_API_KEY}',
                'Content-Type': 'audio/wav',
            },
            data=audio_file,
            params={
                'model': 'nova-2',
                'language': 'en-US',
            }
        )
    
    deepgram_latency = (time.time() - deepgram_start) * 1000
    
    if deepgram_response.status_code == 200:
        result = deepgram_response.json()
        transcript = ""
        duration_seconds = 0.0
        
        if 'results' in result and 'channels' in result['results']:
            channels = result['results']['channels']
            if channels and len(channels) > 0:
                alternatives = channels[0].get('alternatives', [])
                if alternatives and len(alternatives) > 0:
                    transcript = alternatives[0].get('transcript', '')
        
        if 'metadata' in result:
            duration_seconds = result['metadata'].get('duration', 0.0)
        
        print(f"✅ Transcript: '{transcript}'")
        print(f"   Duration: {duration_seconds:.2f}s")
        print(f"   Latency: {deepgram_latency:.2f}ms")
        
        # Track Deepgram STT call
        from llmobserve.instrumentation.deepgram_instrumentor import track_deepgram_call
        track_deepgram_call(
            method_name="listen",
            model="nova-2",
            audio_duration_seconds=duration_seconds,
            latency_ms=deepgram_latency,
            status="ok",
            is_streaming=False,
            transcript=transcript,
        )
    else:
        print(f"❌ Deepgram error: {deepgram_response.status_code}")
        print(deepgram_response.text)
        transcript = "Hello, this is a test transcription."
        duration_seconds = 1.0
        
        # Track error
        from llmobserve.instrumentation.deepgram_instrumentor import track_deepgram_call
        track_deepgram_call(
            method_name="listen",
            model="nova-2",
            audio_duration_seconds=duration_seconds,
            latency_ms=deepgram_latency,
            status="error",
            error=f"HTTP {deepgram_response.status_code}: {deepgram_response.text[:200]}",
            is_streaming=False,
        )
    
    # Step 2: LLM with OpenAI
    print("\n--- Generating response with OpenAI ---")
    llm_start = time.time()
    
    # Use the transcript as input
    user_message = transcript if transcript else "Hello, this is a test message."
    
    llm_response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Keep responses brief (1-2 sentences)."},
            {"role": "user", "content": user_message}
        ],
        max_tokens=100,
    )
    
    llm_latency = (time.time() - llm_start) * 1000
    llm_text = llm_response.choices[0].message.content
    input_tokens = llm_response.usage.prompt_tokens
    output_tokens = llm_response.usage.completion_tokens
    
    print(f"✅ Response: '{llm_text}'")
    print(f"   Input tokens: {input_tokens}")
    print(f"   Output tokens: {output_tokens}")
    print(f"   Latency: {llm_latency:.2f}ms")
    
    # Step 3: TTS with ElevenLabs
    print("\n--- Synthesizing speech with ElevenLabs ---")
    tts_start = time.time()
    
    # Use the LLM response for TTS
    tts_text = llm_text
    
    elevenlabs_response = requests.post(
        'https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM',  # Default voice
        headers={
            'xi-api-key': ELEVENLABS_API_KEY,
            'Content-Type': 'application/json',
        },
        json={
            'text': tts_text,
            'model_id': 'eleven_turbo_v2_5',
            'voice_settings': {
                'stability': 0.5,
                'similarity_boost': 0.75,
            }
        }
    )
    
    tts_latency = (time.time() - tts_start) * 1000
    
    if elevenlabs_response.status_code == 200:
        # Save audio to file
        audio_output_path = "/tmp/test_output.wav"
        with open(audio_output_path, 'wb') as f:
            f.write(elevenlabs_response.content)
        
        # Estimate duration (rough: ~150 words per minute, ~10 chars per word)
        char_count = len(tts_text)
        estimated_duration = (char_count / 1500.0) * 60.0  # Rough estimate
        
        print(f"✅ Audio generated: {audio_output_path}")
        print(f"   Characters: {char_count}")
        print(f"   Estimated duration: {estimated_duration:.2f}s")
        print(f"   Latency: {tts_latency:.2f}ms")
        
        # Track ElevenLabs TTS call
        from llmobserve.instrumentation.elevenlabs_instrumentor import track_elevenlabs_tts
        track_elevenlabs_tts(
            method_name="text_to_speech",
            model="eleven_turbo_v2_5",
            character_count=char_count,
            latency_ms=tts_latency,
            voice_id="21m00Tcm4TlvDq8ikWAM",
            status="ok",
        )
    else:
        print(f"❌ ElevenLabs error: {elevenlabs_response.status_code}")
        print(elevenlabs_response.text)
        char_count = len(tts_text)
        estimated_duration = 1.0
        
        # Track error
        from llmobserve.instrumentation.elevenlabs_instrumentor import track_elevenlabs_tts
        track_elevenlabs_tts(
            method_name="text_to_speech",
            model="eleven_turbo_v2_5",
            character_count=char_count,
            latency_ms=tts_latency,
            status="error",
            error=f"HTTP {elevenlabs_response.status_code}: {elevenlabs_response.text[:200]}",
        )

# Flush events
print("\n=== Flushing events to collector ===")
flush_events()
time.sleep(2)  # Give time for flush

print("\n" + "=" * 60)
print("✅ DIY Voice Call Test Complete!")
print("=" * 60)
print(f"Voice Call ID: {call_id}")
print(f"Platform: diy")
print("\nCheck the dashboard at:")
print("   http://localhost:3000/voice-agents")
print("   Look for 'diy' in the Cross-Platform Comparison")
print("=" * 60)

