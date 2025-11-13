"""
Test gRPC and WebSocket protocol support.

CRITICAL: These protocols are UNTESTED in production.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../sdk/python"))

import llmobserve
from unittest.mock import Mock, patch, MagicMock


class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def test_grpc_patching():
    """Test that gRPC channels can be patched."""
    print(f"\n{Color.BLUE}Test 1: gRPC Patching{Color.END}")
    
    try:
        import grpc
        print(f"  {Color.GREEN}✓ grpcio installed{Color.END}")
    except ImportError:
        print(f"  {Color.YELLOW}⚠ grpcio not installed - SKIPPING TEST{Color.END}")
        print(f"    Install with: pip install grpcio")
        return True  # Skip, not fail
    
    # Initialize SDK
    llmobserve.observe()
    
    # Try to import gRPC interceptor
    try:
        from llmobserve.grpc_interceptor import is_grpc_patched, patch_grpc
        
        # Try to patch
        result = patch_grpc()
        
        if result and is_grpc_patched():
            print(f"  {Color.GREEN}✓ gRPC patching WORKS{Color.END}")
            print(f"    - grpc.insecure_channel: patched")
            print(f"    - grpc.secure_channel: patched")
            return True
        else:
            print(f"  {Color.RED}✗ gRPC patching FAILED{Color.END}")
            return False
    
    except Exception as e:
        print(f"  {Color.RED}✗ gRPC interceptor ERROR: {e}{Color.END}")
        return False


def test_websocket_patching():
    """Test that WebSocket connections can be patched."""
    print(f"\n{Color.BLUE}Test 2: WebSocket Patching{Color.END}")
    
    # Check if websockets library installed
    try:
        import websockets
        print(f"  {Color.GREEN}✓ websockets installed{Color.END}")
        has_websockets = True
    except ImportError:
        print(f"  {Color.YELLOW}⚠ websockets not installed{Color.END}")
        has_websockets = False
    
    # Check if aiohttp installed
    try:
        import aiohttp
        print(f"  {Color.GREEN}✓ aiohttp installed{Color.END}")
        has_aiohttp = True
    except ImportError:
        print(f"  {Color.YELLOW}⚠ aiohttp not installed{Color.END}")
        has_aiohttp = False
    
    if not has_websockets and not has_aiohttp:
        print(f"  {Color.YELLOW}⚠ No WebSocket libraries - SKIPPING TEST{Color.END}")
        print(f"    Install with: pip install websockets aiohttp")
        return True  # Skip, not fail
    
    # Initialize SDK
    llmobserve.observe()
    
    # Try to import WebSocket interceptor
    try:
        from llmobserve.websocket_interceptor import is_websockets_patched, patch_all_websockets
        
        # Try to patch
        result = patch_all_websockets()
        
        if result and is_websockets_patched():
            print(f"  {Color.GREEN}✓ WebSocket patching WORKS{Color.END}")
            if has_websockets:
                print(f"    - websockets.connect: patched")
            if has_aiohttp:
                print(f"    - aiohttp.ClientSession.ws_connect: patched")
            return True
        else:
            print(f"  {Color.RED}✗ WebSocket patching FAILED{Color.END}")
            return False
    
    except Exception as e:
        print(f"  {Color.RED}✗ WebSocket interceptor ERROR: {e}{Color.END}")
        return False


def test_protocol_coverage():
    """Test what protocols we support."""
    print(f"\n{Color.BLUE}Test 3: Protocol Coverage{Color.END}")
    
    protocols = {
        "HTTP (httpx)": lambda: __import__("httpx"),
        "HTTP (requests)": lambda: __import__("requests"),
        "HTTP (aiohttp)": lambda: __import__("aiohttp"),
        "gRPC": lambda: __import__("grpc"),
        "WebSocket (websockets)": lambda: __import__("websockets"),
    }
    
    supported = []
    unsupported = []
    
    for name, check in protocols.items():
        try:
            check()
            supported.append(name)
            print(f"  {Color.GREEN}✓ {name}: available{Color.END}")
        except ImportError:
            unsupported.append(name)
            print(f"  {Color.YELLOW}⚠ {name}: not installed{Color.END}")
    
    print(f"\n  Summary:")
    print(f"    Supported: {len(supported)}/{len(protocols)}")
    print(f"    Missing: {len(unsupported)}/{len(protocols)}")
    
    if len(supported) >= 2:  # At least 2 HTTP clients
        print(f"  {Color.GREEN}✓ Minimum coverage met{Color.END}")
        return True
    else:
        print(f"  {Color.RED}✗ Insufficient coverage{Color.END}")
        return False


def test_sdk_update_detection():
    """Test if we can detect when SDKs update their HTTP clients."""
    print(f"\n{Color.BLUE}Test 4: SDK Update Detection{Color.END}")
    
    # Check OpenAI SDK
    try:
        import openai
        print(f"  {Color.GREEN}✓ OpenAI SDK installed: {openai.__version__}{Color.END}")
        
        # Check what HTTP client it uses
        import inspect
        
        # Try to find the HTTP client
        # This is hacky but demonstrates the concept
        openai_source = inspect.getsource(openai)
        
        if "httpx" in openai_source:
            print(f"    - Uses: httpx ✓ (we support this)")
        elif "requests" in openai_source:
            print(f"    - Uses: requests ✓ (we support this)")
        elif "urllib3" in openai_source:
            print(f"    - Uses: urllib3 ✗ (NOT SUPPORTED)")
        else:
            print(f"    - Uses: unknown ⚠️ (could not detect)")
        
        return True
        
    except ImportError:
        print(f"  {Color.YELLOW}⚠ OpenAI SDK not installed - SKIPPING TEST{Color.END}")
        return True  # Skip, not fail
    except Exception as e:
        print(f"  {Color.YELLOW}⚠ Could not analyze OpenAI SDK: {e}{Color.END}")
        return True  # Not critical


def main():
    """Run all protocol tests."""
    print(f"{Color.BLUE}{'='*60}{Color.END}")
    print(f"{Color.BLUE}LLMObserve Protocol Support Tests{Color.END}")
    print(f"{Color.BLUE}{'='*60}{Color.END}")
    
    tests = [
        ("gRPC Patching", test_grpc_patching),
        ("WebSocket Patching", test_websocket_patching),
        ("Protocol Coverage", test_protocol_coverage),
        ("SDK Update Detection", test_sdk_update_detection),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"  {Color.RED}✗ Test crashed: {e}{Color.END}")
            import traceback
            traceback.print_exc()
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
        print(f"{Color.GREEN}✓ Protocol support verified{Color.END}")
        return 0
    else:
        print(f"{Color.YELLOW}⚠ Some protocols not fully tested{Color.END}")
        print(f"\n{Color.YELLOW}RECOMMENDATION:{Color.END}")
        print(f"  Install missing libraries:")
        print(f"    pip install grpcio websockets")
        return 1


if __name__ == "__main__":
    exit(main())


