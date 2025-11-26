"""
Test script to verify OpenAI cost tracking with LLMObserve.
"""
import os
import sys
from openai import OpenAI

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sdk', 'python'))

from llmobserve import observe

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize LLMObserve
print("🚀 Initializing LLMObserve...")
observe(
    collector_url="http://localhost:8000",
    api_key="llmo_sk_f27c7f7f73a40172b8bf9d226ced22255b5036dccc8050d2"
)
print("✅ LLMObserve initialized!\n")

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("❌ OPENAI_API_KEY not found in environment")
    sys.exit(1)

client = OpenAI(api_key=openai_api_key)

print("=" * 60)
print("TEST 1: Simple GPT-4o-mini Chat Completion")
print("=" * 60)

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in exactly 5 words."}
        ],
        max_tokens=50
    )
    
    print(f"✅ Response: {response.choices[0].message.content}")
    print(f"📊 Tokens used: {response.usage.total_tokens}")
    print(f"   - Prompt: {response.usage.prompt_tokens}")
    print(f"   - Completion: {response.usage.completion_tokens}")
    print()
except Exception as e:
    print(f"❌ Error: {e}\n")

print("=" * 60)
print("TEST 2: GPT-3.5-turbo Chat Completion")
print("=" * 60)

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "What is 2+2? Answer in one word."}
        ],
        max_tokens=10
    )
    
    print(f"✅ Response: {response.choices[0].message.content}")
    print(f"📊 Tokens used: {response.usage.total_tokens}")
    print()
except Exception as e:
    print(f"❌ Error: {e}\n")

print("=" * 60)
print("TEST 3: Multiple Calls (Batch Test)")
print("=" * 60)

questions = [
    "What color is the sky?",
    "What is the capital of France?",
    "Name one planet in our solar system."
]

for i, question in enumerate(questions, 1):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": question}],
            max_tokens=20
        )
        print(f"✅ Question {i}: {question}")
        print(f"   Answer: {response.choices[0].message.content}")
        print(f"   Tokens: {response.usage.total_tokens}")
    except Exception as e:
        print(f"❌ Question {i} failed: {e}")

print("\n" + "=" * 60)
print("✅ All tests completed!")
print("=" * 60)
print("\n📊 Check the dashboard at http://localhost:3000/dashboard")
print("   to see the tracked costs and metrics!")















