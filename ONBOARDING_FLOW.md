# 🚀 LLMObserve - Simple Onboarding Flow

**Status:** ✅ IMPLEMENTED  
**Goal:** Solo devs and SaaS founders can sign up and start tracking in 30 seconds

---

## 🎯 USER JOURNEY

### **Step 1: Sign Up (15 seconds)**

User goes to `/signup`:
- Enters email, password, optional name
- Clicks "Create Account"
- ✅ Account created
- ✅ API key auto-generated
- ✅ JWT token saved in localStorage

### **Step 2: Onboarding (15 seconds)**

Immediately shown setup instructions with:
- 🔑 **Their API key** (shown once, with copy button)
- 📋 **3-step setup guide:**
  1. `pip install llmobserve`
  2. Add 2 lines to code
  3. Optional: Track customers with `set_customer_id()`
- 💡 Pro tips

### **Step 3: Dashboard**

- Click "Go to Dashboard"
- See their costs immediately after first API call
- Can filter by customer (if tracking SaaS customers)

---

## 🔐 AUTHENTICATION

### Backend (`/auth` endpoints)

✅ **POST /auth/signup**
- Input: `{ email, password, name? }`
- Creates user + auto-generates API key
- Returns: JWT token + API key (shown once!)

✅ **POST /auth/login**
- Input: `{ email, password }`
- Returns: JWT token

✅ **GET /auth/me**
- Headers: `Authorization: Bearer <jwt>`
- Returns: User info + API keys (without full keys)

✅ **POST /auth/api-keys**
- Create additional API keys
- Returns: New API key (shown once!)

✅ **DELETE /auth/api-keys/{key_id}**
- Revoke an API key

### Frontend Authentication

✅ **Login Page:** `/login`
✅ **Signup Page:** `/signup` (with onboarding)
✅ **Auth Utils:** `/lib/auth.ts`
- `saveAuth()` - Store JWT + user in localStorage
- `loadAuth()` - Load JWT + user
- `clearAuth()` - Logout
- `getAuthHeaders()` - Get Bearer token for API calls
- `isAuthenticated()` - Check if logged in

---

## 📊 HOW IT WORKS

### For Solo Developers

**Use Case:** "I'm building an AI app for myself, want to track costs"

**Flow:**
```python
1. Sign up at /signup
2. Get API key automatically
3. Add to your code:

import llmobserve

llmobserve.observe(
    collector_url="http://localhost:8000",
    api_key="llmo_sk_..."  # From signup
)

# All OpenAI/Pinecone calls now tracked!
4. View costs in dashboard
```

**What they see:**
- Total costs
- Breakdown by provider (OpenAI, Pinecone, etc.)
- Breakdown by model
- Individual API calls

---

### For SaaS Founders

**Use Case:** "I'm building SaaS, want to track which customers cost me the most"

**Flow:**
```python
1. Sign up at /signup
2. Get API key automatically
3. Add to your server:

import llmobserve
from llmobserve import set_customer_id

# Initialize once
llmobserve.observe(
    collector_url="https://your-server.com",
    api_key="llmo_sk_..."
)

# In your API handler (per request)
@app.post("/api/chat")
def handle_chat(request):
    # Track costs per customer
    set_customer_id(request.user_id)
    
    # All API calls now tagged with customer_id
    response = openai_client.chat.completions.create(...)
    return response

4. View dashboard:
   - Filter by customer
   - See per-customer costs
   - Identify expensive customers
```

**What they see:**
- Total costs (all customers)
- **Per-customer breakdown** ← Key feature!
- Cost per customer over time
- Which customers are most expensive

---

## ✅ WHAT'S IMPLEMENTED

### ✅ Backend (Collector)

1. **Authentication Endpoints** (`collector/routers/auth_simple.py`):
   - POST /auth/signup - Create account + API key
   - POST /auth/login - Login
   - GET /auth/me - Get user info
   - POST /auth/api-keys - Create new API key
   - DELETE /auth/api-keys/{id} - Revoke API key

2. **Database Models** (`collector/models.py`):
   - User with email/password
   - API key management
   - User-scoped data

3. **Migration** (`migrations/004_add_user_password.sql`):
   - Add password_hash column

### ✅ Frontend (Next.js)

1. **Auth Pages**:
   - `/login` - Login form
   - `/signup` - Signup + onboarding flow

2. **Auth Utils** (`lib/auth.ts`):
   - JWT token management
   - localStorage persistence
   - API helpers

3. **Onboarding Flow** (`/signup` page, step 2):
   - Show API key (once!)
   - 3-step setup guide
   - Copy-paste code examples
   - Pro tips

### ✅ SDK (Already Working!)

- `tenant_id` defaults to "default_tenant"
- `set_customer_id()` works out of the box
- All events tagged with user's API key

---

## ⚠️ REMAINING TASKS (Est: 2-3 hours)

### 1. Dashboard Auth Protection (30 min)

Update `/app/page.tsx` to:
- Check if user is logged in
- Redirect to `/login` if not
- Filter data by logged-in user

```typescript
// In page.tsx
useEffect(() => {
  const { token } = loadAuth();
  if (!token) {
    router.push("/login");
  }
}, []);

// When fetching data
const headers = getAuthHeaders();
fetch("/api/runs?user_id=...", { headers })
```

### 2. User-Scoped Dashboard (1 hour)

