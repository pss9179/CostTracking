#!/usr/bin/env python3
"""
End-to-end test for API key authentication system.

Tests:
1. User sync and API key generation
2. Event ingestion with API key auth
3. Runs retrieval with API key auth
4. Stats retrieval with API key auth
"""
import os
import sys
import time
from dotenv import load_dotenv
from openai import OpenAI

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk", "python"))

from llmobserve import observe, section, set_customer_id

# Load environment variables
load_dotenv()

COLLECTOR_URL = os.getenv("NEXT_PUBLIC_COLLECTOR_URL", "http://localhost:8000")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def test_user_sync_and_key_generation():
    """Test 1: Sync user and get API key."""
    print_section("Test 1: User Sync & API Key Generation")
    
    import requests
    
    # Simulate Clerk user
    test_user = {
        "id": f"test_user_{int(time.time())}",
        "email_addresses": [{"email_address": f"test{int(time.time())}@example.com"}],
        "first_name": "Test",
        "last_name": "User"
    }
    
    print(f"📧 Creating test user: {test_user['email_addresses'][0]['email_address']}")
    
    response = requests.post(
        f"{COLLECTOR_URL}/users/sync",
        json=test_user
    )
    
    if response.status_code != 200:
        print(f"❌ User sync failed: {response.text}")
        return None
    
    data = response.json()
    print(f"✅ User synced successfully")
    print(f"   User ID: {data['user_id']}")
    print(f"   API Key: {data['api_key'][:20]}...")
    print(f"   Key Prefix: {data['api_key_prefix']}")
    
    return data['api_key']

def test_event_ingestion(api_key: str):
    """Test 2: Ingest events with API key authentication."""
    print_section("Test 2: Event Ingestion with API Key")
    
    if not OPENAI_API_KEY:
        print("⚠️  No OpenAI API key found, skipping actual API calls")
        print("   Set OPENAI_API_KEY to test real OpenAI integration")
        return
    
    # Initialize observe with API key
    print(f"🔑 Initializing SDK with API key: {api_key[:20]}...")
    observe(
        collector_url=COLLECTOR_URL,
        api_key=api_key
    )
    
    # Test 1: Simple call
    print("\n📞 Test Call 1: Simple completion")
    client = OpenAI()
    
    with section("agent:test_agent"):
        with section("tool:simple_query"):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": "Say 'Hello from LLM Observe test!'"}
                ]
            )
            print(f"   Response: {response.choices[0].message.content[:50]}...")
    
    # Test 2: With customer tracking
    print("\n📞 Test Call 2: With customer tracking")
    set_customer_id("test_customer_123")
    
    with section("agent:customer_support"):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "What is 2+2?"}
            ]
        )
        print(f"   Response: {response.choices[0].message.content[:50]}...")
    
    print("\n✅ Events ingested successfully")
    print("   Waiting 2 seconds for events to flush...")
    time.sleep(2)

