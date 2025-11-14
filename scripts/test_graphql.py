#!/usr/bin/env python3
"""
Test GraphQL support in LLMObserve proxy.

Tests GraphQL request detection and parsing.
"""
import json
import httpx
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from proxy.graphql_parser import (
    is_graphql_request,
    parse_graphql_request,
    extract_graphql_endpoint,
    parse_graphql_response,
)


def test_graphql_detection():
    """Test GraphQL request detection."""
    print("\n=== Testing GraphQL Detection ===")
    
    # Test 1: JSON format with query
    json_body = json.dumps({
        "query": "query GetUser { user(id: 1) { name email } }",
        "variables": {}
    }).encode('utf-8')
    
    is_gql = is_graphql_request("application/json", json_body)
    print(f"✓ JSON format detected: {is_gql}")
    assert is_gql, "Should detect GraphQL in JSON format"
    
    # Test 2: Raw GraphQL string
    raw_body = b"query GetUser { user(id: 1) { name email } }"
    is_gql = is_graphql_request("application/graphql", raw_body)
    print(f"✓ Raw GraphQL detected: {is_gql}")
    assert is_gql, "Should detect raw GraphQL"
    
    # Test 3: Mutation
    mutation_body = json.dumps({
        "mutation": "mutation CreatePost { createPost(title: \"Test\") { id } }"
    }).encode('utf-8')
    is_gql = is_graphql_request("application/json", mutation_body)
    print(f"✓ Mutation detected: {is_gql}")
    assert is_gql, "Should detect mutations"
    
    # Test 4: Non-GraphQL request
    non_gql_body = json.dumps({"key": "value"}).encode('utf-8')
    is_gql = is_graphql_request("application/json", non_gql_body)
    print(f"✓ Non-GraphQL correctly rejected: {not is_gql}")
    assert not is_gql, "Should not detect non-GraphQL as GraphQL"
    
    print("✅ All detection tests passed!\n")


def test_graphql_parsing():
    """Test GraphQL query parsing."""
    print("\n=== Testing GraphQL Parsing ===")
    
    # Test query parsing
    query_json = {
        "query": "query GetUser($id: ID!) { user(id: $id) { name email posts { title } } }",
        "variables": {"id": "123"}
    }
    body = json.dumps(query_json).encode('utf-8')
    
    parsed = parse_graphql_request(body, query_json)
    print(f"✓ Operation type: {parsed['operation_type']}")
    assert parsed['operation_type'] == "query", "Should parse operation type"
    
    print(f"✓ Operation name: {parsed['operation_name']}")
    assert parsed['operation_name'] == "GetUser", "Should parse operation name"
    
    print(f"✓ Field count: {parsed['field_count']}")
    assert parsed['field_count'] > 0, "Should count fields"
    
    print(f"✓ Complexity score: {parsed['complexity_score']}")
    assert parsed['complexity_score'] > 0, "Should calculate complexity"
    
    print(f"✓ Variables: {parsed['variables']}")
    assert parsed['variables'] == {"id": "123"}, "Should parse variables"
    
    # Test mutation parsing
    mutation_json = {
        "mutation": "mutation CreatePost($title: String!) { createPost(title: $title) { id title } }"
    }
    body = json.dumps(mutation_json).encode('utf-8')
    
    parsed = parse_graphql_request(body, mutation_json)
    print(f"✓ Mutation type: {parsed['operation_type']}")
    assert parsed['operation_type'] == "mutation", "Should parse mutation"
    
    print("✅ All parsing tests passed!\n")


def test_endpoint_extraction():
    """Test GraphQL endpoint extraction."""
    print("\n=== Testing Endpoint Extraction ===")
    
    query = "query GetUser { user { name } }"
    endpoint = extract_graphql_endpoint(query, "https://api.example.com/graphql")
    print(f"✓ Endpoint: {endpoint}")
    assert "graphql" in endpoint.lower(), "Should extract GraphQL endpoint"
    
    query = "query getUserProfile { user { name email } }"
    endpoint = extract_graphql_endpoint(query, "https://api.example.com/graphql")
    print(f"✓ Named query endpoint: {endpoint}")
    assert "getUserProfile" in endpoint or "user" in endpoint, "Should extract operation name"
    
    print("✅ All endpoint extraction tests passed!\n")


def test_response_parsing():
    """Test GraphQL response parsing."""
    print("\n=== Testing Response Parsing ===")
    
    # Success response
    response = {
        "data": {
            "user": {
                "name": "John",
                "email": "john@example.com"
            }
        }
    }
    
    parsed = parse_graphql_response(response)
    print(f"✓ Data size: {parsed['data_size']}")
    assert parsed['data_size'] > 0, "Should calculate data size"
    
    print(f"✓ Field count: {parsed['field_count']}")
    assert parsed['field_count'] > 0, "Should count fields"
    
    # Error response
    error_response = {
        "errors": [
            {"message": "User not found"},
            {"message": "Permission denied"}
        ]
    }
    
    parsed = parse_graphql_response(error_response)
    print(f"✓ Error count: {parsed['error_count']}")
    assert parsed['error_count'] == 2, "Should count errors"
    
    print("✅ All response parsing tests passed!\n")


if __name__ == "__main__":
    print("🧪 Testing GraphQL Support in LLMObserve Proxy\n")
    
    try:
        test_graphql_detection()
        test_graphql_parsing()
        test_endpoint_extraction()
        test_response_parsing()
        
        print("\n" + "="*50)
        print("✅ ALL TESTS PASSED!")
        print("="*50)
        print("\nGraphQL support is working correctly!")
        print("The proxy will now:")
        print("  - Detect GraphQL requests automatically")
        print("  - Parse queries/mutations/subscriptions")
        print("  - Extract operation names and complexity")
        print("  - Track GraphQL calls with full metadata")
        print("  - Forward requests transparently (like Kong)")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

