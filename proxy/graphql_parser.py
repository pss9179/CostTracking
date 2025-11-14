"""
GraphQL Request Parser for LLMObserve Proxy

Parses GraphQL queries/mutations from HTTP requests to extract:
- Operation type (query, mutation, subscription)
- Operation name
- Query complexity estimation
- Field count
- Variables

Similar to how Kong handles GraphQL requests transparently.
"""
import json
import re
from typing import Dict, Optional, Any, Tuple
import logging

logger = logging.getLogger("llmobserve.proxy.graphql")


def is_graphql_request(content_type: Optional[str], request_body: bytes, request_json: Optional[Dict] = None) -> bool:
    """
    Detect if a request is a GraphQL request.
    
    Args:
        content_type: Content-Type header value
        request_body: Raw request body bytes
        request_json: Parsed JSON request body (if available)
    
    Returns:
        True if this appears to be a GraphQL request
    """
    if not content_type:
        return False
    
    content_type_lower = content_type.lower()
    
    # Check Content-Type headers
    graphql_content_types = [
        "application/graphql",
        "application/json",  # GraphQL often uses JSON
    ]
    
    if not any(ct in content_type_lower for ct in graphql_content_types):
        return False
    
    # Check request body for GraphQL patterns
    try:
        # Try JSON format first: {"query": "...", "variables": {...}}
        if request_json:
            if "query" in request_json or "mutation" in request_json or "subscription" in request_json:
                return True
        
        # Try raw body parsing
        if request_body:
            body_str = request_body.decode('utf-8', errors='ignore')
            
            # Check for GraphQL keywords
            graphql_keywords = ["query", "mutation", "subscription", "__typename"]
            if any(keyword in body_str for keyword in graphql_keywords):
                # Verify it looks like GraphQL (has braces, not just random text)
                if "{" in body_str and ("query" in body_str or "mutation" in body_str or "subscription" in body_str):
                    return True
        
        # Check JSON format
        if request_body:
            try:
                parsed = json.loads(request_body.decode('utf-8'))
                if isinstance(parsed, dict) and ("query" in parsed or "mutation" in parsed or "subscription" in parsed):
                    return True
            except:
                pass
    except Exception as e:
        logger.debug(f"[graphql] Error detecting GraphQL request: {e}")
        return False
    
    return False


def parse_graphql_request(request_body: bytes, request_json: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Parse GraphQL request to extract operation details.
    
    Args:
        request_body: Raw request body bytes
        request_json: Parsed JSON request body (if available)
    
    Returns:
        Dict with keys:
        - operation_type: "query", "mutation", "subscription", or None
        - operation_name: Name of the operation (if named)
        - query: The GraphQL query string
        - variables: Variables dict (if present)
        - field_count: Estimated number of fields
        - complexity_score: Simple complexity estimation
    """
    result = {
        "operation_type": None,
        "operation_name": None,
        "query": None,
        "variables": None,
        "field_count": 0,
        "complexity_score": 0,
    }
    
    try:
        query_string = None
        
        # Try to get query from JSON format
        if request_json:
            query_string = request_json.get("query") or request_json.get("mutation") or request_json.get("subscription")
            result["variables"] = request_json.get("variables")
        
        # If not in JSON, try parsing raw body
        if not query_string and request_body:
            try:
                body_str = request_body.decode('utf-8', errors='ignore')
                
                # Try JSON parsing
                try:
                    parsed = json.loads(body_str)
                    if isinstance(parsed, dict):
                        query_string = parsed.get("query") or parsed.get("mutation") or parsed.get("subscription")
                        result["variables"] = parsed.get("variables")
                except:
                    # Might be raw GraphQL string
                    query_string = body_str.strip()
            except:
                pass
        
        if not query_string:
            return result
        
        result["query"] = query_string
        
        # Parse operation type and name
        operation_match = re.search(r'\b(query|mutation|subscription)\s+(\w+)?', query_string, re.IGNORECASE)
        if operation_match:
            result["operation_type"] = operation_match.group(1).lower()
            if operation_match.group(2):
                result["operation_name"] = operation_match.group(2)
        
        # Count fields (simple estimation)
        # Count opening braces and field patterns
        field_pattern = r'\w+\s*\{'
        fields = re.findall(field_pattern, query_string)
        result["field_count"] = len(fields)
        
        # Simple complexity score based on:
        # - Field count
        # - Nested depth (count of nested braces)
        # - Variables count
        complexity = result["field_count"]
        
        # Add depth complexity (nested queries)
        depth = 0
        max_depth = 0
        for char in query_string:
            if char == '{':
                depth += 1
                max_depth = max(max_depth, depth)
            elif char == '}':
                depth -= 1
        
        complexity += max_depth * 2
        
        # Add variables complexity
        if result["variables"]:
            if isinstance(result["variables"], dict):
                complexity += len(result["variables"])
        
        result["complexity_score"] = complexity
        
    except Exception as e:
        logger.debug(f"[graphql] Error parsing GraphQL request: {e}")
    
    return result


def extract_graphql_endpoint(query: Optional[str], url: str) -> str:
    """
    Extract meaningful endpoint name from GraphQL query.
    
    Args:
        query: GraphQL query string
        url: Request URL
    
    Returns:
        Endpoint name (e.g., "getUser", "createPost", "graphql.query")
    """
    if not query:
        # Fallback to URL path
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        return path or "graphql"
    
    try:
        # Try to extract operation name
        operation_match = re.search(r'\b(query|mutation|subscription)\s+(\w+)', query, re.IGNORECASE)
        if operation_match:
            operation_type = operation_match.group(1).lower()
            operation_name = operation_match.group(2)
            return f"graphql.{operation_type}.{operation_name}"
        
        # Fallback: extract first field name
        field_match = re.search(r'\{\s*(\w+)', query)
        if field_match:
            return f"graphql.{field_match.group(1)}"
    except:
        pass
    
    # Final fallback
    return "graphql.query"


def parse_graphql_response(response_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse GraphQL response to extract usage information.
    
    Args:
        response_body: Parsed JSON response
    
    Returns:
        Dict with usage information:
        - data_size: Size of data returned
        - error_count: Number of errors
        - field_count: Number of fields in response
    """
    result = {
        "data_size": 0,
        "error_count": 0,
        "field_count": 0,
    }
    
    try:
        # Count errors
        if "errors" in response_body:
            errors = response_body["errors"]
            if isinstance(errors, list):
                result["error_count"] = len(errors)
        
        # Estimate data size
        if "data" in response_body:
            data = response_body["data"]
            if isinstance(data, dict):
                result["field_count"] = len(data)
                # Rough size estimation (JSON string length)
                result["data_size"] = len(json.dumps(data))
        
    except Exception as e:
        logger.debug(f"[graphql] Error parsing GraphQL response: {e}")
    
    return result

