# LLM Observe - Complete Architecture Overview

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER'S APPLICATION CODE                      │
│  (Python script, FastAPI app, Django app, etc.)                 │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        │ 1. User calls: observe(collector_url, api_key)
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SDK (llmobserve)                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  observe.py                                               │  │
│  │  - Configures SDK                                          │  │
│  │  - Calls patch_openai() and patch_pinecone()              │  │
│  │  - Starts flush timer                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                        │                                          │
│                        ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  MONKEY-PATCHING LAYER                                     │  │
│  │  ┌──────────────────┐  ┌──────────────────┐              │  │
│  │  │ openai_patch.py  │  │ pinecone_patch.py │              │  │
│  │  │                  │  │                  │              │  │
│  │  │ Patches:         │  │ Patches:         │              │  │
│  │  │ - chat.create() │  │ - Index.query()  │              │  │
│  │  │ - embeddings    │  │ - Index.upsert()  │              │  │
│  │  │ - audio.*        │  │ - inference.*    │              │  │
│  │  │ - images.*       │  │                  │              │  │
│  │  └──────────────────┘  └──────────────────┘              │  │
│  │         │                          │                        │  │
│  │         └──────────┬───────────────┘                        │  │
│  │                    ▼                                        │  │
│  │  ┌──────────────────────────────────────────┐             │  │
│  │  │  robustness.py                            │             │  │
│  │  │  - safe_patch() wrapper                    │             │  │
│  │  │  - Version checks                          │             │  │
│  │  │  - Conflict detection                      │             │  │
│  │  └──────────────────────────────────────────┘             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                        │                                          │
│                        ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  INSTRUMENTATION LAYER                                     │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │  │
│  │  │ context.py   │  │ buffer.py    │  │ pricing.py   │    │  │
│  │  │              │  │              │  │              │    │  │
│  │  │ ContextVars: │  │ Thread-safe  │  │ Cost calc    │    │  │
│  │  │ - run_id     │  │ event buffer │  │ from tokens  │    │  │
│  │  │ - customer_id│  │ - Auto-flush │  │              │    │  │
│  │  │ - section    │  │ - Timer      │  │              │    │  │
│  │  │ - span_id    │  │              │  │              │    │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                        │                                          │
│                        ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  transport.py                                               │  │
│  │  - HTTP POST to /events                                    │  │
│  │  - Batch sending (500ms default)                            │  │
│  │  - Silent failure (doesn't break app)                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        │ 2. HTTP POST /events (batch)
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COLLECTOR (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  routers/events.py                                         │  │
│  │  - Receives batch of events                                │  │
│  │  - Validates API key (auth.py)                             │  │
│  │  - Computes cost if missing                                 │  │
│  │  - Stores in database                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                        │                                          │
│                        ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  db.py + models.py                                         │  │
│  │  - SQLModel ORM                                            │  │
│  │  - SQLite (dev) or PostgreSQL (prod)                      │  │
│  │  - trace_events table                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                        │                                          │
│                        ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  routers/runs.py, insights.py, dashboard.py               │  │
│  │  - Query endpoints for frontend                             │  │
│  │  - Aggregations, filtering                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        │ 3. HTTP GET /runs, /insights, etc.
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                            │
│  - Dashboard, Runs, Costs, Agents pages                         │
│  - Recharts for visualizations                                  │
│  - Customer filtering, hierarchical traces                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 How Monkey-Patching Works

### Step-by-Step Patching Process

#### 1. **Initialization** (`observe()`)
```python
# User calls:
observe(collector_url="http://localhost:8000", api_key="llmo_sk_...")

# This triggers:
1. config.configure() - Stores collector_url, api_key
2. patch_openai() - Patches OpenAI SDK
3. patch_pinecone() - Patches Pinecone SDK
4. buffer.start_flush_timer() - Starts background thread
```

#### 2. **OpenAI Patching** (`openai_patch.py`)

**What Gets Patched:**
- `resources.chat.Completions.create` → Wrapped with tracking
- `resources.Completions.create` → Wrapped with tracking
- `resources.Embeddings.create` → Wrapped with tracking
- `resources.audio.*.create` → Wrapped with tracking
- `resources.Images.generate` → Wrapped with tracking
- ... (15+ endpoints total)

**How It Works:**
```python
# BEFORE PATCHING:
client = OpenAI()
response = client.chat.completions.create(...)  # Direct OpenAI call

# AFTER PATCHING:
client = OpenAI()
response = client.chat.completions.create(...)  # Goes through wrapper!

# The wrapper (_patch_method):
def sync_wrapper(*args, **kwargs):
    start_time = time.time()
    model = kwargs.get("model")
    
    try:
        # Call original OpenAI method
        response = original_method(*args, **kwargs)
        
        # Track the call
        _track_openai_call(
            method_name="chat.completions.create",
            model=model,
            start_time=start_time,
            response=response
        )
        
        return response
    except Exception as e:
        # Track error
        _track_openai_call(..., error=e)
        raise
```

**Key Mechanism:**
1. `getattr(resources.chat.Completions, "create")` - Gets original method
2. `_patch_method()` - Creates wrapper function
3. `setattr(resources.chat.Completions, "create", wrapped_method)` - **Replaces** the method
4. `wrapped_method._llmobserve_patched = True` - Marks as patched (idempotency)

#### 3. **Pinecone Patching** (`pinecone_patch.py`)

**What Gets Patched:**
- `Index.query()` - Read units
- `Index.upsert()` - Write units
- `Index.delete()` - Write units
- `Index.update()` - Write units
- `Index.fetch()` - Read units
- `Index.list()` - Read units
- `Index.describe_index_stats()` - Read units
- `inference.embed()` - Embedding API
- `inference.rerank()` - Reranking API

**How It Works:**
```python
# BEFORE:
index = pc.Index("my-index")
results = index.query(...)  # Direct Pinecone call

# AFTER:
index = pc.Index("my-index")
results = index.query(...)  # Goes through wrapper!

# The wrapper:
def patched_query(self, *args, **kwargs):
    start_time = time.time()
    try:
        result = original_query(self, *args, **kwargs)
        return result
    except Exception as e:
        error = e
        raise
    finally:
        _track_pinecone_call("query", start_time, error)
```

---

## 📊 How Instrumentation Works

### 1. **Context Management** (`context.py`)

**ContextVars (Async-Safe):**
```python
_run_id_var = ContextVar("run_id")           # Groups events into runs
_customer_id_var = ContextVar("customer_id") # Tracks end-users
_section_stack_var = ContextVar("section_stack") # Hierarchical sections
```

**How It Works:**
- Each async task/thread gets its own context
- `section("agent:researcher")` pushes to stack
- `span_id` and `parent_span_id` generated automatically
- When API call happens, it reads current context

**Example:**
```python
with section("agent:researcher"):
    with section("tool:web_search"):
        # OpenAI call happens here
        response = client.embeddings.create(...)
        # Event gets:
        # - section_path: "agent:researcher/tool:web_search"
        # - span_id: "uuid-123"
        # - parent_span_id: "uuid-456" (from agent:researcher)
```

### 2. **Event Buffering** (`buffer.py`)

**Thread-Safe Buffer:**
```python
_buffer: List[TraceEvent] = []  # In-memory list
_buffer_lock = threading.Lock()  # Thread lock
```

**How It Works:**
1. `add_event(event)` - Adds to buffer (thread-safe)
2. `start_flush_timer()` - Starts background thread
3. Every 500ms (default), `flush_events()` is called
4. `get_and_clear_buffer()` - Gets all events, clears buffer
5. Events sent via HTTP POST to `/events`

**Why Buffer?**
- Reduces HTTP overhead (batch sending)
- Non-blocking (doesn't slow down user's code)
- Handles network failures gracefully

### 3. **Cost Calculation** (`pricing.py`)

**Client-Side Calculation:**
```python
# SDK calculates cost BEFORE sending to collector
cost = pricing.compute_cost(
    provider="openai",
    model="gpt-4o",
    input_tokens=100,
    output_tokens=50,
    cached_tokens=20  # 10% discount for cached
)

# Uses baked-in PRICING_REGISTRY (synced with collector)
```

**Why Client-Side?**
- Reduces collector load
- Works even if collector is down
- Immediate cost feedback

### 4. **Transport Layer** (`transport.py`)

**HTTP POST to Collector:**
```python
requests.post(
    f"{collector_url}/events",
    json=events,  # Batch of events
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    timeout=5
)
```

**Error Handling:**
- **Silent failure** - Never breaks user's app
- If network fails, events are lost (but app continues)
- No retries (to avoid blocking)

---

## 🐛 Main Bug Vulnerabilities

### 1. **SDK Version Breakage** ⚠️ HIGH RISK

**What Can Break:**
- OpenAI restructures `resources.chat.Completions` → Patch fails
- Pinecone changes `Index` class structure → Patch fails
- Method signatures change → Wrapper breaks

**Current Safeguards:**
- ✅ Version checks (`check_openai_version()`)
- ✅ Try/except around each patch
- ✅ Graceful degradation (continues if one patch fails)
- ✅ Logging warnings

**What's Missing:**
- ❌ No automated testing against new SDK versions
- ❌ No version pinning recommendations
- ❌ No telemetry on patch failures

**Example Breakage:**
```python
# OpenAI v1.0 → v2.0 changes:
# OLD: resources.chat.Completions.create
# NEW: resources.chat.completions.create  # lowercase!
# Your patch breaks silently
```

### 2. **Multiple Library Conflicts** ⚠️ MEDIUM RISK

**What Happens:**
- User has Helicone + your SDK
- Both patch `resources.chat.Completions.create`
- Last patch wins → One library breaks

**Current Safeguards:**
- ✅ Conflict detection (`detect_patching_conflicts()`)
- ✅ Warns user about conflicts
- ✅ Checks for `__wrapped__` attribute

**What's Missing:**
- ❌ No coordination between libraries
- ❌ Can't prevent conflicts, only detect

**Example:**
```python
# User code:
import helicone
import llmobserve

helicone.patch()  # Patches OpenAI
llmobserve.observe()  # Patches OpenAI again

# Result: Helicone's patch is overwritten
# Helicone tracking breaks, but your tracking works
```

### 3. **Streaming Cancellation** ⚠️ MEDIUM RISK

**What Can Break:**
- User cancels stream early
- Usage data not in last chunk
- Token estimation may be inaccurate

**Current Safeguards:**
- ✅ Token estimation using tiktoken
- ✅ Accumulates content during stream
- ✅ Handles `GeneratorExit` exception

**What's Missing:**
- ❌ Estimation may be off by 10-20%
- ❌ No validation of estimated tokens

### 4. **Context Loss in Background Workers** ⚠️ LOW RISK

**What Can Break:**
- Celery/RQ workers don't inherit context
- Events lose `run_id`, `customer_id`

**Current Safeguards:**
- ✅ `celery_support.py` with context passing
- ✅ `with_context()` decorator
- ✅ Manual context restoration

**What's Missing:**
- ❌ Requires manual setup (not automatic)
- ❌ Easy to forget

### 5. **Silent Failures** ⚠️ LOW RISK

**What Can Break:**
- Network failure → Events lost
- Collector down → No tracking
- User never knows

**Current Safeguards:**
- ✅ App doesn't crash (good!)
- ✅ Logging (if enabled)

**What's Missing:**
- ❌ No retry mechanism
- ❌ No dead-letter queue
- ❌ No user notification

---

## 🔄 Will You Constantly Worry About SDK Changes?

### **Short Answer: Not Constantly, But You'll Need to Monitor**

### **Breakage Frequency:**

**OpenAI SDK:**
- **Major version changes:** ~1-2 times per year
  - v0.x → v1.0 (2023) - Major restructuring
  - v1.0 → v1.1 (2024) - Minor changes
- **Minor version changes:** ~Monthly
  - Usually backward compatible
  - Your patches should survive

**Pinecone SDK:**
- **Major version changes:** ~1 time per year
  - v6.x → v7.x (2024) - Major restructuring
- **Minor version changes:** ~Quarterly
  - Usually backward compatible

### **What You Need to Do:**

**Monthly:**
- ✅ Monitor OpenAI/Pinecone release notes
- ✅ Test against new SDK versions in CI
- ✅ Check user reports for patch failures

**Quarterly:**
- ✅ Update version compatibility checks
- ✅ Test all patched endpoints
- ✅ Update pricing registry if needed

**When Major Version Drops:**
- ⚠️ **Immediate action required**
- Test all patches
- Update patch code if needed
- Release hotfix within 24-48 hours

### **Your Current Safeguards Help:**

1. **Version Checks** - Warns about incompatible versions
2. **Graceful Degradation** - App doesn't crash if patch fails
3. **Conflict Detection** - Warns about library conflicts
4. **Logging** - Users can report issues

### **What Would Make It Better:**

1. **Automated Testing:**
   ```python
   # CI/CD tests against multiple SDK versions
   pytest tests/test_openai_patch.py --openai-version=1.0,1.1,1.2
   ```

2. **Version Pinning Recommendations:**
   ```python
   # Recommend users pin SDK versions
   # openai>=1.0,<2.0  # Safe range
   ```

3. **Telemetry:**
   ```python
   # Track patch failures in production
   # Alert when failure rate > 5%
   ```

4. **Wrapper Client Option:**
   ```python
   # Offer stable wrapper (like Helicone)
   from llmobserve import OpenAI  # Wrapper client
   # More stable than monkey-patching
   ```

---

## 📁 File-by-File Architecture

### **SDK (`sdk/python/llmobserve/`)**

#### `observe.py` - Entry Point
- **Purpose:** Initialize SDK
- **Key Functions:**
  - `observe()` - Main entry point
  - Calls `patch_openai()`, `patch_pinecone()`
  - Starts flush timer

#### `openai_patch.py` - OpenAI Monkey-Patching
- **Purpose:** Patch all OpenAI endpoints
- **Key Functions:**
  - `patch_openai()` - Main patching function
  - `_patch_method()` - Generic wrapper creator
  - `_track_openai_call()` - Event creation
  - `_wrap_streaming_response()` - Streaming handling
  - `_estimate_tokens()` - Token estimation (tiktoken)

#### `pinecone_patch.py` - Pinecone Monkey-Patching
- **Purpose:** Patch all Pinecone operations
- **Key Functions:**
  - `patch_pinecone()` - Main patching function
  - `_track_pinecone_call()` - Event creation
  - Patches 9 operations (query, upsert, delete, etc.)

#### `context.py` - Context Management
- **Purpose:** Async-safe context for run_id, customer_id, sections
- **Key Functions:**
  - `section()` - Context manager for hierarchical sections
  - `set_run_id()`, `get_run_id()`
  - `set_customer_id()`, `get_customer_id()`
  - `get_section_path()` - Full hierarchical path
  - Uses `contextvars` for async safety

#### `buffer.py` - Event Buffering
- **Purpose:** Thread-safe in-memory event buffer
- **Key Functions:**
  - `add_event()` - Add event to buffer
  - `get_and_clear_buffer()` - Get all events, clear buffer
  - `start_flush_timer()` - Background thread for auto-flush
  - Uses `threading.Lock()` for thread safety

#### `transport.py` - HTTP Transport
- **Purpose:** Send events to collector
- **Key Functions:**
  - `flush_events()` - POST batch to `/events`
  - Silent failure (doesn't break app)
  - Falls back to `urllib` if `requests` not available

#### `pricing.py` - Cost Calculation
- **Purpose:** Client-side cost calculation
- **Key Functions:**
  - `compute_cost()` - Calculate cost from tokens
  - Uses baked-in `PRICING_REGISTRY`
  - Handles cached tokens (10% discount)

#### `robustness.py` - Production Safeguards
- **Purpose:** Version checks, conflict detection, safe patching
- **Key Functions:**
  - `check_openai_version()` - Version compatibility
  - `detect_patching_conflicts()` - Find other libraries
  - `safe_patch()` - Safe wrapper with error handling
  - `get_patch_state()` - Debug patch status

#### `config.py` - Configuration
- **Purpose:** Global SDK configuration
- **Key Functions:**
  - `configure()` - Set collector_url, api_key
  - `is_enabled()` - Check if SDK enabled
  - `get_collector_url()`, `get_api_key()`

### **Collector (`collector/`)**

#### `main.py` - FastAPI App
- **Purpose:** FastAPI application entry point
- **Key Features:**
  - CORS middleware (allows all origins)
  - Database initialization on startup
  - Router registration

#### `db.py` - Database Setup
- **Purpose:** SQLModel engine and session management
- **Key Functions:**
  - `init_db()` - Create tables
  - `run_migrations()` - SQLite migrations
  - `get_session()` - FastAPI dependency

#### `models.py` - Database Models
- **Purpose:** SQLModel schemas
- **Key Models:**
  - `TraceEvent` - Main event table
  - `User` - User accounts (Clerk integration)
  - `APIKey` - API key management

#### `routers/events.py` - Event Ingestion
- **Purpose:** Receive events from SDK
- **Key Endpoints:**
  - `POST /events` - Batch ingest events
  - Validates API key
  - Computes cost if missing
  - Stores in database

#### `routers/runs.py` - Run Queries
- **Purpose:** Query runs and events
- **Key Endpoints:**
  - `GET /runs/latest` - Get recent runs
  - `GET /runs/{run_id}` - Get run details with events

#### `routers/insights.py` - Analytics
- **Purpose:** Aggregated analytics
- **Key Endpoints:**
  - `GET /insights/daily` - Daily cost breakdown
  - `GET /insights/provider` - Provider stats

#### `routers/dashboard.py` - Dashboard Data
- **Purpose:** Customer breakdown, stats
- **Key Endpoints:**
  - `GET /dashboard/customers` - Customer cost breakdown
  - `GET /dashboard/stats` - Overall stats

#### `routers/auth.py` - Authentication
- **Purpose:** API key validation
- **Key Functions:**
  - `get_current_user_id()` - Extract user_id from API key
  - Validates API key hash

### **Frontend (`web/`)**

#### `app/page.tsx` - Dashboard
- **Purpose:** Main dashboard with KPIs
- **Key Features:**
  - Customer filtering
  - Provider/agent stats
  - Recent runs

#### `app/runs/page.tsx` - Runs List
- **Purpose:** List of all runs
- **Key Features:**
  - Virtualized table
  - Filtering, search
  - Click to detail

#### `app/runs/[runId]/page.tsx` - Run Detail
- **Purpose:** Detailed run view
- **Key Features:**
  - Hierarchical trace tree
  - Event details
  - Cost breakdown

#### `app/costs/page.tsx` - Cost Breakdown
- **Purpose:** Cost analysis
- **Key Features:**
  - By provider, model, agent
  - Charts (Recharts)
  - Customer filtering

#### `app/agents/page.tsx` - Agent Analytics
- **Purpose:** Agent-specific metrics
- **Key Features:**
  - Agent cost breakdown
  - Top agents by cost
  - Agent detail drawer

---

## 🎯 Summary: Production Readiness

### **What Works Well:**
✅ Monkey-patching with safeguards
✅ Async-safe context management
✅ Thread-safe buffering
✅ Graceful degradation
✅ Conflict detection
✅ Version checks
✅ Silent failures (doesn't break app)

### **What Needs Monitoring:**
⚠️ SDK version updates (monthly check)
⚠️ Library conflicts (user education)
⚠️ Patch failures (logging + alerts)
⚠️ Streaming cancellation (token estimation)

### **What Could Be Better:**
🔧 Automated testing against SDK versions
🔧 Telemetry on patch health
🔧 Retry mechanism for failed sends
🔧 Wrapper client option (like Helicone)

### **Bottom Line:**
Your architecture is **production-ready** with the safeguards in place. You'll need to:
- Monitor SDK releases (monthly)
- Test patches on major version updates
- Respond to user reports quickly

But you **won't** constantly worry - the graceful degradation and logging mean issues are visible but not catastrophic.

