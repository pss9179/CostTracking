"""
gRPC Cost Configuration

Allows users to configure costs for gRPC APIs that don't implement ORCA.
Costs can be set per service, method, or globally.
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger("llmobserve")

# Global gRPC cost registry
# Format: {
#   "service_name": {
#     "method_name": cost_per_call,
#     "*": default_cost  # Wildcard for all methods
#   },
#   "*": default_cost  # Global default
# }
_grpc_cost_registry: Dict[str, Dict[str, float]] = {}


def configure_grpc_cost(
    service: Optional[str] = None,
    method: Optional[str] = None,
    cost_per_call: float = 0.0
) -> None:
    """
    Configure cost for a gRPC method or service.
    
    Args:
        service: Service name (e.g., "pinecone", "my_service"). 
                If None, applies to all services.
        method: Method name (e.g., "Query", "Upsert").
                If None, applies to all methods in the service.
                Use "*" for wildcard.
        cost_per_call: Cost in USD per call
    
    Examples:
        # Set cost for specific method
        configure_grpc_cost("pinecone", "Query", 0.000016)
        
        # Set default cost for all methods in a service
        configure_grpc_cost("my_service", "*", 0.001)
        
        # Set global default cost for all gRPC calls
        configure_grpc_cost("*", "*", 0.0001)
        
        # Set cost for all methods in a service (same as above)
        configure_grpc_cost("my_service", cost_per_call=0.001)
    """
    global _grpc_cost_registry
    
    if service is None:
        service = "*"
    if method is None:
        method = "*"
    
    if service not in _grpc_cost_registry:
        _grpc_cost_registry[service] = {}
    
    _grpc_cost_registry[service][method] = cost_per_call
    
    logger.info(
        f"[llmobserve] Configured gRPC cost: {service}/{method} = ${cost_per_call:.6f} per call"
    )


def get_grpc_cost(service: str, method: str) -> float:
    """
    Get configured cost for a gRPC method.
    
    Checks in order:
    1. Exact service + method match
    2. Service wildcard + method match
    3. Service + method wildcard
    4. Global wildcard
    
    Args:
        service: Service name (e.g., "pinecone")
        method: Method name (e.g., "Query")
    
    Returns:
        Cost in USD per call, or 0.0 if not configured
    """
    # Try exact match
    if service in _grpc_cost_registry:
        if method in _grpc_cost_registry[service]:
            return _grpc_cost_registry[service][method]
        # Try method wildcard
        if "*" in _grpc_cost_registry[service]:
            return _grpc_cost_registry[service]["*"]
    
    # Try service wildcard
    if "*" in _grpc_cost_registry:
        if method in _grpc_cost_registry["*"]:
            return _grpc_cost_registry["*"][method]
        # Try both wildcards
        if "*" in _grpc_cost_registry["*"]:
            return _grpc_cost_registry["*"]["*"]
    
    return 0.0


def parse_grpc_method(method_path: str) -> tuple[str, str]:
    """
    Parse gRPC method path to extract service and method names.
    
    Args:
        method_path: Full gRPC method path (e.g., "/pinecone.Query/Query")
    
    Returns:
        Tuple of (service_name, method_name)
    """
    if not method_path or not method_path.startswith("/"):
        return ("unknown", "unknown")
    
    # Remove leading "/"
    path = method_path[1:]
    
    # Split by "/" - format is usually "/Service/Method" or "/Service.Service/Method"
    parts = path.split("/")
    if len(parts) < 2:
        return ("unknown", path)
    
    service_part = parts[0]
    method_name = parts[1]
    
    # Extract service name (e.g., "pinecone.Query" -> "pinecone")
    if "." in service_part:
        service_name = service_part.split(".")[0].lower()
    else:
        service_name = service_part.lower()
    
    return (service_name, method_name)


def clear_grpc_costs() -> None:
    """Clear all configured gRPC costs."""
    global _grpc_cost_registry
    _grpc_cost_registry = {}
    logger.info("[llmobserve] Cleared all gRPC cost configurations")

