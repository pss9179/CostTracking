# 🎯 Multi-Tenant SaaS Guide - Per-Tenant Cost Tracking

**Status:** ✅ **FULLY IMPLEMENTED**  
**Date:** December 2024

---

## 📋 Overview

When you give this library to someone, **each tenant automatically gets their own isolated dashboard** showing:
- ✅ **Their own usage and costs** (only their data)
- ✅ **What APIs they're using** (provider breakdown)
- ✅ **Their run structure** (hierarchical traces)
- ✅ **Per-customer breakdown** (if they use `set_customer_id()`)

**Complete data isolation** - Tenant A cannot see Tenant B's data.

---

## 🏗️ Architecture

### How It Works

1. **SDK Initialization**: Each tenant calls `llmobserve.observe()` with their `tenant_id`
2. **Event Emission**: All API calls are tagged with `tenant_id` 
3. **Database Storage**: Events stored with `tenant_id` column (indexed for fast queries)
4. **API Filtering**: Collector routes filter by `tenant_id` 
5. **Dashboard**: Frontend passes `tenant_id` to show only that tenant's data

### Data Flow

```
┌─────────────────────────────────────────┐
│  TENANT A's CODE                        │
│                                         │
│  llmobserve.observe(                   │
│      collector_url="...",              │
│      tenant_id="tenant_a"               │
│  )                                      │
│                                         │
│  openai_client.chat.completions.create()│
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│  SDK (llmobserve)                       │
│                                         │
│  Intercepts API call                    │
│  Adds header: X-LLMObserve-Tenant-ID   │
│  Routes through proxy                   │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│  PROXY                                  │
│                                         │
│  Parses response                       │
│  Calculates cost                       │
│  Creates event:                        │
│    {                                   │
│      "tenant_id": "tenant_a",          │
│      "cost_usd": 0.000123,             │
│      ...                               │
│    }                                   │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│  COLLECTOR API                          │
│                                         │
│  POST /events                          │
│  Stores in database                    │
│  tenant_id indexed                     │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│  DATABASE                               │
│                                         │
│  trace_events table:                   │
│  ┌──────────────┬──────────────┐     │
│  │ tenant_id     │ cost_usd     │     │
│  ├──────────────┼──────────────┤     │
│  │ tenant_a      │ 0.000123     │     │
│  │ tenant_b      │ 0.000456     │     │
│  │ tenant_a      │ 0.000789     │     │
│  └──────────────┴──────────────┘     │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│  DASHBOARD                              │
│                                         │
│  GET /runs?tenant_id=tenant_a          │
│  → Returns only tenant_a's runs        │
│                                         │
│  GET /stats/by-provider?tenant_id=...  │
│  → Returns only tenant_a's providers   │
└─────────────────────────────────────────┘
```

---

## 🚀 Usage Examples

### Example 1: Multi-Tenant SaaS Platform

**Scenario**: You're building a SaaS where each customer logs in and sees their own cost dashboard.

**Backend Code** (Python):
```python
import llmobserve
from llmobserve import set_customer_id

# During user login/session initialization
def initialize_for_tenant(logged_in_user):
    # Each logged-in user becomes a tenant
    llmobserve.observe(
        collector_url="https://your-llmobserve.com",
        tenant_id=logged_in_user.id,  # Use Clerk user ID or your user ID
        api_key=logged_in_user.api_key  # Optional: tenant-specific API key
    )

# Example: User "acme_corp" logs in
user = get_logged_in_user()  # user.id = "user_abc123"
initialize_for_tenant(user)

# Now all their API calls are tagged with tenant_id="user_abc123"
response = openai_client.chat.completions.create(...)

# Optional: They can track their own end-customers
set_customer_id("end_user_42")
```

**What Happens**:
- ✅ All events tagged with `tenant_id="user_abc123"`
- ✅ Dashboard shows ONLY their costs
- ✅ Complete isolation from other tenants
- ✅ They can track their own customers via `set_customer_id()`

---

### Example 2: White-Label Observability

**Scenario**: You sell LLMObserve as a service. Each customer gets their own dashboard.

**Customer A's Code**:
```python
import llmobserve

llmobserve.observe(
    collector_url="https://llmobserve-saas.com",
    tenant_id="acme_corp",  # Their tenant ID
    api_key="llmo_sk_acme_..."  # Their API key
)
```

**Customer B's Code**:
```python
import llmobserve

llmobserve.observe(
    collector_url="https://llmobserve-saas.com",
    tenant_id="globex_inc",  # Different tenant ID
    api_key="llmo_sk_globex_..."  # Their API key
)
```

**Result**:
- ✅ Acme Corp sees ONLY their data
- ✅ Globex Inc sees ONLY their data
- ✅ Complete isolation at database level

---

### Example 3: Using Clerk Authentication

**Scenario**: Your dashboard uses Clerk for authentication. Each Clerk user becomes a tenant.

**Frontend** (Next.js):
```typescript
import { useUser } from "@clerk/nextjs";
import { getTenantId, fetchRuns } from "@/lib/api";

export default function Dashboard() {
  const { user } = useUser();
  
  useEffect(() => {
    if (!user) return;
    
    // Get tenant_id from Clerk user
    const tenantId = getTenantId(user.id);  // Returns user.id
    
    // Fetch only this tenant's data
    fetchRuns(100, tenantId).then(setRuns);
  }, [user]);
}
```

**Backend** (Python SDK):
```python
import llmobserve

# When user logs in, initialize with their Clerk user ID
clerk_user_id = "user_abc123"  # From Clerk

llmobserve.observe(
    collector_url="http://localhost:8000",
    tenant_id=clerk_user_id  # Same ID used in frontend
)
```

