"""
Test edge cases and fixes for production readiness.

TESTS:
1. Retry detection (should not double-count)
2. Failed request handling (5xx should not be tracked)
3. Rate limit detection (429 should not be tracked)
4. Batch API pricing (50% discount)
5. Clock skew detection
6. Concurrent requests (no race conditions)
7. Streaming responses
"""
import asyncio
import time
import sys
import os

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../sdk/python"))

import llmobserve
from llmobserve import request_tracker

# Mock httpx for testing
import httpx
from unittest.mock import Mock, patch


class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def test_retry_detection():
    """Test that retries are detected and not double-counted."""
    print(f"\n{Color.BLUE}Test 1: Retry Detection{Color.END}")
    
    # Generate request ID
    request_id = request_tracker.generate_request_id(
        "POST",
        "https://api.openai.com/v1/chat/completions",
        b'{"model": "gpt-4"}'
    )
    
    # First request - should track
    is_tracked_1 = request_tracker.is_request_tracked(request_id)
    request_tracker.mark_request_tracked(request_id)
    
    # Retry - should detect
    is_tracked_2 = request_tracker.is_request_tracked(request_id)
    
    if not is_tracked_1 and is_tracked_2:
        print(f"  {Color.GREEN}✓ Retry detection working{Color.END}")
        print(f"    - First request: tracked=False (good)")
        print(f"    - Retry: tracked=True (good, will skip)")
        return True
    else:
        print(f"  {Color.RED}✗ Retry detection failed{Color.END}")
        return False


def test_status_code_filtering():
    """Test that only appropriate status codes are tracked."""
    print(f"\n{Color.BLUE}Test 2: Status Code Filtering{Color.END}")
    
    test_cases = [
        (200, True, "2xx success"),
        (201, True, "2xx success"),
        (400, True, "4xx client error (still charged)"),
        (401, True, "4xx client error (still charged)"),
        (429, False, "4xx rate limit (not charged)"),
        (500, False, "5xx server error (not charged)"),
        (502, False, "5xx server error (not charged)"),
    ]
    
    all_passed = True
    for status_code, expected, description in test_cases:
        result = request_tracker.should_track_response(status_code)
        if result == expected:
            print(f"  {Color.GREEN}✓ {status_code} ({description}): {'track' if result else 'skip'}{Color.END}")
        else:
            print(f"  {Color.RED}✗ {status_code} ({description}): expected {expected}, got {result}{Color.END}")
            all_passed = False
    
    return all_passed


def test_rate_limit_detection():
    """Test rate limit detection from headers."""
    print(f"\n{Color.BLUE}Test 3: Rate Limit Detection{Color.END}")
    
    # Simulate 429 response with headers
    headers = {
        "Retry-After": "60",
        "X-RateLimit-Limit": "100",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": "1699999999"
    }
    
    rate_limit_info = request_tracker.detect_rate_limit(429, headers)
    
    if rate_limit_info and rate_limit_info["rate_limited"]:
        print(f"  {Color.GREEN}✓ Rate limit detected{Color.END}")
        print(f"    - Retry after: {rate_limit_info['retry_after']}s")
        print(f"    - Limit: {rate_limit_info['limit']}")
        print(f"    - Remaining: {rate_limit_info['remaining']}")
        return True
    else:
        print(f"  {Color.RED}✗ Rate limit not detected{Color.END}")
        return False


def test_batch_api_detection():
    """Test batch API detection for discounts."""
    print(f"\n{Color.BLUE}Test 4: Batch API Detection{Color.END}")
    
    # OpenAI Batch API URL
    batch_url = "https://api.openai.com/v1/batches"
    regular_url = "https://api.openai.com/v1/chat/completions"
    
    batch_info_1 = request_tracker.extract_batch_api_info(batch_url, {})
    batch_info_2 = request_tracker.extract_batch_api_info(regular_url, {})
    
    passed = True
    
    if batch_info_1 and batch_info_1["is_batch"] and batch_info_1["discount"] == 0.5:
        print(f"  {Color.GREEN}✓ Batch API detected: 50% discount{Color.END}")
    else:
        print(f"  {Color.RED}✗ Batch API not detected{Color.END}")
        passed = False
    
    if batch_info_2 is None:
        print(f"  {Color.GREEN}✓ Regular API: no discount{Color.END}")
    else:
        print(f"  {Color.RED}✗ False positive: regular API detected as batch{Color.END}")
        passed = False
    
    return passed


