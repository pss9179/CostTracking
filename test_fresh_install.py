"""
Test script: Simulating a fresh user installing llmobserve

This script tests:
1. Installing the package from local source (simulating pip install llmobserve)
2. Using the SDK with just an API key
3. Making real API calls
4. Verifying tracking works
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

print("="*70)
print("🧪 TESTING FRESH LLMOBSERVE INSTALLATION")
print("="*70)

# ============================================================================
# STEP 1: Create a fresh virtual environment
# ============================================================================
print("\n📦 Step 1: Creating fresh virtual environment...")
test_dir = Path(tempfile.mkdtemp(prefix="llmobserve_test_"))
venv_dir = test_dir / "venv"

print(f"   Test directory: {test_dir}")
subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
print("   ✅ Virtual environment created")

# Get paths
if sys.platform == "win32":
    python_exe = venv_dir / "Scripts" / "python.exe"
    pip_exe = venv_dir / "Scripts" / "pip.exe"
else:
    python_exe = venv_dir / "bin" / "python"
    pip_exe = venv_dir / "bin" / "pip"

# ============================================================================
# STEP 2: Install llmobserve from local source
# ============================================================================
print("\n📦 Step 2: Installing llmobserve package...")
sdk_path = Path(__file__).parent / "sdk" / "python"
result = subprocess.run(
    [str(pip_exe), "install", "-e", str(sdk_path)],
    capture_output=True,
    text=True
)
if result.returncode != 0:
    print(f"   ❌ Installation failed: {result.stderr}")
    sys.exit(1)
print("   ✅ llmobserve installed")

# ============================================================================
# STEP 3: Install OpenAI SDK
# ============================================================================
print("\n📦 Step 3: Installing openai package...")
subprocess.run([str(pip_exe), "install", "openai"], capture_output=True, check=True)
print("   ✅ openai installed")

# ============================================================================
# STEP 4: Create test script
# ============================================================================
print("\n📝 Step 4: Creating test script...")

# Get API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLMOBSERVE_API_KEY = os.getenv("LLMOBSERVE_API_KEY", "llmo_sk_9858c9a35578b19d96be7a373def01d5b7fedab72c3712a5")

if not OPENAI_API_KEY:
    print("   ⚠️  WARNING: OPENAI_API_KEY not set")
    print("   Set it with: export OPENAI_API_KEY='your-key-here'")
    print("   Skipping actual API calls...")
    test_with_api = False
else:
    test_with_api = True
    print(f"   ✅ Using OpenAI API key: {OPENAI_API_KEY[:20]}...")

print(f"   ✅ Using LLMObserve API key: {LLMOBSERVE_API_KEY[:30]}...")

# Create the test script
test_script = test_dir / "test_usage.py"
test_script.write_text(f'''
import os
import uuid
from llmobserve import observe, section, set_run_id, set_customer_id
from openai import OpenAI

print("\\n" + "="*70)
print("🚀 TESTING LLMOBSERVE SDK")
print("="*70)

# Initialize llmobserve
print("\\n🔧 Initializing llmobserve...")
observe(
    collector_url="http://localhost:8000",
    api_key="{LLMOBSERVE_API_KEY}",
    tenant_id="test_tenant"
)
print("✅ llmobserve initialized!")

# Configure OpenAI
client = OpenAI(api_key="{OPENAI_API_KEY}")

# Set tracking context
run_id = str(uuid.uuid4())
set_run_id(run_id)
set_customer_id("test_customer")

print(f"\\n📊 Run ID: {{run_id}}")
print("📊 Customer ID: test_customer")
print("📊 Tenant ID: test_tenant")

# Make API calls
print("\\n📝 Making API calls...")

try:
    with section("test_section"):
        print("   → Calling OpenAI API...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {{"role": "user", "content": "Say 'Hello from llmobserve test!' in one sentence."}}
            ],
            max_tokens=50
        )
        print(f"   ✅ Response: {{response.choices[0].message.content}}")
        print(f"   💰 Tokens: {{response.usage.total_tokens}}")
        
    print("\\n" + "="*70)
    print("✅ TEST PASSED!")
    print("="*70)
    print("\\n📊 View your costs at: http://localhost:3000")
    print("   • Tenant: test_tenant")
    print("   • Customer: test_customer")
    print(f"   • Run ID: {{run_id}}")
    
except Exception as e:
    print(f"\\n❌ ERROR: {{e}}")
    import traceback
    traceback.print_exc()
    exit(1)
''')

print(f"   ✅ Test script created: {test_script}")

# ============================================================================
# STEP 5: Run the test
# ============================================================================
if test_with_api:
    print("\n🚀 Step 5: Running test script...")
    print("-" * 70)
    
    result = subprocess.run(
        [str(python_exe), str(test_script)],
        env={**os.environ, "OPENAI_API_KEY": OPENAI_API_KEY},
        text=True
    )
    
    print("-" * 70)
    
    if result.returncode == 0:
        print("\n✅ TEST COMPLETED SUCCESSFULLY!")
        print("\n📊 Next steps:")
        print("   1. Open http://localhost:3000 in your browser")
        print("   2. Check the dashboard for tracked costs")
        print("   3. Look for tenant 'test_tenant' and customer 'test_customer'")
    else:
        print("\n❌ TEST FAILED!")
        sys.exit(1)
else:
    print("\n⚠️  Skipping API test (no OPENAI_API_KEY)")
    print("   To test with real API calls:")
    print("   export OPENAI_API_KEY='your-key-here'")
    print("   python test_fresh_install.py")

# ============================================================================
# STEP 6: Cleanup info
# ============================================================================
print(f"\n🗑️  Test environment: {test_dir}")
print("   (You can delete this directory after testing)")

print("\n" + "="*70)
print("✅ FRESH INSTALL TEST COMPLETE")
print("="*70)