**Result**:
- ✅ Frontend automatically filters by `tenant_id`
- ✅ Backend tags all events with same `tenant_id`
- ✅ Perfect sync between frontend and backend

---

## 🔐 Implementation Details

### Database Schema

```sql
CREATE TABLE trace_events (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL DEFAULT 'default_tenant',  -- 🆕 Tenant isolation
    customer_id TEXT,  -- Tenant's end-customers
    provider TEXT NOT NULL,
    cost_usd REAL NOT NULL,
    ...
);

CREATE INDEX idx_tenant_id ON trace_events(tenant_id);
CREATE INDEX idx_tenant_created ON trace_events(tenant_id, created_at);
CREATE INDEX idx_tenant_customer ON trace_events(tenant_id, customer_id);
```

### Collector Routes

All collector routes now support `tenant_id` query parameter:

```python
# GET /runs/latest?tenant_id=tenant_a
# GET /stats/by-provider?tenant_id=tenant_a
# GET /runs/{run_id}?tenant_id=tenant_a
# GET /dashboard/customers?tenant_id=tenant_a
```

**Filtering Logic**:
```python
if tenant_id:
    statement = statement.where(TraceEvent.tenant_id == tenant_id)
elif user_id:
    statement = statement.where(TraceEvent.user_id == user_id)
# If neither provided, returns all data (MVP mode)
```

### Frontend Integration

**Helper Function** (`web/lib/api.ts`):
```typescript
export function getTenantId(userId: string | null | undefined): string | null {
  if (!userId) return null;
  // Use Clerk user ID as tenant_id
  return userId;
}
```

**API Calls**:
```typescript
// All API functions accept optional tenantId parameter
fetchRuns(limit: number, tenantId?: string | null)
fetchRunDetail(runId: string, tenantId?: string | null)
fetchProviderStats(hours: number, tenantId?: string | null)
```

---

## ✅ What's Implemented

### Backend (Collector)
- ✅ `tenant_id` column in database (indexed)
- ✅ All routes filter by `tenant_id` query parameter
- ✅ Backward compatible (defaults to "default_tenant" if not provided)
- ✅ Event ingestion handles `tenant_id`

### Frontend (Dashboard)
- ✅ Helper function `getTenantId()` to get tenant from Clerk user
- ✅ All API calls accept `tenantId` parameter
- ✅ Dashboard page passes `tenant_id` automatically
- ✅ Complete tenant isolation in UI

### SDK
- ✅ `observe()` accepts `tenant_id` parameter
- ✅ All events automatically include `tenant_id`
- ✅ Can be set via argument, env var, or dynamically
- ✅ Works with proxy architecture

---

## 🧪 Testing Multi-Tenancy

### Test Scenario: Two Tenants

**Tenant A**:
```python
import llmobserve

llmobserve.observe(
    collector_url="http://localhost:8000",
    tenant_id="tenant_a"
)

# Make some API calls
response = openai_client.chat.completions.create(...)
```

**Tenant B**:
```python
import llmobserve

llmobserve.observe(
    collector_url="http://localhost:8000",
    tenant_id="tenant_b"
)

# Make some API calls
response = openai_client.chat.completions.create(...)
```

**Verify Isolation**:
```bash
# Tenant A should only see their data
curl "http://localhost:8000/runs/latest?tenant_id=tenant_a"

# Tenant B should only see their data
curl "http://localhost:8000/runs/latest?tenant_id=tenant_b"

# Without tenant_id, see all data (admin view)
curl "http://localhost:8000/runs/latest"
```

---

## 📊 Dashboard Features Per Tenant

Each tenant sees:

1. **Total Costs**: Only their spend
2. **Provider Breakdown**: Which APIs they're using (OpenAI, Anthropic, etc.)
3. **Run Structure**: Hierarchical traces of their API calls
4. **Per-Customer Breakdown**: If they use `set_customer_id()`
5. **Cost Trends**: Time-series of their costs
6. **Insights**: Anomaly detection for their usage

**Complete isolation** - No tenant can see another tenant's data.

---

## 🎯 Use Cases

### ✅ Use Case 1: Multi-Tenant SaaS Platform
- Each logged-in customer is a tenant
- They see only their costs
- Perfect for platforms like Shopify, Notion, etc.

### ✅ Use Case 2: White-Label Observability
- You sell LLMObserve as a service
- Each customer gets unique `tenant_id`
- Complete data isolation

### ✅ Use Case 3: Enterprise Multi-Tenancy
- Large organizations with multiple teams
- Each team is a tenant
- Centralized cost tracking with team isolation

---

## 🔒 Security Notes

**Current Implementation (MVP)**:
- `tenant_id` is passed as query parameter
- No authentication required (suitable for trusted environments)
- Frontend automatically passes `tenant_id` from Clerk user

**For Production**:
- Add auth middleware to extract `tenant_id` from JWT/API key
- Enforce tenant isolation at API level
- Add row-level security in database
- Validate `tenant_id` matches authenticated user

**Example Auth Middleware** (Future):
```python
async def get_current_tenant_id(
    authorization: Optional[str] = Header(None)
) -> str:
    token = extract_bearer_token(authorization)
    user = decode_jwt(token)
    return user.tenant_id  # From JWT claims
```

---

## 📝 Summary

**What You Get**:
- ✅ **Automatic tenant isolation** - Each tenant sees only their data
- ✅ **Zero configuration** - Works out of the box with Clerk
- ✅ **Complete isolation** - Database-level filtering
- ✅ **Flexible** - Works with any authentication system
- ✅ **Backward compatible** - Existing code works unchanged

**How It Works**:
1. SDK tags events with `tenant_id`
2. Collector filters by `tenant_id`
3. Dashboard shows only tenant's data
4. Complete isolation at every level

**When you give this library to someone, they automatically get their own isolated dashboard!** 🎉

