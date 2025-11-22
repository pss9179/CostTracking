"""
Test script specifically for VAPI API calls to show multiple providers in the graph.
"""
import os
import sys
import requests
import time

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sdk', 'python'))

from llmobserve import observe, section, set_customer_id

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize LLMObserve (this automatically patches HTTP clients)
print("🚀 Initializing LLMObserve...")
observe(
    collector_url="http://localhost:8000",
    api_key="llmo_sk_f27c7f7f73a40172b8bf9d226ced22255b5036dccc8050d2"
)
print("✅ LLMObserve initialized (HTTP tracking enabled)!\n")

vapi_private_key = os.getenv("VAPI_PRIVATE_KEY")
vapi_assistant_id = os.getenv("VAPI_ASSISTANT_ID")
vapi_phone_number_id = os.getenv("VAPI_PHONE_NUMBER_ID")

if not vapi_private_key:
    print("❌ VAPI_PRIVATE_KEY not found")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {vapi_private_key}",
    "Content-Type": "application/json"
}

print("=" * 70)
print("VAPI TEST 1: List Assistants (Multiple Calls)")
print("=" * 70)

set_customer_id("customer_vapi_001")
print("👤 Customer: customer_vapi_001\n")

with section("agent:vapi_manager"):
    for i in range(5):
        try:
            print(f"  📞 VAPI API Call {i+1}/5: Listing assistants...")
            response = requests.get(
                "https://api.vapi.ai/assistant",
                headers=headers
            )
            
            if response.status_code == 200:
                assistants = response.json()
                print(f"  ✅ Success: {len(assistants)} assistants found")
            else:
                print(f"  ⚠️  Status: {response.status_code}")
            
            time.sleep(0.5)  # Small delay between calls
        except Exception as e:
            print(f"  ❌ Error: {e}")
    print()

print("=" * 70)
print("VAPI TEST 2: Get Assistant Details (Multiple Customers)")
print("=" * 70)

if vapi_assistant_id:
    customers = ["customer_vapi_002", "customer_vapi_003", "customer_vapi_004"]
    
    for i, customer in enumerate(customers, 1):
        set_customer_id(customer)
        print(f"👤 Customer: {customer}\n")
        
        with section(f"agent:assistant_viewer_{i}"):
            try:
                print(f"  📞 Fetching assistant details...")
                response = requests.get(
                    f"https://api.vapi.ai/assistant/{vapi_assistant_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    assistant = response.json()
                    print(f"  ✅ Success: Got assistant '{assistant.get('name', 'Unknown')}'")
                else:
                    print(f"  ⚠️  Status: {response.status_code}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
        print()
else:
    print("  ⚠️  VAPI_ASSISTANT_ID not set, skipping\n")

print("=" * 70)
print("VAPI TEST 3: Phone Numbers")
print("=" * 70)

set_customer_id("customer_vapi_005")
print("👤 Customer: customer_vapi_005\n")

with section("agent:phone_manager"):
    for i in range(3):
        try:
            print(f"  📞 VAPI API Call {i+1}/3: Listing phone numbers...")
            response = requests.get(
                "https://api.vapi.ai/phone-number",
                headers=headers
            )
            
            if response.status_code == 200:
                phone_numbers = response.json()
                print(f"  ✅ Success: {len(phone_numbers)} phone numbers found")
            else:
                print(f"  ⚠️  Status: {response.status_code}")
            
            time.sleep(0.3)
        except Exception as e:
            print(f"  ❌ Error: {e}")
    print()

print("=" * 70)
print("VAPI TEST 4: Rapid Fire Calls")
print("=" * 70)

set_customer_id("customer_vapi_heavy")
print("👤 Customer: customer_vapi_heavy (10 rapid calls)\n")

with section("agent:vapi_stress_test"):
    success_count = 0
    for i in range(10):
        try:
            response = requests.get(
                "https://api.vapi.ai/assistant",
                headers=headers
            )
            
            if response.status_code == 200:
                success_count += 1
                if i % 3 == 0:
                    print(f"  ✅ Progress: {success_count}/10 calls...")
        except Exception as e:
            print(f"  ❌ Error on call {i+1}: {e}")
    
    print(f"  ✅ Completed {success_count}/10 calls\n")

print("=" * 70)
print("✅ ALL VAPI TESTS COMPLETED!")
print("=" * 70)
print(f"""
📊 Summary:

Total VAPI API Calls: ~21 calls
- 5 calls from customer_vapi_001
- 3 calls from customer_vapi_002, 003, 004
- 3 calls from customer_vapi_005
- 10 calls from customer_vapi_heavy

Agents Created:
- agent:vapi_manager
- agent:assistant_viewer_1, 2, 3
- agent:phone_manager
- agent:vapi_stress_test

🎯 Go to http://localhost:3000/dashboard to see:
   1. VAPI provider in the graph (separate from OpenAI)
   2. Multiple colored bars for different providers
   3. VAPI costs tracked separately
   4. Customer breakdown showing VAPI usage
""")

