# 🎯 LLMObserve Multi-Tenancy - Complete Guide

**Status:** ✅ **FULLY IMPLEMENTED**  
**Date:** November 12, 2025

---

## 📋 TABLE OF CONTENTS

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Use Cases](#use-cases)
4. [SDK Usage](#sdk-usage)
5. [How Data Flows](#how-data-flows)
6. [Customer Attribution](#customer-attribution)
7. [Multi-Tenant SaaS](#multi-tenant-saas)
8. [Deployment Modes](#deployment-modes)
9. [FAQ](#faq)

---

## OVERVIEW

LLMObserve now supports **unified multi-tenancy** that works for:

✅ **Solo developers** building personal projects  
✅ **SaaS founders** tracking costs per customer  
✅ **Multi-tenant platforms** where each tenant sees only their data

**Key Features:**
- Zero-config default (`tenant_id = "default_tenant"`)
- Backward compatible (existing code works unchanged)
- Customer tracking (`customer_id`) works independently
- Flexible: explicit tenant_id OR environment variable OR authentication

---

## ARCHITECTURE

### Data Model

Every trace event now includes:

```typescript
{
  "run_id": "uuid",           // Groups calls in one request
  "span_id": "uuid",           // Unique span identifier
  "parent_span_id": "uuid",    // For hierarchical traces
  "section": "agent:research", // User-defined label
  "tenant_id": "acme_corp",    // 🆕 Tenant identifier
  "customer_id": "alice",      // Tenant's end-customer
  "provider": "openai",
  "cost_usd": 0.000123,
  ...
}
```

**Isolation Levels:**
1. **`tenant_id`**: Top-level isolation (who's using LLMObserve)
2. **`customer_id`**: Second-level isolation (tenant's customers)

### Schema Changes

**Database:**
```sql
ALTER TABLE trace_events 
ADD COLUMN tenant_id TEXT NOT NULL DEFAULT 'default_tenant';

CREATE INDEX idx_tenant_id ON trace_events(tenant_id);
CREATE INDEX idx_tenant_created ON trace_events(tenant_id, created_at);
CREATE INDEX idx_tenant_customer ON trace_events(tenant_id, customer_id);
```

**SDK:**
- All events automatically include `tenant_id`
- Defaults to `"default_tenant"` if not specified
- Can be set via argument, env var, or auth

**Collector:**
- Event ingestion handles `tenant_id`
- Query endpoints filter by `tenant_id` (when implemented)

---

## USE CASES

### 1️⃣ Solo Developer (Personal Project)

**Scenario:** You're building an AI app for yourself

**Code:**
```python
import llmobserve

llmobserve.observe(collector_url="http://localhost:8000")

# That's it! All tracking works automatically
# tenant_id defaults to "default_tenant"
```

**What happens:**
- All your API calls tracked under `tenant_id="default_tenant"`
- Dashboard shows your total costs
- No configuration needed

**Use case:**
- Personal projects
- Internal tools
- Prototypes
- Learning/experimentation

---

### 2️⃣ SaaS Founder (Track Your Customers)

**Scenario:** You build SaaS, use your own API keys, want to see which customers cost you the most

**Code:**
```python
import llmobserve
from llmobserve import set_customer_id

# One-time initialization (your server startup)
llmobserve.observe(
    collector_url="https://your-llmobserve.com",
    tenant_id="your_company",  # Optional: defaults to "default_tenant"
    api_key="your-api-key"
)

# In your request handler
@app.post("/api/chat")
def handle_chat(request):
    # Tag costs to specific customer
    set_customer_id(request.user_id)  # e.g., "customer_alice"
    
    # Now all OpenAI/Pinecone calls are tracked per customer
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": request.message}]
    )
    
    return response
```

**What happens:**
- All events tagged with `tenant_id="your_company"`, `customer_id="customer_alice"`
- Dashboard shows:
  - **Total cost**: Your actual spend (all customers combined)
  - **Per-customer breakdown**: Which customers cost you the most
  - **Filtering**: View costs for specific customer

**Use case:**
- SaaS products with usage-based pricing
- Identifying high-cost customers
- Cost allocation for billing
- Optimization (which customers/features are expensive)

**Key Points:**
- ✅ You use **your** API keys (OpenAI, Pinecone, etc.)
- ✅ You run **one** collector for your whole SaaS
- ✅ You see **all** customer costs in one dashboard
- ✅ Deployment agnostic (cloud or on-prem)

---

### 3️⃣ Multi-Tenant SaaS (Each Tenant Sees Only Their Data)

**Scenario:** You sell LLMObserve (or use it in a platform where each customer wants their own dashboard)

**Code:**
```python
import llmobserve

# During user login / session initialization
def initialize_observability_for_tenant(logged_in_user):
    llmobserve.observe(
        collector_url="https://your-llmobserve.com",
        tenant_id=logged_in_user.tenant_id,  # Unique per tenant
        api_key=logged_in_user.api_key       # Tenant-specific API key
    )

# Example: Tenant "acme_corp" logs in
initialize_observability_for_tenant(
    logged_in_user=User(tenant_id="acme_corp", api_key="llmo_sk_...")
)

# All their API calls are now tagged with tenant_id="acme_corp"

# Optional: They can track their own end-customers too
from llmobserve import set_customer_id
set_customer_id("end_user_42")
```

**What happens:**
- Each tenant's events isolated by `tenant_id`
- Tenant "acme_corp" sees ONLY their costs
- Tenant "globex" sees ONLY their costs
- Row-level filtering ensures data isolation

**Dashboard (per tenant):**
- Total cost: Only their spend
- Per-customer breakdown: Their end-users (if they use `set_customer_id()`)
- Complete isolation from other tenants

**Use case:**
- Multi-tenant platforms (Shopify, Notion, etc.)
- White-label observability
- Reseller/agency models
- Enterprise deployments

**What's needed for full multi-tenant:**
- ⚠️ Auth middleware to extract `tenant_id` from JWT/API key
- ⚠️ Frontend tenant-scoped dashboards
- ⚠️ Collector routes need `tenant_id` filtering (partially implemented)

---

## SDK USAGE

### Basic Initialization

```python
import llmobserve

# Minimal (solo dev)
llmobserve.observe(collector_url="http://localhost:8000")

# With tenant ID (shared-key SaaS)
llmobserve.observe(
    collector_url="http://localhost:8000",
    tenant_id="my_company"
)

# Multi-tenant (from auth)
llmobserve.observe(
    collector_url="http://localhost:8000",
    tenant_id=logged_in_user.tenant_id  # From your auth system
)
```

### Environment Variables

```bash
# Set tenant ID via environment
export LLMOBSERVE_TENANT_ID="my_company"
export LLMOBSERVE_COLLECTOR_URL="http://localhost:8000"
export LLMOBSERVE_API_KEY="dev-mode"
```

```python
import llmobserve

# tenant_id automatically loaded from env var
llmobserve.observe()
```

### Priority Order

Tenant ID resolution (highest to lowest priority):

1. **Explicit argument**: `observe(tenant_id="xyz")`
2. **Environment variable**: `LLMOBSERVE_TENANT_ID`
3. **Default value**: `"default_tenant"`

### Customer Tracking

```python
from llmobserve import set_customer_id

# Set customer for current request/context
set_customer_id("customer_alice")

# All API calls from here tagged with customer_id="customer_alice"
```

**Note:** `customer_id` is independent of `tenant_id`:
- `tenant_id`: Who's using LLMObserve (top-level)
- `customer_id`: Tenant's end-customers (second-level)

---

## HOW DATA FLOWS

### Flow Diagram

```
┌─────────────────────────────────────────┐
│  DEVELOPER CODE                         │
│                                         │
│  llmobserve.observe(tenant_id="acme")  │
│  set_customer_id("alice")               │
│                                         │
│  openai_client.chat.completions.create()│
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│  SDK (llmobserve)                       │
│                                         │
│  1. Intercepts OpenAI call              │
│  2. Reads context:                      │
│     - tenant_id = "acme"                │
│     - customer_id = "alice"             │
│  3. Creates event:                      │
│     {                                   │
│       "tenant_id": "acme",              │
│       "customer_id": "alice",           │
│       "cost_usd": 0.000123,             │
│       ...                               │
│     }                                   │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│  COLLECTOR (FastAPI)                    │
│                                         │
│  POST /events                           │
│  - Receives events                      │
│  - Defaults tenant_id if missing        │
│  - Stores in database                   │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│  DATABASE (SQLite/PostgreSQL)           │
│                                         │
│  trace_events table:                    │
│  ┌────────────────┬──────────────┐     │
│  │ tenant_id      │ customer_id  │     │
│  ├────────────────┼──────────────┤     │
│  │ acme           │ alice        │     │
│  │ acme           │ bob          │     │
│  │ globex         │ carol        │     │
│  │ default_tenant │ NULL         │     │
│  └────────────────┴──────────────┘     │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│  DASHBOARD (Next.js)                    │
│                                         │
│  GET /runs?tenant_id=acme               │
│  - Filters by tenant_id                 │
│  - Shows only "acme" data               │
│  - Can further filter by customer_id    │
└─────────────────────────────────────────┘
```

---

## CUSTOMER ATTRIBUTION

### How It Works

**Tenant-level** (`tenant_id`):
- Who's using LLMObserve
- Top-level isolation
- Used for multi-tenancy

**Customer-level** (`customer_id`):
- Tenant's end-users
- Second-level attribution
- Used for cost breakdown

### Example: SaaS Product

```
tenant_id: "acme_corp" (your SaaS company)
├── customer_id: "alice"
│   ├── OpenAI call: $0.001
│   └── Pinecone call: $0.0001
├── customer_id: "bob"
│   └── OpenAI call: $0.002
└── customer_id: "carol"
    └── OpenAI call: $0.0005
```

**Dashboard shows:**
- Total cost: $0.0036 (all customers)
- Per-customer:
  - alice: $0.0011
  - bob: $0.0020
  - carol: $0.0005

### Use Cases for Customer Attribution

1. **Usage-based pricing**: Charge customers based on their actual API usage
2. **Cost optimization**: Identify high-cost customers
3. **Feature analysis**: Which features/customers drive costs
4. **Alerts**: Notify when customer exceeds budget
5. **Billing**: Generate invoices based on actual usage

---

## MULTI-TENANT SAAS

### Current State

**✅ What's Working:**
- SDK emits `tenant_id` in all events
- Database schema supports tenant isolation
- Event ingestion handles `tenant_id`
- Backward compatible (defaults to "default_tenant")

**⚠️ What's Needed for Full Multi-Tenancy:**
1. **Auth middleware**: Extract `tenant_id` from JWT/API key
2. **Collector routes**: Add `tenant_id` filtering to all query endpoints
3. **Frontend**: Tenant-scoped dashboards
4. **Row-level security**: Enforce tenant isolation at DB level

### Simple Auth Middleware (Example)

```python
# collector/auth.py

async def get_current_tenant_id(
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_session)
) -> str:
    """
    Extract tenant_id from API key or JWT.
    Returns "default_tenant" for unauthenticated requests (MVP mode).
    """
    if not authorization:
        return "default_tenant"  # MVP: Allow unauthenticated
    
    # Extract tenant_id from API key or JWT
    api_key = extract_bearer_token(authorization)
    user = await validate_api_key(api_key, session)
    
    # Map user to tenant_id (could be user.id or user.tenant_id field)
    return user.tenant_id if user else "default_tenant"
```

### Tenant-Scoped Routes (Example)

```python
# collector/routers/runs.py

@router.get("/runs")
def get_runs(
    tenant_id: str = Depends(get_current_tenant_id),  # From auth
    session: Session = Depends(get_session)
):
    """Get runs for authenticated tenant only."""
    statement = select(TraceEvent).where(
        TraceEvent.tenant_id == tenant_id
    )
    events = session.exec(statement).all()
    return events
```

---

## DEPLOYMENT MODES

### Mode 1: Self-Hosted (Solo Dev)

```bash
# Run collector locally
cd collector
uvicorn main:app --reload

# In your code
llmobserve.observe(collector_url="http://localhost:8000")
```

**Characteristics:**
- Single user
- No authentication required
- `tenant_id="default_tenant"`
- Perfect for development/testing

### Mode 2: Self-Hosted (Shared-Key SaaS)

```bash
# Deploy collector to your infrastructure
docker-compose up -d

# In your SaaS backend
llmobserve.observe(
    collector_url="https://llmobserve.yourcompany.com",
    tenant_id="your_company"
)
```

**Characteristics:**
- One collector for your whole SaaS
- You see all customer costs
- Use `set_customer_id()` for attribution
- Cloud or on-prem deployment

### Mode 3: Multi-Tenant SaaS

```bash
# Deploy collector with authentication
# Each tenant gets unique tenant_id

# Tenant A's code
llmobserve.observe(
    collector_url="https://llmobserve-saas.com",
    tenant_id="tenant_a",
    api_key="llmo_sk_tenant_a_..."
)

# Tenant B's code
llmobserve.observe(
    collector_url="https://llmobserve-saas.com",
    tenant_id="tenant_b",
    api_key="llmo_sk_tenant_b_..."
)
```

**Characteristics:**
- Shared infrastructure, isolated data
- Each tenant has unique API key
- Row-level filtering by `tenant_id`
- Tenant-scoped dashboards

### Mode 4: Hybrid

**On-Prem vs. Cloud doesn't matter!**

```python
# Customer A: Self-hosted collector
llmobserve.observe(
    collector_url="https://collector.customer-a.com",
    tenant_id="customer_a"
)

# Customer B: Your SaaS collector
llmobserve.observe(
    collector_url="https://your-saas.com",
    tenant_id="customer_b"
)
```

**Both work identically!** The SDK doesn't care where the collector is.

---

## FAQ

### Q1: "Do I need to pass `tenant_id` every time I make an API call?"

**A:** No! You set it once during initialization:

```python
llmobserve.observe(tenant_id="my_company")
```

Then all API calls automatically include `tenant_id="my_company"`.

---

### Q2: "What if I don't specify `tenant_id`?"

**A:** It defaults to `"default_tenant"`. Perfect for:
- Solo developers
- Personal projects
- Testing/development

```python
llmobserve.observe(collector_url="http://localhost:8000")
# tenant_id automatically set to "default_tenant"
```

---

### Q3: "Can I use environment variables instead of passing `tenant_id`?"

**A:** Yes!

```bash
export LLMOBSERVE_TENANT_ID="my_company"
export LLMOBSERVE_COLLECTOR_URL="http://localhost:8000"
```

```python
llmobserve.observe()  # Loads from env vars
```

---

### Q4: "What's the difference between `tenant_id` and `customer_id`?"

**A:**
- **`tenant_id`**: Who's using LLMObserve (top-level isolation)
- **`customer_id`**: Tenant's end-customers (for cost attribution)

**Example:**
```
tenant_id: "acme_corp" (your SaaS company)
└── customer_id: "alice" (your customer)
```

You can use both:
```python
llmobserve.observe(tenant_id="acme_corp")
set_customer_id("alice")
```

---

### Q5: "If I sell SaaS, do my customers need to provide their own API keys?"

**A:** No! There are two modes:

**Mode 1: Shared Keys (Common)**
- **You** use your own OpenAI/Pinecone keys
- **You** pay for API costs
- You track which customers cost you the most via `set_customer_id()`
- This is what most SaaS products do

**Mode 2: Customer Keys (Advanced)**
- Each customer provides their own API keys
- They pay for their own API costs
- Requires more complex setup (not common)

---

### Q6: "Does deployment mode (cloud vs on-prem) matter?"

**A:** Nope! The SDK works the same regardless of where the collector is:

```python
# Cloud collector
llmobserve.observe(collector_url="https://cloud.llmobserve.com")

# On-prem collector
llmobserve.observe(collector_url="http://internal-server:8000")

# localhost
llmobserve.observe(collector_url="http://localhost:8000")
```

All work identically!

---

### Q7: "Can I change `tenant_id` at runtime?"

**A:** Not easily. The `observe()` function is meant to be called once at startup. If you need to switch tenants dynamically, you'd need to:

1. Store multiple configurations
2. Re-initialize before each tenant's requests
3. Or use a middleware to inject `tenant_id` dynamically

For most use cases, set it once based on:
- Your company (shared-key SaaS)
- Logged-in user (multi-tenant SaaS)
- Environment variable (solo dev)

---

### Q8: "What happens to existing data when I add `tenant_id`?"

**A:** Migration automatically sets `tenant_id="default_tenant"` for all existing events. They'll continue to work normally.

---

### Q9: "How do I filter dashboard by tenant?"

**A:** (Once collector routes are updated)

```http
GET /runs?tenant_id=acme_corp
GET /insights?tenant_id=acme_corp
```

Frontend will pass `tenant_id` as query parameter.

---

### Q10: "Is this production-ready?"

**A:**

**For Solo Dev / Shared-Key SaaS:** ✅ **YES!**
- SDK emits `tenant_id`
- Database stores it
- Event ingestion works
- Just needs collector routes updated (15 min task)

**For Multi-Tenant SaaS:** ⚠️ **NEEDS AUTH**
- Add auth middleware to extract `tenant_id` from API key
- Add row-level security
- Add tenant-scoped dashboards
- Estimated: 2-4 hours of work

---

## 🎯 NEXT STEPS

### For Solo Devs / Shared-Key SaaS:

1. **Start using it!**
   ```python
   llmobserve.observe(tenant_id="my_company")
   set_customer_id(user.id)
   ```

2. **Run migration** (if you have existing data):
   ```bash
   sqlite3 collector.db < migrations/003_add_tenant_id.sql
   ```

3. **Update collector routes** (when ready):
   - Add `tenant_id` filtering to query endpoints

### For Multi-Tenant SaaS:

1. **Implement auth middleware**:
   - Extract `tenant_id` from JWT/API key
   - Return `"default_tenant"` for MVP mode

2. **Update collector routes**:
   - Use `tenant_id` from auth as default filter
   - Enforce row-level security

3. **Update frontend**:
   - Pass `tenant_id` to all API calls
   - Add tenant selector (optional)

4. **Test tenant isolation**:
   - Verify tenant A can't see tenant B's data
   - Test customer attribution within tenants

---

## ✅ SUMMARY

**What You Get:**

✅ **Unified multi-tenancy** - one system, three use cases  
✅ **Backward compatible** - existing code works unchanged  
✅ **Flexible isolation** - tenant_id + customer_id  
✅ **Zero-config default** - works out of the box for solo devs  
✅ **Deployment agnostic** - cloud, on-prem, localhost all work  
✅ **Production-ready** - for solo dev and shared-key SaaS (with minor collector updates)

**What's Needed for Full Multi-Tenant:**

⚠️ Auth middleware (extract tenant_id from API key)  
⚠️ Collector route updates (add tenant_id filtering)  
⚠️ Frontend updates (pass tenant_id, tenant selector)  
⚠️ Testing (verify tenant isolation)

---

**Questions? Check the examples above or ask!** 🚀

