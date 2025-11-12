# Multi-Tenancy Implementation Status

**Date:** 2025-11-12  
**Goal:** Add unified multi-tenancy to support solo devs, shared-key SaaS, and multi-tenant SaaS

---

## ✅ COMPLETED

### 1. Database Schema ✅
- Added `tenant_id TEXT NOT NULL DEFAULT 'default_tenant'` to `TraceEvent` model
- Added indexes: `idx_tenant_id`, `idx_tenant_created`, `idx_tenant_customer`
- Created migration script: `migrations/003_add_tenant_id.sql`
- Updated `TraceEventCreate` schema to accept optional `tenant_id`

### 2. SDK Updates ✅
- **config.py**: Added `tenant_id` to global config
  - Loads from: explicit arg > `LLMOBSERVE_TENANT_ID` env var > "default_tenant"
  - Added `get_tenant_id()` helper function
- **observe.py**: Updated function signature to accept `tenant_id` parameter
  - Added comprehensive docstring examples for all 3 use cases
  - Passes `tenant_id` to `config.configure()`
- **types.py**: Added `tenant_id` field to `TraceEvent` TypedDict
- **Event Emission**: Updated ALL instrumentors to include `tenant_id` in events:
  - ✅ `openai_patch.py`
  - ✅ `pinecone_patch.py`
  - ✅ `instrumentation/utils.py` (OpenAI)
  - ✅ `instrumentation/google_instrumentor.py`
  - ✅ `instrumentation/elevenlabs_instrumentor.py`
  - ✅ `instrumentation/twilio_instrumentor.py`
  - ✅ `instrumentation/stripe_instrumentor.py`
  - ✅ `instrumentation/voyage_instrumentor.py`
  - ✅ `instrumentation/pinecone_instrumentor.py`
  - ✅ `instrumentation/cohere_instrumentor.py`
  - ✅ `instrumentation/anthropic_instrumentor.py`

### 3. Collector - Event Ingestion ✅
- **routers/events.py**: Updated `/events` POST endpoint
  - Handles `tenant_id` from event payload
  - Defaults to "default_tenant" if not provided
  - Maintains backward compatibility

---

## ⚠️ IN PROGRESS / PENDING

### 4. Collector - Query Endpoints 🚧
Need to add optional `tenant_id` query parameter to all read endpoints:

**Files to update:**
- `routers/runs.py` - `/runs/latest`, `/runs/{run_id}`, `/runs/sections/top`
- `routers/dashboard.py` - All dashboard endpoints
- `routers/insights.py` - All insights endpoints
- `routers/stats.py` - All stats endpoints
- `routers/tenants.py` - May already have tenant logic (check)

**Pattern to apply:**
```python
@router.get("/endpoint")
def endpoint_handler(
    tenant_id: Optional[str] = Query("default_tenant", description="Tenant identifier"),
    session: Session = Depends(get_session)
):
    statement = select(TraceEvent)...
    
    # Add tenant filter
    statement = statement.where(TraceEvent.tenant_id == tenant_id)
    
    # Rest of logic...
```

### 5. Frontend Updates 📱
Need to add tenant awareness:
- Add tenant ID to API calls (via query param or header)
- Optional: Add tenant selector UI component
- For MVP: Can default to "default_tenant" for all frontend calls

### 6. Database Migration 💾
Need to run migration:
```bash
# For PostgreSQL
psql $DATABASE_URL < migrations/003_add_tenant_id.sql

# For SQLite
sqlite3 collector.db < migrations/003_add_tenant_id.sql
```

### 7. Testing 🧪
Test all 3 scenarios:

**Scenario 1: Solo Developer (Default Tenant)**
```python
import llmobserve
llmobserve.observe(collector_url="http://localhost:8000")
# All events tagged with tenant_id="default_tenant"
```

**Scenario 2: Shared-Key SaaS (Track Customers)**
```python
import llmobserve
from llmobserve import set_customer_id

llmobserve.observe(
    collector_url="http://localhost:8000",
    tenant_id="my_company"  # Optional, defaults to "default_tenant"
)

# In request handler:
set_customer_id("customer_alice")
# API calls tagged with tenant_id="my_company", customer_id="customer_alice"
```

**Scenario 3: Multi-Tenant SaaS (Each Customer Sees Only Their Data)**
```python
import llmobserve

# For each logged-in tenant:
llmobserve.observe(
    collector_url="http://localhost:8000",
    tenant_id=logged_in_user.tenant_id  # From auth
)
# API calls tagged with their tenant_id
# Dashboard shows only their events
```

---

## 🎯 ARCHITECTURE SUMMARY

### Data Flow
```
SDK (observe) 
  → tenant_id (explicit arg / env var / "default_tenant")
  → config.get_tenant_id()
  → Included in every event
  → Collector POST /events
  → Database (tenant_id column)
  → Collector GET /runs?tenant_id=X
  → Frontend (filtered by tenant)
```