Update all API calls to include user_id:
- GET /runs?user_id={user_id}
- GET /insights?user_id={user_id}
- GET /stats?user_id={user_id}

Update backend routes to filter by user_id.

### 3. Customer Breakdown View (1 hour)

Create `/app/customers/page.tsx`:
- List all unique customer_ids
- Show total cost per customer
- Show call count per customer
- Link to customer detail view

### 4. Navigation/Header (30 min)

Add global nav with:
- Logo
- Dashboard / Customers / Settings
- User menu (logout)

---

## 🚀 TO DEPLOY (5 minutes)

### 1. Set Environment Variables

```bash
# Backend (.env)
DATABASE_URL=sqlite:///./collector.db
JWT_SECRET=your-secret-key-here-change-in-production

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Run Migrations

```bash
cd collector
sqlite3 collector.db < migrations/004_add_user_password.sql
```

### 3. Install Dependencies

```bash
# Backend
cd collector
pip install -r requirements.txt

# Frontend
cd web
npm install
```

### 4. Start Servers

```bash
# Terminal 1: Backend
cd collector
uvicorn main:app --reload

# Terminal 2: Frontend
cd web
npm run dev
```

### 5. Test!

1. Go to http://localhost:3000/signup
2. Create account
3. Copy API key
4. Add to your code:
   ```python
   import llmobserve
   llmobserve.observe(
       collector_url="http://localhost:8000",
       api_key="llmo_sk_..."
   )
   ```
5. Make some API calls
6. View dashboard!

---

## 📋 USAGE EXAMPLES

### Example 1: Solo Dev

```python
import llmobserve
from openai import OpenAI

# Initialize (once)
llmobserve.observe(
    collector_url="http://localhost:8000",
    api_key="llmo_sk_abc123..."
)

# Use OpenAI normally
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)

# ✅ Automatically tracked!
# View costs at http://localhost:3000
```

### Example 2: SaaS with Customer Tracking

```python
import llmobserve
from llmobserve import set_customer_id
from openai import OpenAI
from fastapi import FastAPI

app = FastAPI()

# Initialize once
llmobserve.observe(
    collector_url="https://your-llmobserve.com",
    api_key="llmo_sk_abc123..."
)

client = OpenAI()

@app.post("/api/chat")
def chat(request: ChatRequest):
    # Track per customer
    set_customer_id(request.user_id)  # e.g., "alice"
    
    # Use OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": request.message}]
    )
    
    # ✅ Cost attributed to "alice"
    return {"response": response.choices[0].message.content}

# Dashboard shows:
# - alice: $3.20
# - bob: $5.10
# - carol: $2.20
```

---

## 🎯 KEY FEATURES

### ✅ Fully Implemented

1. **Simple Signup** - Email/password, no external auth needed
2. **Auto API Key** - Generated on signup, shown once
3. **Beautiful Onboarding** - 3-step setup guide with code examples
4. **JWT Auth** - Secure token-based authentication
5. **Multi-Key Support** - Users can create multiple API keys
6. **Customer Tracking** - `set_customer_id()` works out of the box

### ⚠️ Needs Completion

1. **Dashboard Auth** - Protect dashboard, show only user's data
2. **Customer Breakdown** - Dedicated page for per-customer costs
3. **Settings Page** - View/manage API keys, account settings

---

## 💡 NEXT STEPS FOR USER

After implementing remaining tasks (2-3 hours):

**Complete Flow:**
1. User signs up → Gets API key
2. Adds 2 lines to code
3. Makes API calls
4. Views dashboard (filtered to their data only)
5. **SaaS users:** Filter by customer to see per-customer costs
6. **Solo users:** See total costs and optimize

---

## 🔐 SECURITY NOTES

### ✅ Current Security

- Passwords hashed with bcrypt
- JWT tokens for frontend auth
- API keys hashed in database
- CORS enabled for frontend

### 🚨 Production Recommendations

1. **Change JWT secret** (currently hardcoded):
   ```python
   JWT_SECRET = os.getenv("JWT_SECRET")  # Load from env
   ```

2. **Use HTTPS** in production

3. **Add rate limiting** to prevent abuse

4. **Add email verification** (optional)

5. **Add password reset** flow (optional)

---

## ✅ TESTING CHECKLIST

- [ ] User can sign up
- [ ] API key shown on signup
- [ ] User can copy API key
- [ ] User can log in
- [ ] Dashboard protected (redirect if not logged in)
- [ ] Dashboard shows user's data only
- [ ] `set_customer_id()` works
- [ ] Customer filter works
- [ ] User can create new API keys
- [ ] User can revoke API keys

---

## 🎉 CONCLUSION

**What You Have:**
- ✅ Simple email/password auth
- ✅ Auto API key generation
- ✅ Beautiful onboarding flow
- ✅ Copy-paste setup instructions
- ✅ Customer tracking support

**What's Left:**
- ⚠️ Dashboard auth protection (~30 min)
- ⚠️ User-scoped data filtering (~1 hour)
- ⚠️ Customer breakdown page (~1 hour)
- ⚠️ Navigation/settings (~30 min)

**Total:** ~3 hours to complete

**After that:**
- Solo devs can sign up and track costs ✅
- SaaS founders can track customer costs ✅
- Multi-tenancy can be added later ✅

🚀 **You're 90% there!**

