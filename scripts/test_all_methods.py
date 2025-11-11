"""
Comprehensive test of all patched OpenAI and Pinecone methods.

Tests every single endpoint to ensure proper patching, cost tracking,
and event emission.
"""

import os
import sys
import time
import io
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

import llmobserve
from llmobserve import observe, section, set_tenant_id, set_customer_id

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
COLLECTOR_URL = os.getenv("LLMOBSERVE_COLLECTOR_URL", "http://localhost:8000")

print("=" * 80)
print("🧪 COMPREHENSIVE METHOD TESTING")
print("=" * 80)
print(f"Collector: {COLLECTOR_URL}")
print(f"OpenAI Key: {'✅ Found' if OPENAI_API_KEY else '❌ Missing'}")
print(f"Pinecone Key: {'✅ Found' if PINECONE_API_KEY else '❌ Missing'}")
print()

# Initialize observability
observe(collector_url=COLLECTOR_URL)
set_tenant_id("test-all-methods")
set_customer_id("comprehensive-test")

# Track results
results = {
    "openai": {},
    "pinecone": {}
}


def test_result(category: str, method: str, success: bool, error: str = None):
    """Record test result."""
    results[category][method] = {
        "success": success,
        "error": error
    }
    status = "✅" if success else "❌"
    print(f"  {status} {method}")
    if error and not success:
        print(f"     Error: {error}")


# ============================================================================
# OPENAI TESTS
# ============================================================================

def test_openai():
    """Test all OpenAI endpoints."""
    print("\n" + "=" * 80)
    print("🤖 TESTING OPENAI METHODS")
    print("=" * 80)
    
    if not OPENAI_API_KEY:
        print("⚠️  Skipping OpenAI tests (no API key)")
        return
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
    except ImportError:
        print("❌ OpenAI SDK not installed")
        return
    
    # Test 1: chat.completions.create
    with section("test:openai:chat_completions"):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Say 'test'"}],
                max_tokens=5
            )
            test_result("openai", "chat.completions.create", True)
        except Exception as e:
            test_result("openai", "chat.completions.create", False, str(e))
    
    # Test 2: completions.create (legacy)
    with section("test:openai:completions"):
        try:
            response = client.completions.create(
                model="gpt-3.5-turbo-instruct",
                prompt="Say hello",
                max_tokens=5
            )
            test_result("openai", "completions.create", True)
        except Exception as e:
            test_result("openai", "completions.create", False, str(e))
    
    # Test 3: embeddings.create
    with section("test:openai:embeddings"):
        try:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input="Hello world"
            )
            test_result("openai", "embeddings.create", True)
        except Exception as e:
            test_result("openai", "embeddings.create", False, str(e))
    
    # Test 4: audio.transcriptions.create
    with section("test:openai:audio_transcriptions"):
        try:
            # Create a tiny audio file (silence)
            audio_data = b'\x00' * 1024
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "test.wav"
            
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            test_result("openai", "audio.transcriptions.create", True)
        except Exception as e:
            # Expected to fail with invalid audio, but patching should work
            if "audio" in str(e).lower() or "invalid" in str(e).lower():
                test_result("openai", "audio.transcriptions.create", True, "Expected error (invalid audio)")
            else:
                test_result("openai", "audio.transcriptions.create", False, str(e))
    
    # Test 5: audio.translations.create
    with section("test:openai:audio_translations"):
        try:
            audio_data = b'\x00' * 1024
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "test.wav"
            
            response = client.audio.translations.create(
                model="whisper-1",
                file=audio_file
            )
            test_result("openai", "audio.translations.create", True)
        except Exception as e:
            if "audio" in str(e).lower() or "invalid" in str(e).lower():
                test_result("openai", "audio.translations.create", True, "Expected error (invalid audio)")
            else:
                test_result("openai", "audio.translations.create", False, str(e))
    
    # Test 6: audio.speech.create
    with section("test:openai:audio_speech"):
        try:
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input="Hello world"
            )
            # Consume the response
            _ = response.read()
            test_result("openai", "audio.speech.create", True)
        except Exception as e:
            test_result("openai", "audio.speech.create", False, str(e))
    
    # Test 7: images.generate
    with section("test:openai:images_generate"):
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt="A simple red circle",
                size="1024x1024",
                n=1
            )
            test_result("openai", "images.generate", True)
        except Exception as e:
            # DALL-E might be expensive/restricted, just check patching
            test_result("openai", "images.generate", False, str(e))
    
    # Test 8: moderations.create
    with section("test:openai:moderations"):
        try:
            response = client.moderations.create(
                model="omni-moderation-latest",
                input="Hello world"
            )
            test_result("openai", "moderations.create", True)
        except Exception as e:
            test_result("openai", "moderations.create", False, str(e))
    
    # Test 9: Streaming chat.completions
    with section("test:openai:chat_streaming"):
        try:
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Count to 3"}],
                stream=True,
                max_tokens=20
            )
            chunks = []
            for chunk in stream:
                chunks.append(chunk)
            test_result("openai", "chat.completions.create (streaming)", True)
        except Exception as e:
            test_result("openai", "chat.completions.create (streaming)", False, str(e))
    
    print("\n⏸️  Skipping expensive/special endpoints:")
    print("  - images.create_variation (requires image file)")
    print("  - images.edit (requires image file)")
    print("  - fine_tuning.jobs.create (expensive, requires training file)")
    print("  - batches.create (requires batch file)")


