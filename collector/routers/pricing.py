"""
Pricing router - manage pricing registry.
"""
from typing import Dict, Any
from fastapi import APIRouter
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from pricing import load_pricing_registry, save_pricing_registry

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.get("/")
def get_pricing() -> Dict[str, Any]:
    """Get current pricing registry."""
    return load_pricing_registry()


@router.put("/")
def update_pricing(registry: Dict[str, Any]) -> Dict[str, str]:
    """
    Update pricing registry.
    
    Accepts full registry JSON to replace existing pricing.
    """
    save_pricing_registry(registry)
    return {"status": "success", "message": "Pricing registry updated"}