def test_clock_skew_detection():
    """Test clock skew detection."""
    print(f"\n{Color.BLUE}Test 5: Clock Skew Detection{Color.END}")
    
    current_time = time.time()
    
    # Valid timestamp (now)
    valid = request_tracker.validate_timestamp(current_time)
    
    # Future timestamp (10 minutes ahead) - should fail
    future = request_tracker.validate_timestamp(current_time + 600)
    
    # Past timestamp (10 minutes ago) - should fail
    past = request_tracker.validate_timestamp(current_time - 600)
    
    if valid and not future and not past:
        print(f"  {Color.GREEN}✓ Clock skew detection working{Color.END}")
        print(f"    - Current time: valid")
        print(f"    - +10min: invalid (clock skew)")
        print(f"    - -10min: invalid (clock skew)")
        return True
    else:
        print(f"  {Color.RED}✗ Clock skew detection failed{Color.END}")
        return False


async def test_concurrent_requests():
    """Test that concurrent requests don't interfere."""
    print(f"\n{Color.BLUE}Test 6: Concurrent Requests{Color.END}")
    
    # Initialize SDK
    llmobserve.observe(
        collector_url="http://localhost:8000",
        api_key="test_key"
    )
    
    # Track requests by ID
    request_ids = set()
    
    async def make_request(id: int):
        """Simulate concurrent request."""
        # Each request should have its own context
        llmobserve.context.set_customer_id(f"customer_{id}")
        
        # Generate unique request ID
        req_id = request_tracker.generate_request_id(
            "POST",
            f"https://api.openai.com/test/{id}",
            f"request_{id}".encode()
        )
        request_ids.add(req_id)
        
        # Simulate work
        await asyncio.sleep(0.01)
        
        # Verify context is preserved
        customer_id = llmobserve.context.get_customer_id()
        return customer_id == f"customer_{id}"
    
    # Run 10 concurrent requests
    results = await asyncio.gather(*[make_request(i) for i in range(10)])
    
    # Check all contexts were preserved
    all_passed = all(results) and len(request_ids) == 10
    
    if all_passed:
        print(f"  {Color.GREEN}✓ Concurrent requests handled correctly{Color.END}")
        print(f"    - 10 concurrent requests")
        print(f"    - 10 unique request IDs")
        print(f"    - All contexts preserved")
        return True
    else:
        print(f"  {Color.RED}✗ Concurrent requests had issues{Color.END}")
        print(f"    - Expected 10 unique IDs, got {len(request_ids)}")
        return False


def test_lru_cache_bounds():
    """Test that request tracker cache is bounded."""
    print(f"\n{Color.BLUE}Test 7: LRU Cache Bounds{Color.END}")
    
    # Generate more than max cache size
    max_size = request_tracker._max_cache_size
    
    # Clear cache first
    request_tracker._tracked_requests.clear()
    
    # Add max_size + 100 requests
    for i in range(max_size + 100):
        req_id = request_tracker.generate_request_id(
            "GET",
            f"https://api.test.com/{i}",
            None
        )
        request_tracker.mark_request_tracked(req_id)
    
    cache_size = len(request_tracker._tracked_requests)
    
    if cache_size <= max_size:
        print(f"  {Color.GREEN}✓ LRU cache bounded correctly{Color.END}")
        print(f"    - Max size: {max_size}")
        print(f"    - Actual size: {cache_size}")
        print(f"    - Added: {max_size + 100} (oldest evicted)")
        return True
    else:
        print(f"  {Color.RED}✗ Cache unbounded: {cache_size} > {max_size}{Color.END}")
        return False


def main():
    """Run all tests."""
    print(f"{Color.BLUE}{'='*60}{Color.END}")
    print(f"{Color.BLUE}LLMObserve Edge Case Tests{Color.END}")
    print(f"{Color.BLUE}{'='*60}{Color.END}")
    
    tests = [
        ("Retry Detection", test_retry_detection),
        ("Status Code Filtering", test_status_code_filtering),
        ("Rate Limit Detection", test_rate_limit_detection),
        ("Batch API Detection", test_batch_api_detection),
        ("Clock Skew Detection", test_clock_skew_detection),
        ("Concurrent Requests", lambda: asyncio.run(test_concurrent_requests())),
        ("LRU Cache Bounds", test_lru_cache_bounds),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"  {Color.RED}✗ Test crashed: {e}{Color.END}")
            results.append((name, False))
    
    # Summary
    print(f"\n{Color.BLUE}{'='*60}{Color.END}")
    print(f"{Color.BLUE}Summary{Color.END}")
    print(f"{Color.BLUE}{'='*60}{Color.END}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = f"{Color.GREEN}PASS{Color.END}" if passed else f"{Color.RED}FAIL{Color.END}"
        print(f"  {status} {name}")
    
    print(f"\n{Color.BLUE}Result: {passed_count}/{total_count} tests passed{Color.END}")
    
    if passed_count == total_count:
        print(f"{Color.GREEN}✓ All tests passed! Ready for launch.{Color.END}")
        return 0
    else:
        print(f"{Color.RED}✗ Some tests failed. Fix before launch.{Color.END}")
        return 1


if __name__ == "__main__":
    exit(main())