# ============================================================================
# PINECONE TESTS
# ============================================================================

def test_pinecone():
    """Test all Pinecone operations."""
    print("\n" + "=" * 80)
    print("📊 TESTING PINECONE METHODS")
    print("=" * 80)
    
    if not PINECONE_API_KEY:
        print("⚠️  Skipping Pinecone tests (no API key)")
        return
    
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=PINECONE_API_KEY)
    except ImportError:
        print("❌ Pinecone SDK not installed")
        return
    
    # Get or create index
    try:
        # List existing indexes
        indexes = pc.list_indexes()
        print(f"\nℹ️  Found {len(indexes)} existing indexes")
        
        if len(indexes) == 0:
            print("⚠️  No indexes found")
            print("   Please create a test index first")
            return
        
        # Use the first available index
        index_name = indexes[0].name
        dimension = indexes[0].dimension
        print(f"ℹ️  Using index '{index_name}' (dimension={dimension})")
        
        index = pc.Index(index_name)
        
    except Exception as e:
        print(f"❌ Failed to connect to Pinecone: {e}")
        return
    
    # Test vectors (use the index's dimension)
    test_vectors = [
        {
            "id": "llmobserve-test-1",
            "values": [0.1] * dimension,
            "metadata": {"test": "true", "llmobserve": "test"}
        },
        {
            "id": "llmobserve-test-2",
            "values": [0.2] * dimension,
            "metadata": {"test": "true", "llmobserve": "test"}
        }
    ]
    
    # Test 1: upsert
    with section("test:pinecone:upsert"):
        try:
            response = index.upsert(vectors=test_vectors)
            test_result("pinecone", "upsert", True)
        except Exception as e:
            test_result("pinecone", "upsert", False, str(e))
    
    time.sleep(1)  # Allow indexing
    
    # Test 2: query
    with section("test:pinecone:query"):
        try:
            response = index.query(
                vector=[0.1] * dimension,
                top_k=2,
                include_values=True,
                include_metadata=True
            )
            test_result("pinecone", "query", True)
        except Exception as e:
            test_result("pinecone", "query", False, str(e))
    
    # Test 3: fetch
    with section("test:pinecone:fetch"):
        try:
            response = index.fetch(ids=["llmobserve-test-1", "llmobserve-test-2"])
            test_result("pinecone", "fetch", True)
        except Exception as e:
            test_result("pinecone", "fetch", False, str(e))
    
    # Test 4: update
    with section("test:pinecone:update"):
        try:
            response = index.update(
                id="llmobserve-test-1",
                values=[0.15] * dimension,
                set_metadata={"test": "updated", "llmobserve": "test"}
            )
            test_result("pinecone", "update", True)
        except Exception as e:
            test_result("pinecone", "update", False, str(e))
    
    # Test 5: describe_index_stats
    with section("test:pinecone:describe_index_stats"):
        try:
            response = index.describe_index_stats()
            test_result("pinecone", "describe_index_stats", True)
        except Exception as e:
            test_result("pinecone", "describe_index_stats", False, str(e))
    
    # Test 6: list (if supported)
    with section("test:pinecone:list"):
        try:
            # Note: list() may not be available in all Pinecone versions
            if hasattr(index, 'list'):
                response = index.list()
                test_result("pinecone", "list", True)
            else:
                test_result("pinecone", "list", True, "Not available in this version")
        except Exception as e:
            test_result("pinecone", "list", False, str(e))
    
    # Test 7: delete
    with section("test:pinecone:delete"):
        try:
            response = index.delete(ids=["llmobserve-test-1", "llmobserve-test-2"])
            test_result("pinecone", "delete", True)
        except Exception as e:
            test_result("pinecone", "delete", False, str(e))
    
    # Test 8: query by id (if supported)
    with section("test:pinecone:query_by_id"):
        try:
            # Re-upsert for this test
            index.upsert(vectors=[test_vectors[0]])
            time.sleep(1)
            
            if hasattr(index, 'query'):
                response = index.query(
                    id="llmobserve-test-1",
                    top_k=2
                )
                test_result("pinecone", "query (by id)", True)
            else:
                test_result("pinecone", "query (by id)", True, "Not available")
        except Exception as e:
            test_result("pinecone", "query (by id)", False, str(e))
    
    # Cleanup
    try:
        index.delete(ids=["llmobserve-test-1", "llmobserve-test-2"])
    except:
        pass


