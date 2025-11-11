# SaaS Transformation Plan

## 🎯 Goal
Transform LLMObserve from a multi-tenant local tool into a production SaaS where users:
1. Sign up and create an account
2. Get an API key
3. Download/install the Python SDK
4. Configure SDK with their API key
5. See all their costs in a personalized dashboard

---

## 🏗️ Architecture Changes

### Current → New
- ❌ SQLite → ✅ PostgreSQL (Supabase or Neon)
- ❌ `tenant_id` → ✅ `user_id` / `account_id`
- ❌ Manual tenant selection → ✅ Automatic user-scoped data
- ❌ No authentication → ✅ Clerk or NextAuth.js
- ❌ Local deployment → ✅ Vercel (frontend) + Railway/Render (backend)

---

## 📋 Implementation Phases

### Phase 1: Authentication & User Management (Priority 1) ⭐
**Goal**: Users can sign up, login, and have isolated accounts

#### Frontend (Next.js)
- [ ] Install Clerk (recommended) or NextAuth.js
- [ ] Add `/sign-up` and `/sign-in` pages
- [ ] Add protected route middleware
- [ ] Add user profile/settings page
- [ ] Remove tenant selector dropdown
- [ ] Add "API Keys" settings page

#### Backend (FastAPI)
- [ ] Add API key validation middleware
- [ ] Create `users` table (id, email, created_at, subscription_tier)
- [ ] Create `api_keys` table (id, user_id, key_hash, name, created_at, last_used, revoked)
- [ ] Add endpoints:
  - `POST /api-keys` - Generate new API key
  - `GET /api-keys` - List user's API keys
  - `DELETE /api-keys/{key_id}` - Revoke API key

#### Database Migration
- [ ] Replace `tenant_id` with `user_id` in `trace_events` table
- [ ] Add `users` table
- [ ] Add `api_keys` table
- [ ] Migration script: `001_add_auth_tables.sql`

---

### Phase 2: SDK Authentication (Priority 1) ⭐
**Goal**: SDK uses API keys instead of tenant_id

#### SDK Changes
```python
# OLD (tenant-based)
llmobserve.init(tenant_id="acme-corp")

# NEW (API key-based)
llmobserve.init(api_key="llmo_sk_1234567890abcdef")
# Or via environment variable
export LLMOBSERVE_API_KEY="llmo_sk_1234567890abcdef"
```

#### Implementation
- [ ] Update `sdk/python/llmobserve/config.py`:
  - Remove `tenant_id` configuration
  - Add `api_key` configuration
  - Add `LLMOBSERVE_API_KEY` env var support
- [ ] Update `sdk/python/llmobserve/transport.py`:
  - Add `Authorization: Bearer {api_key}` header to all requests
  - Remove `tenant_id` from request bodies