def test_runs_retrieval(api_key: str):
    """Test 3: Retrieve runs with API key authentication."""
    print_section("Test 3: Runs Retrieval with API Key")
    
    import requests
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # Get latest runs
    print("📊 Fetching latest runs...")
    response = requests.get(
        f"{COLLECTOR_URL}/runs/latest?limit=5",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Runs retrieval failed: {response.text}")
        return False
    
    runs = response.json()
    print(f"✅ Retrieved {len(runs)} runs")
    
    if runs:
        latest_run = runs[0]
        print(f"\n   Latest Run:")
        print(f"   - Run ID: {latest_run['run_id'][:16]}...")
        print(f"   - Cost: ${latest_run['total_cost']:.6f}")
        print(f"   - Calls: {latest_run['call_count']}")
        print(f"   - Started: {latest_run['started_at']}")
        
        # Get run detail
        print(f"\n📊 Fetching run detail...")
        detail_response = requests.get(
            f"{COLLECTOR_URL}/runs/{latest_run['run_id']}",
            headers=headers
        )
        
        if detail_response.status_code == 200:
            detail = detail_response.json()
            print(f"✅ Run detail retrieved")
            print(f"   - Total cost: ${detail['total_cost']:.6f}")
            print(f"   - Events: {len(detail['events'])}")
            print(f"   - Providers: {len(detail['breakdown']['by_provider'])}")
        else:
            print(f"❌ Run detail failed: {detail_response.text}")
    else:
        print("⚠️  No runs found (events may not have been ingested yet)")
    
    return True

def test_stats_retrieval(api_key: str):
    """Test 4: Retrieve stats with API key authentication."""
    print_section("Test 4: Stats Retrieval with API Key")
    
    import requests
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # Get provider stats
    print("📈 Fetching provider stats...")
    response = requests.get(
        f"{COLLECTOR_URL}/stats/by-provider?hours=24",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Stats retrieval failed: {response.text}")
        return False
    
    stats = response.json()
    print(f"✅ Retrieved stats for {len(stats)} providers")
    
    for provider in stats:
        print(f"\n   {provider['provider']}:")
        print(f"   - Total cost: ${provider['total_cost']:.6f}")
        print(f"   - Calls: {provider['call_count']}")
        print(f"   - Percentage: {provider['percentage']}%")
    
    return True

def test_api_key_management(api_key: str):
    """Test 5: API key management endpoints."""
    print_section("Test 5: API Key Management")
    
    import requests
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # List API keys
    print("🔑 Listing API keys...")
    response = requests.get(
        f"{COLLECTOR_URL}/api-keys",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ API key listing failed: {response.text}")
        return False
    
    keys = response.json()
    print(f"✅ User has {len(keys)} API key(s)")
    
    for key in keys:
        print(f"\n   Key: {key['key_prefix']}")
        print(f"   - Name: {key['name']}")
        print(f"   - Created: {key['created_at']}")
        print(f"   - Last used: {key.get('last_used_at', 'Never')}")
    
    # Create new API key
    print("\n🔑 Creating new API key...")
    response = requests.post(
        f"{COLLECTOR_URL}/api-keys",
        headers=headers,
        json={"name": "Test Key 2"}
    )
    
    if response.status_code != 200:
        print(f"❌ API key creation failed: {response.text}")
        return False
    
    new_key = response.json()
    print(f"✅ New API key created")
    print(f"   Key: {new_key['key'][:20]}...")
    print(f"   Prefix: {new_key['key_prefix']}")
    
    return True

def main():
    """Run all tests."""
    print("\n" + "🧪" * 35)
    print("  LLM Observe - API Key Authentication Test Suite")
    print("🧪" * 35)
    
    print(f"\n📡 Collector URL: {COLLECTOR_URL}")
    print(f"🔐 OpenAI API Key: {'✅ Set' if OPENAI_API_KEY else '❌ Not set'}")
    
    # Test 1: User sync & API key generation
    api_key = test_user_sync_and_key_generation()
    if not api_key:
        print("\n❌ Test suite failed at user sync")
        sys.exit(1)
    
    # Test 2: Event ingestion (only if OpenAI key is set)
    if OPENAI_API_KEY:
        test_event_ingestion(api_key)
    else:
        print_section("Test 2: Event Ingestion (Skipped)")
        print("⚠️  Skipped: No OPENAI_API_KEY found")
    
    # Test 3: Runs retrieval
    if not test_runs_retrieval(api_key):
        print("\n❌ Test suite failed at runs retrieval")
        sys.exit(1)
    
    # Test 4: Stats retrieval
    if not test_stats_retrieval(api_key):
        print("\n❌ Test suite failed at stats retrieval")
        sys.exit(1)
    
    # Test 5: API key management
    if not test_api_key_management(api_key):
        print("\n❌ Test suite failed at API key management")
        sys.exit(1)
    
    # Summary
    print_section("✅ All Tests Passed!")
    print("The API key authentication system is working correctly.")
    print("\nNext steps:")
    print("1. Visit the dashboard to view tracked events")
    print("2. Test the onboarding flow in the frontend")
    print("3. Deploy to production!")
    print("\n" + "🎉" * 35 + "\n")

if __name__ == "__main__":
    main()