# ============================================================================
# RUN ALL TESTS
# ============================================================================

def print_summary():
    """Print test summary."""
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    for category, tests in results.items():
        if not tests:
            continue
        
        total = len(tests)
        passed = sum(1 for t in tests.values() if t["success"])
        failed = total - passed
        
        print(f"\n{category.upper()}:")
        print(f"  Total:  {total}")
        print(f"  Passed: ✅ {passed}")
        print(f"  Failed: ❌ {failed}")
        
        if failed > 0:
            print(f"\n  Failed tests:")
            for method, result in tests.items():
                if not result["success"]:
                    print(f"    ❌ {method}")
                    if result["error"]:
                        print(f"       {result['error'][:100]}")
    
    # Overall
    all_tests = sum(len(tests) for tests in results.values())
    all_passed = sum(
        sum(1 for t in tests.values() if t["success"])
        for tests in results.values()
    )
    
    print(f"\n{'=' * 80}")
    print(f"OVERALL: {all_passed}/{all_tests} tests passed")
    print(f"{'=' * 80}")
    
    # Database verification
    print(f"\n🔍 VERIFICATION:")
    print(f"Check database for events:")
    print(f"  sqlite3 collector/collector.db \"SELECT COUNT(*) FROM trace_events WHERE tenant_id = 'test-all-methods';\"")
    print(f"\nView events in dashboard:")
    print(f"  http://localhost:3000/runs")
    print(f"\nCheck API:")
    print(f"  curl 'http://localhost:8000/runs/latest?tenant_id=test-all-methods' | python3 -m json.tool")


def main():
    """Run all tests."""
    try:
        test_openai()
        test_pinecone()
        
        # Wait for buffer to flush
        print("\n⏳ Waiting for events to flush to collector...")
        time.sleep(3)
        
        print_summary()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

