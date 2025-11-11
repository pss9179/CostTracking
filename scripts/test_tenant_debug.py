"""
Debug script to test tenant_id context.
"""

import os
import sys
import time
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from llmobserve import observe, set_tenant_id, set_customer_id, get_tenant_id, get_customer_id
from llmobserve import context, config

print("Testing tenant_id context...")

# Initialize
observe(collector_url="http://localhost:8000")

# Set tenant and customer
print(f"\n1. Before setting: tenant_id={get_tenant_id()}, customer_id={get_customer_id()}")

set_tenant_id("test-tenant")
set_customer_id("test-customer")

print(f"2. After setting: tenant_id={get_tenant_id()}, customer_id={get_customer_id()}")

# Check what config.get_tenant_id returns
print(f"3. config.get_tenant_id()={config.get_tenant_id()}")
print(f"4. config.get_customer_id()={config.get_customer_id()}")

# Try OpenAI call if available
try:
    from openai import OpenAI
    OPENAI_KEY = os.getenv("OPENAI_API_KEY")
    
    if OPENAI_KEY:
        print("\n5. Making OpenAI call...")
        client = OpenAI(api_key=OPENAI_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10
        )
        print(f"6. Response: {response.choices[0].message.content[:50]}")
        print("7. Waiting for buffer flush...")
        time.sleep(2)
        print("8. Done")
    else:
        print("\n5. No OpenAI key found, skipping LLM call")
except ImportError:
    print("\n5. OpenAI SDK not installed")

print("\nCheck database:")
print("sqlite3 /Users/pranavsrigiriraju/CostTracking/collector/collector.db \"SELECT run_id, tenant_id, customer_id, section FROM trace_events WHERE tenant_id = 'test-tenant';\"")

