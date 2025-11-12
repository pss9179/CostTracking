"""
Test hierarchical tracking with nested sections.

This should automatically create parent-child relationships when using nested sections.
"""
import os
import sys
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from llmobserve import observe, section
from openai import OpenAI

# Initialize
COLLECTOR_URL = os.getenv("LLMOBSERVE_COLLECTOR_URL", "http://localhost:8000")
API_KEY = "llmo_sk_d184d2df8968d4f8365f7b1b85f4647d4bdadcc3798a0573"

observe(collector_url=COLLECTOR_URL, api_key=API_KEY)

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    print("\n❌ OPENAI_API_KEY not set in environment!")
    print("   Set it in your .env file or export it:")
    print("   export OPENAI_API_KEY=sk-...")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_KEY)

print("🧪 Testing Hierarchical Tracking with Nested Sections")
print("=" * 70)

# Test: Nested sections should create parent-child relationships
with section("agent:research_assistant"):
    print("\n📦 In agent:research_assistant section")
    
    with section("step:gather_data"):
        print("  📦 In step:gather_data section")
        
        with section("tool:web_search"):
            print("    📦 In tool:web_search section")
            
            # This should have parent_span_id = web_search span
            print("    🔍 Calling OpenAI embedding...")
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input="test query"
            )
            print(f"    ✅ Embedding created: {response.data[0].embedding[:3]}...")
    
    with section("step:synthesize"):
        print("  📦 In step:synthesize section")
        
        # This should have parent_span_id = synthesize span
        print("  💬 Calling OpenAI chat...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10
        )
        print(f"  ✅ Chat response: {response.choices[0].message.content}")

print("\n" + "=" * 70)
print("✅ Test complete! Check the dashboard:")
print("   1. Go to http://localhost:3000")
print("   2. Click into the latest run")
print("   3. Click 'Hierarchical Trace' tab")
print("   4. You should see:")
print("")
print("      └─ agent:research_assistant")
print("         ├─ step:gather_data")
print("         │  └─ tool:web_search")
print("         │     └─ embedding (text-embedding-3-small)")
print("         └─ step:synthesize")
print("            └─ chat (gpt-4o-mini)")
print("")