### Tenant Isolation
- **Database Level**: `tenant_id` column with indexes
- **API Level**: Query parameter `?tenant_id=X` on all endpoints
- **SDK Level**: Automatically includes `tenant_id` in all events
- **Frontend Level**: Passes `tenant_id` to all API calls

### Backward Compatibility
- ✅ Default value: "default_tenant"
- ✅ Existing code works without changes
- ✅ Migration adds column with default value
- ✅ No breaking changes to API

---

## 📋 NEXT STEPS

1. **Apply Migration**:
   ```bash
   cd /Users/pranavsrigiriraju/CostTracking
   python3 migrations/apply_migration.py 003_add_tenant_id.sql
   ```

2. **Update Collector Routes**:
   - Add `tenant_id` query param to all GET endpoints in:
     - `routers/runs.py`
     - `routers/dashboard.py`
     - `routers/insights.py`
     - `routers/stats.py`

3. **Update Frontend**:
   - Add `tenant_id` to API calls (default to "default_tenant" for MVP)
   - Optional: Add tenant selector UI

4. **Test All 3 Scenarios**:
   - Solo dev (no tenant_id specified)
   - Shared-key SaaS (set customer_id)
   - Multi-tenant SaaS (unique tenant_id per user)

5. **Documentation**:
   - Update README with multi-tenancy examples
   - Add migration guide for existing deployments

---

## 🚀 USE CASES SUPPORTED

### ✅ Use Case 1: Solo Developer
**How it works:**
- Call `llmobserve.observe()` with no tenant_id
- Defaults to "default_tenant"
- All costs tracked under one account
- No authentication required

**Example:**
```python
import llmobserve
llmobserve.observe(collector_url="http://localhost:8000")
# Done! All tracking works automatically
```

### ✅ Use Case 2: SaaS with Shared Keys
**How it works:**
- You use your own API keys (OpenAI, Pinecone, etc.)
- You want to track which customers cost you the most
- Use `set_customer_id()` to tag costs per customer
- Optional: Set your company's tenant_id

**Example:**
```python
import llmobserve
from llmobserve import set_customer_id

llmobserve.observe(
    collector_url="http://localhost:8000",
    tenant_id="acme_corp"  # Optional
)

# In your request handler:
@app.post("/api/chat")
def handle_chat(request):
    set_customer_id(request.user_id)  # Tag costs to this customer
    response = openai_client.chat.completions.create(...)
    return response
```

**Dashboard shows:**
- Total costs: Your actual spend
- Per-customer breakdown: Which customers cost the most
- You can filter by `customer_id`

### ✅ Use Case 3: Multi-Tenant SaaS
**How it works:**
- Each logged-in customer has unique `tenant_id`
- Each customer sees ONLY their data
- Row-level filtering by `tenant_id`
- Each customer can track their own end-users via `customer_id`

**Example:**
```python
import llmobserve

# During user login/session init:
llmobserve.observe(
    collector_url="http://localhost:8000",
    tenant_id=logged_in_user.tenant_id  # From your auth system
)

# Optional: Track their end-customers too
from llmobserve import set_customer_id
set_customer_id(end_user.id)
```

**Dashboard shows (per tenant):**
- Only their costs
- Their per-customer breakdown (if they use `set_customer_id()`)
- Complete isolation from other tenants

---

## 🔐 AUTHENTICATION NOTES

For MVP:
- `tenant_id` is a simple string filter (no auth required)
- Frontend defaults to "default_tenant"
- Suitable for solo devs and trusted environments

For Production Multi-Tenancy:
- Add auth middleware to extract `tenant_id` from JWT/API key
- Enforce tenant isolation at API level
- Add row-level security in database
- Add tenant-scoped dashboards

**Simple Auth Middleware (Future):**
```python
async def get_current_tenant_id(
    authorization: Optional[str] = Header(None)
) -> str:
    if not authorization:
        return "default_tenant"  # MVP mode
    
    # Extract tenant_id from JWT/API key
    token = extract_bearer_token(authorization)
    tenant_id = decode_jwt(token).get("tenant_id")
    return tenant_id or "default_tenant"
```

Then use as dependency:
```python
@router.get("/runs")
def get_runs(
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session)
):
    # Automatically filtered by authenticated tenant
    statement = select(TraceEvent).where(TraceEvent.tenant_id == tenant_id)
    ...
```

---

## ✅ CONCLUSION

**What's Working:**
- ✅ Database schema supports multi-tenancy
- ✅ SDK emits `tenant_id` in all events
- ✅ Event ingestion handles `tenant_id`
- ✅ Backward compatible (defaults to "default_tenant")

**What's Needed:**
- 🚧 Add `tenant_id` filtering to query endpoints
- 📱 Update frontend to pass `tenant_id`
- 💾 Run database migration
- 🧪 Test all 3 scenarios

**Estimated Time to Complete:**
- Collector routes: 30 minutes
- Frontend updates: 15 minutes
- Migration: 5 minutes
- Testing: 30 minutes
- **Total: ~1.5 hours**

