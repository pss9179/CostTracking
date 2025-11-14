# Quick Start Guide - Using llmobserve in Your Code

## Prerequisites

1. **Start the services** (if not already running):
   ```bash
   # Terminal 1: Start collector API
   cd collector
   python3 -m uvicorn main:app --port 8000

   # Terminal 2: Start proxy
   cd proxy
   python3 -m uvicorn main:app --port 9000

   # Terminal 3: Start web dashboard (optional)
   cd web
   npm run dev
   ```

2. **Get your API key**:
   - Go to http://localhost:3000/settings
   - Sign in with Clerk
   - Create an API key
   - Copy the key (starts with `llmo_sk_...`)

3. **Set environment variables**:
   ```bash
   export OPENAI_API_KEY='your-openai-key-here'
   export LLMOBSERVE_API_KEY='llmo_sk_your-key-here'
   ```

## Basic Usage

### Option 1: Use the example script

```bash
python3 example_usage.py
```

### Option 2: Use in your own code

```python
import os
import sys
from pathlib import Path

# Add SDK to path
sdk_path = Path(__file__).parent / "sdk" / "python"
sys.path.insert(0, str(sdk_path))

from llmobserve import observe, section, set_run_id, set_customer_id
from openai import OpenAI
import uuid

# 1. Initialize llmobserve
observe(
    collector_url="http://localhost:8000",
    proxy_url="http://localhost:9000",
    api_key=os.getenv("LLMOBSERVE_API_KEY"),
    tenant_id="my_app"  # Your app/tenant identifier
)

# 2. Configure OpenAI client to use proxy
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="http://localhost:9000/v1"  # IMPORTANT: Route through proxy
)

# 3. Set run ID and customer ID (optional)
set_run_id(str(uuid.uuid4()))
set_customer_id("customer_123")

# 4. Make API calls - they're tracked automatically!
with section("my_section"):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.choices[0].message.content)
```

## Key Points

1. **Always set `base_url`** when creating the OpenAI client:
   ```python
   client = OpenAI(api_key=..., base_url="http://localhost:9000/v1")
   ```

2. **Use `section()`** to organize your calls:
   ```python
   with section("user_query"):
       # API calls here
   ```

3. **Set `run_id`** to group related calls:
   ```python
   set_run_id(str(uuid.uuid4()))
   ```

4. **View costs** at http://localhost:3000

## What Gets Tracked

- ✅ API provider (OpenAI, Anthropic, etc.)
- ✅ Model name (gpt-4o, gpt-4o-mini, etc.)
- ✅ Input/output tokens
- ✅ Cost in USD (calculated automatically)
- ✅ Latency
- ✅ Status (success/error)
- ✅ Section/context

## Troubleshooting

**"Connection error" when making API calls:**
- Make sure proxy is running: `curl http://localhost:9000/health`
- Make sure you set `base_url="http://localhost:9000/v1"`

**"Invalid API key" warnings:**
- Check your API key at http://localhost:3000/settings
- Make sure `LLMOBSERVE_API_KEY` environment variable is set

**No data in dashboard:**
- Wait a few seconds for events to flush
- Check tenant_id matches (default is "my_app" in example)
- Make sure collector API is running

## Next Steps

- Track multiple APIs (not just OpenAI)
- Use different sections for different parts of your app
- Set customer_id for multi-tenant tracking
- View costs by provider, model, section, customer

