"""
Test script to verify GPT and Pinecone instrumentation still works.

This test:
1. Makes a GPT call (should be auto-instrumented)
2. Makes a Pinecone query (should be auto-instrumented)
3. Verifies spans are created and costs are tracked
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try parent directory
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

async def test_gpt_call():
    """Test GPT call instrumentation."""
    print("🧪 Testing GPT call instrumentation...")
    
    try:
        import openai
        from llmobserve.config import settings
        
        # Initialize OpenAI client
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        
        # Make a simple GPT call
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say hello in one word"}],
            temperature=0.7,
        )
        
        print(f"✅ GPT call successful: {response.choices[0].message.content[:50]}")
        
        # Check if usage is available
        if hasattr(response, "usage"):
            print(f"   Tokens: {response.usage.total_tokens} (prompt: {response.usage.prompt_tokens}, completion: {response.usage.completion_tokens})")
        
        return True
        
    except Exception as e:
        print(f"❌ GPT call failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_pinecone_query():
    """Test Pinecone query instrumentation."""
    print("\n🧪 Testing Pinecone query instrumentation...")
    
    try:
        import pinecone
        from llmobserve.config import settings
        
        # Initialize Pinecone client
        pc = pinecone.Pinecone(api_key=settings.pinecone_api_key)
        index_name = settings.pinecone_index_name or "test"
        
        # Get index
        index = pc.Index(index_name)
        
        # Make a simple query (with a dummy vector)
        # Use dimension 1024 (common Pinecone dimension)
        dummy_vector = [0.0] * 1024
        
        result = index.query(
            vector=dummy_vector,
            top_k=3,
            include_metadata=True
        )
        
        print(f"✅ Pinecone query successful")
        if isinstance(result, dict) and "matches" in result:
            print(f"   Matches: {len(result['matches'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pinecone query failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_simulate_agent():
    """Test the full simulate_agent workflow."""
    print("\n🧪 Testing simulate_agent workflow...")
    
    try:
        from llmobserve.demo.simulate_agent import simulate_agent_workflow
        
        result = await simulate_agent_workflow()
        
        print(f"✅ Simulate agent workflow successful")
        query = result.get('query', '')
        summary = result.get('summary', '')
        if isinstance(query, str):
            print(f"   Query: {query[:50]}")
        else:
            print(f"   Query: {str(query)[:50]}")
        if isinstance(summary, str):
            print(f"   Summary: {summary[:50]}")
        else:
            print(f"   Summary: {str(summary)[:50]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Simulate agent workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def check_spans_in_db():
    """Check if spans were written to database."""
    print("\n🧪 Checking if spans were written to database...")
    
    try:
        from llmobserve.storage.repo import SpanRepository
        
        # Wait a bit for async writes to complete
        await asyncio.sleep(3)
        
        repo = SpanRepository()
        
        # Get recent spans
        recent_spans = repo.get_spans(limit=10)
        
        print(f"✅ Found {len(recent_spans)} recent spans in database")
        
        for span in recent_spans[:5]:
            print(f"   - {span.name}: cost=${span.cost_usd:.6f}, tokens={span.total_tokens or 0}")
        
        return len(recent_spans) > 0
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing GPT and Pinecone Instrumentation")
    print("=" * 60)
    
    results = []
    
    # Test GPT call
    results.append(("GPT Call", await test_gpt_call()))
    
    # Test Pinecone query
    results.append(("Pinecone Query", await test_pinecone_query()))
    
    # Test full workflow
    results.append(("Simulate Agent", await test_simulate_agent()))
    
    # Check database
    results.append(("Database Spans", await check_spans_in_db()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed")
    
    return all_passed


if __name__ == "__main__":
    # Import llmobserve to trigger auto-instrumentation
    import llmobserve
    
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

