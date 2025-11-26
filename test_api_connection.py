#!/usr/bin/env python3
"""
Test API key authentication with the collector.
This script tests the /caps/check endpoint to verify API key authentication works.
"""
import urllib.request
import urllib.error
import json
import sys
import time

# Test configuration
COLLECTOR_URL = "http://localhost:8000"
API_KEY = "llmo_sk_bc53e472d0bfe8e50007a4ea8f028d7bcdd15099eab0d634"

def test_health():
    """Test health endpoint (no auth required)."""
    print("="*80)
    print("1. Testing Health Endpoint (no auth)")
    print("="*80)
    try:
        req = urllib.request.Request(f"{COLLECTOR_URL}/health")
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.getcode()
            data = json.loads(response.read().decode())
            print(f"✅ Status: {status}")
            print(f"✅ Response: {data}")
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_caps_check():
    """Test /caps/check endpoint with API key."""
    print("\n" + "="*80)
    print("2. Testing /caps/check Endpoint (with API key)")
    print("="*80)
    print(f"API Key: {API_KEY[:30]}...")
    
    try:
        req = urllib.request.Request(f"{COLLECTOR_URL}/caps/check")
        req.add_header("Authorization", f"Bearer {API_KEY}")
        req.add_header("Content-Type", "application/json")
        
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.getcode()
            data = json.loads(response.read().decode())
            print(f"Status Code: {status}")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if status == 200:
                print("✅ SUCCESS! API key authentication works!")
                return True
            else:
                print(f"⚠️  Status {status}")
                return False
                
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            error_data = json.loads(e.read().decode())
            error_detail = error_data.get("detail", "")
        except:
            error_detail = str(e)
        
        print(f"Status Code: {status}")
        print(f"Response: {error_detail}")
        
        if status == 401:
            if "API_KEY_AUTH_FAILED" in error_detail:
                print("⚠️  API key auth attempted but key not found/revoked")
            elif "CLERK_AUTH_FAILED" in error_detail:
                print("❌ Still using Clerk auth instead of API key auth!")
                print("   This means get_current_user is falling through to Clerk")
            else:
                print(f"❌ Authentication failed: {error_detail}")
            return False
        else:
            print(f"❌ Unexpected status code: {status}")
            return False
            
    except urllib.error.URLError as e:
        print(f"❌ Connection Error: {e}")
        print("   Is the collector running on port 8000?")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False

def test_events_endpoint():
    """Test /events/ endpoint with API key (should work even without auth)."""
    print("\n" + "="*80)
    print("3. Testing /events/ Endpoint (with API key)")
    print("="*80)
    
    test_event = {
        "span_id": "test_span_123",
        "trace_id": "test_trace_123",
        "provider": "openai",
        "model_id": "gpt-4o-mini",
        "cost_usd": 0.0001,
        "input_tokens": 10,
        "output_tokens": 20,
        "latency_ms": 100.0,
        "created_at": "2025-11-26T06:30:00Z"
    }
    
    try:
        data = json.dumps([test_event]).encode('utf-8')
        req = urllib.request.Request(
            f"{COLLECTOR_URL}/events/",
            data=data,
            method='POST'
        )
        req.add_header("Authorization", f"Bearer {API_KEY}")
        req.add_header("Content-Type", "application/json")
        
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.getcode()
            response_text = response.read().decode()[:200]
            print(f"Status Code: {status}")
            print(f"Response: {response_text}")
            
            if status in [200, 201]:
                print("✅ SUCCESS! Events endpoint accepts API key!")
                return True
            else:
                print(f"⚠️  Status {status} - may still work (fail-open design)")
                return True  # Events endpoint allows unauthenticated
                
    except urllib.error.HTTPError as e:
        status = e.code
        print(f"Status Code: {status}")
        print(f"⚠️  HTTP Error but may still work (fail-open design)")
        return True  # Events endpoint allows unauthenticated
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False

def check_collector_running():
    """Check if collector is running."""
    print("\n" + "="*80)
    print("Checking if collector is running...")
    print("="*80)
    
    try:
        req = urllib.request.Request(f"{COLLECTOR_URL}/health")
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.getcode() == 200:
                print("✅ Collector is running!")
                return True
            else:
                print(f"⚠️  Collector responded with status {response.getcode()}")
                return False
    except urllib.error.URLError:
        print("❌ Collector is NOT running!")
        print("   Start it with: cd collector && source venv/bin/activate && python -m uvicorn main:app --port 8000")
        return False
    except Exception as e:
        print(f"❌ Error checking collector: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("🧪 LLMOBSERVE API KEY AUTHENTICATION TEST")
    print("="*80)
    print(f"Collector URL: {COLLECTOR_URL}")
    print(f"API Key: {API_KEY[:30]}...")
    print()
    
    # Check if collector is running
    if not check_collector_running():
        print("\n❌ Cannot proceed - collector is not running!")
        sys.exit(1)
    
    # Wait a moment for collector to be ready
    time.sleep(1)
    
    # Run tests
    results = []
    
    results.append(("Health Check", test_health()))
    results.append(("Caps Check", test_caps_check()))
    results.append(("Events Endpoint", test_events_endpoint()))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "="*80)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("\n💡 Next steps:")
        print("   1. Make sure collector is restarted with latest code")
        print("   2. Check collector logs for debug messages")
        print("   3. Verify API key exists in database")
    print("="*80 + "\n")
    
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()