- [ ] Update `sdk/python/llmobserve/context.py`:
  - Remove `tenant_id` context var
  - Keep `customer_id` (now represents user's end-customers)
- [ ] Update all event emission to use API key auth

---

### Phase 3: Database Migration (Priority 1) ⭐
**Goal**: Move from SQLite to PostgreSQL

#### Setup
- [ ] Create Supabase project OR Neon database
- [ ] Get connection string
- [ ] Update `collector/db.py` to use PostgreSQL
- [ ] Create migration scripts

#### Schema Changes
```sql
-- New tables
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    subscription_tier VARCHAR(50) DEFAULT 'free'
);

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    revoked_at TIMESTAMP,
    INDEX idx_key_hash (key_hash),
    INDEX idx_user_id (user_id)
);

-- Update existing table
ALTER TABLE trace_events 
    DROP COLUMN tenant_id,
    ADD COLUMN user_id UUID REFERENCES users(id) ON DELETE CASCADE;

-- Keep customer_id (this represents the user's end-customers)
-- No change needed for customer_id
```

---

### Phase 4: Onboarding Flow (Priority 2)
**Goal**: Seamless user experience from signup to first data

#### Frontend Pages
1. **Sign Up** (`/sign-up`)
   - Email + password (via Clerk/Auth)
   - Redirects to onboarding

2. **Onboarding** (`/onboarding`)
   - Step 1: Welcome
   - Step 2: Generate API key
   - Step 3: Installation instructions
   - Step 4: Test connection

3. **Dashboard** (`/`)
   - Empty state if no data yet
   - "Getting Started" guide
   - Link to docs

#### Onboarding Component
```tsx
// /app/onboarding/page.tsx
- Generate API key automatically on first login
- Show installation instructions:
  ```bash
  pip install llmobserve
  export LLMOBSERVE_API_KEY="llmo_sk_..."
  ```
- Show simple test script
- Verify connection (ping endpoint)
```

---

### Phase 5: API Key Management (Priority 2)
**Goal**: Users can manage multiple API keys

#### Features
- [ ] Generate new API key with custom name
- [ ] List all API keys (show prefix only, not full key)
- [ ] Show last used timestamp
- [ ] Revoke/delete API keys
- [ ] Copy to clipboard functionality

#### UI Design
```
Settings > API Keys

┌─────────────────────────────────────────────────┐
│ API Keys                            [+ New Key] │
├─────────────────────────────────────────────────┤
│ Production Key                                  │
│ llmo_sk_abc...xyz                               │
│ Created: Jan 1, 2024 • Last used: 2 hours ago │
│                                [Copy]  [Revoke] │
├─────────────────────────────────────────────────┤
│ Development Key                                 │
│ llmo_sk_def...123                               │
│ Created: Dec 15, 2023 • Last used: 5 days ago │
│                                [Copy]  [Revoke] │
└─────────────────────────────────────────────────┘
```

---

### Phase 6: Deployment (Priority 1) ⭐
**Goal**: Production-ready hosting

#### Frontend (Vercel)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd web
vercel

# Set environment variables in Vercel dashboard:
NEXT_PUBLIC_COLLECTOR_URL=https://api.llmobserve.com
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
CLERK_SECRET_KEY=sk_...
```

#### Backend (Railway or Render)
```bash
# Option 1: Railway
railway login
railway init
railway add
railway up

# Option 2: Render
# Connect GitHub repo
# Add web service
# Set environment variables:
DATABASE_URL=postgresql://...
SECRET_KEY=...
```

#### Database (Supabase)
- Create project at supabase.com
- Copy connection string
- Run migrations
- Enable Row Level Security (RLS)

#### Custom Domain
- Frontend: `app.llmobserve.com` (Vercel)
- Backend API: `api.llmobserve.com` (Railway/Render)
- Docs: `docs.llmobserve.com` (Vercel or GitBook)

---

### Phase 7: SDK Publishing (Priority 2)
**Goal**: Users can `pip install llmobserve` directly

#### PyPI Setup
```bash
cd sdk/python

# Update pyproject.toml
[project]
name = "llmobserve"
version = "0.1.0"
description = "LLM cost observability SDK"
authors = [{name = "Your Name", email = "you@llmobserve.com"}]

# Build and publish
python -m build
twine upload dist/*
```

#### Usage
```python
# Users install
pip install llmobserve

# Configure
import llmobserve
llmobserve.init(
    api_key="llmo_sk_...",  # Or from env var
    collector_url="https://api.llmobserve.com"  # Default
)

# Auto-instrument
import openai
# All OpenAI calls now tracked automatically!
```

---

### Phase 8: Documentation (Priority 2)
**Goal**: Users can self-serve

#### Docs Site Structure
```
docs.llmobserve.com/
├── Getting Started
│   ├── Sign Up
│   ├── Installation
│   ├── Quick Start
│   └── First API Call
├── SDK Reference
│   ├── Configuration
│   ├── OpenAI Integration
│   ├── Pinecone Integration
│   ├── Custom Sections
│   └── Customer Tracking
├── Dashboard
│   ├── Overview
│   ├── Runs
│   ├── Costs Analysis
│   └── Agents
└── API Reference
    ├── Authentication
    ├── Events API
    └── Runs API
```

---

### Phase 9: Pricing & Billing (Priority 3)
**Goal**: Monetize the platform

#### Tiers
```
Free Tier:
- 10K events/month
- 7 days retention
- 1 user

Pro Tier ($29/month):
- 1M events/month
- 90 days retention
- 5 users
- Email support

Enterprise ($Custom):
- Unlimited events
- Custom retention
- Unlimited users
- Priority support
- On-prem option
```

#### Implementation
- [ ] Integrate Stripe
- [ ] Add subscription management
- [ ] Add usage tracking/limits
- [ ] Add billing page
- [ ] Email notifications for limits

---

## 🚀 Quick Start Implementation Order

### Week 1: Core Authentication
1. ✅ Add Clerk to Next.js
2. ✅ Add protected routes
3. ✅ PostgreSQL setup (Supabase)
4. ✅ Database migration (remove tenant_id, add user_id)
5. ✅ API key generation endpoints

### Week 2: SDK & Backend
1. ✅ Update SDK to use API keys
2. ✅ Update backend auth middleware
3. ✅ Test end-to-end flow
4. ✅ Update test scripts

### Week 3: Polish & Deploy
1. ✅ Onboarding flow
2. ✅ API key management UI
3. ✅ Deploy to Vercel + Railway
4. ✅ Custom domain setup

### Week 4: Launch Prep
1. ✅ Documentation
2. ✅ Publish SDK to PyPI
3. ✅ Beta testing
4. ✅ Launch! 🎉

---

## 🔧 Technical Decisions

### Authentication: Clerk (Recommended)
**Pros:**
- Drop-in solution
- Beautiful UI components
- User management built-in
- Webhooks for user sync
- Free tier: 10K MAU

**Alternative:** NextAuth.js (more customizable, but more work)

### Database: Supabase (Recommended)
**Pros:**
- PostgreSQL with great DX
- Built-in Auth (if not using Clerk)
- Realtime subscriptions
- Free tier: 500MB, 2GB bandwidth
- Auto-backup

**Alternative:** Neon (serverless Postgres)

### Backend Hosting: Railway (Recommended)
**Pros:**
- Simple GitHub integration
- Automatic deploys
- Free $5/month credit
- PostgreSQL included

**Alternative:** Render (similar features)

---

## 📊 Success Metrics

### Launch Goals (Month 1)
- [ ] 100 sign-ups
- [ ] 50 active users
- [ ] 1M events tracked
- [ ] $0 infra costs (free tiers)

### Growth Goals (Month 3)
- [ ] 1,000 sign-ups
- [ ] 500 active users
- [ ] 10M events tracked
- [ ] 10 paying customers ($290 MRR)

---

## 🎯 Next Steps

**IMMEDIATE (Do Now):**
1. Choose auth provider (Clerk recommended)
2. Create Supabase account
3. Start with Phase 1: Authentication

**Questions to Answer:**
1. Do you want built-in billing from day 1? (Recommend: yes, even if free tier only)
2. Custom domain ready? (Recommend: get `llmobserve.com` or similar)
3. Target launch date? (Recommend: 3-4 weeks)

Ready to start? I'll implement Phase 1 (Authentication) first! 🚀

