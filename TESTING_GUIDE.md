# 🧪 Complete Testing Guide for LLMObserve

## 📋 What You Need to Test

### 1. **LLMObserve API Keys** (Platform Authentication)
- **What**: Authentication keys for the LLMObserve platform
- **Where to get**: http://localhost:3000/settings → "Create API Key"
- **Format**: `llmo_sk_...`
- **Purpose**: Links tracked costs to your account
- **For multi-user testing**: Create 2+ accounts or API keys

### 2. **Provider API Keys** (LLM Service Keys)
- **OpenAI API Key**: `sk-proj-...` or `sk-...` (for GPT models)
- **Anthropic API Key**: `sk-ant-...` (for Claude models) - Optional
- **Purpose**: Actual API keys to make LLM calls
- **Note**: These are YOUR keys - the platform tracks costs but doesn't store them

### 3. **Running Services**
- ✅ Collector API: http://localhost:8000 (already running)
- ✅ Web Dashboard: http://localhost:3000 (already running)

---

## 🎯 Testing Scenarios

### Scenario 1: Single User, Single Provider (OpenAI)
**Goal**: Verify basic tracking works

**What you need**:
- 1 LLMObserve API key
- 1 OpenAI API key

**Test**:
```bash
export LLMOBSERVE_API_KEY_USER1="llmo_sk_YOUR_KEY"
export OPENAI_API_KEY="sk-proj-YOUR_OPENAI_KEY"
python3 test_multi_user.py
```

**Expected Results**:
- Dashboard shows costs
- Customer page shows customer_a, customer_b, customer_c
- Features page shows agents: user1_chatbot, user1_processor, user1_batch

---

### Scenario 2: Multiple Users, Data Isolation
**Goal**: Verify users can't see each other's data

**What you need**:
- 2 LLMObserve API keys (from 2 different accounts)
- 1 OpenAI API key (shared - that's fine)

**Steps**:
1. **Create Account 1**:
   - Go to http://localhost:3000/sign-up
   - Sign up → Get API key → Save it
   
2. **Create Account 2**:
   - Open incognito window
   - Go to http://localhost:3000/sign-up
   - Sign up → Get API key → Save it

3. **Run tests**:
```bash
export LLMOBSERVE_API_KEY_USER1="llmo_sk_KEY_FROM_ACCOUNT_1"
export LLMOBSERVE_API_KEY_USER2="llmo_sk_KEY_FROM_ACCOUNT_2"
export OPENAI_API_KEY="sk-proj-YOUR_OPENAI_KEY"
python3 test_multi_user.py
```

4. **Verify Isolation**:
   - Login as Account 1 → Should only see User 1's data
   - Login as Account 2 → Should only see User 2's data
   - No cross-contamination ✅

---

### Scenario 3: Multiple Providers (OpenAI + Anthropic)
**Goal**: Verify tracking works with different LLM providers

**What you need**:
- 1 LLMObserve API key
- 1 OpenAI API key
- 1 Anthropic API key

**Test**:
```bash
export LLMOBSERVE_API_KEY_USER1="llmo_sk_YOUR_KEY"
export OPENAI_API_KEY="sk-proj-YOUR_OPENAI_KEY"
export ANTHROPIC_API_KEY="sk-ant-YOUR_ANTHROPIC_KEY"
python3 test_multi_user.py
```

**Expected Results**:
- Dashboard shows costs from both OpenAI and Anthropic
- Provider breakdown shows both providers
- Model breakdown shows: gpt-4o-mini, gpt-3.5-turbo, claude-3-haiku

---

### Scenario 4: Customer Tracking (SaaS Use Case)
**Goal**: Verify per-customer cost tracking

**What you need**:
- 1 LLMObserve API key
- 1 OpenAI API key

**Test**: The script already tests this with `set_customer_id()`

**Expected Results**:
- Customers page shows: customer_a, customer_b, customer_c
- Each customer has separate cost breakdown
- Can filter dashboard by customer

---

## 🚀 Quick Start Testing

### Step 1: Get Your LLMObserve API Key

1. Go to http://localhost:3000
2. Sign up (or sign in if you already have an account)
3. Go to Settings → API Keys
4. Click "Create API Key"
5. **Copy the key immediately** (shown only once!)

### Step 2: Set Environment Variables

```bash
# Required
export LLMOBSERVE_API_KEY_USER1="llmo_sk_YOUR_KEY_HERE"
export OPENAI_API_KEY="sk-proj-YOUR_OPENAI_KEY"

# Optional (for multi-user testing)
export LLMOBSERVE_API_KEY_USER2="llmo_sk_ANOTHER_KEY"

# Optional (for Anthropic testing)
export ANTHROPIC_API_KEY="sk-ant-YOUR_ANTHROPIC_KEY"
```

### Step 3: Run Tests

```bash
# Install dependencies if needed
pip install llmobserve openai anthropic python-dotenv

# Run the test script
python3 test_multi_user.py
```

### Step 4: Verify Results

1. **Dashboard**: http://localhost:3000/dashboard
   - Should show total costs
   - Should show recent API calls
   - Should show provider breakdown

2. **Customers**: http://localhost:3000/customers
   - Should show customer breakdown
   - Each customer has separate costs

3. **Features**: http://localhost:3000/features
   - Should show agent/section breakdown
   - Hierarchical view of costs

---

## 🔍 What Gets Tracked

### Automatically Tracked:
- ✅ Provider (OpenAI, Anthropic, etc.)
- ✅ Model name (gpt-4o-mini, claude-3-haiku, etc.)
- ✅ Input/output tokens
- ✅ Cost (calculated from pricing database)
- ✅ Latency
- ✅ Status (success/error)

### With Labeling:
- ✅ Agent names (`agent:chatbot`)
- ✅ Section hierarchy (`agent:chatbot/tool:search`)
- ✅ Customer IDs (`customer_123`)

---

## 📊 Expected Dashboard Data

After running `test_multi_user.py`, you should see:

### Dashboard View:
- **Total Cost**: Sum of all API calls
- **Total Calls**: Number of API requests
- **Providers**: OpenAI (and Anthropic if tested)
- **Models**: gpt-4o-mini, gpt-3.5-turbo (and claude models if tested)

### Customers View:
- customer_a: 1 call
- customer_b: 1 call  
- customer_c: 3 calls
- customer_x: 1 call (if User 2 tested)
- customer_y: 1 call (if User 2 tested)

### Features View:
- agent:user1_chatbot
- agent:user1_processor
- agent:user1_batch
- agent:user2_researcher (if User 2 tested)
- agent:user2_analyzer (if User 2 tested)

---

## 🐛 Troubleshooting

### "No data showing in dashboard"
- Wait 2-3 seconds for events to flush
- Hard refresh (Cmd+Shift+R)
- Check collector logs: `tail -f logs/collector.log`

### "Authentication failed"
- Verify your LLMObserve API key is correct
- Check it starts with `llmo_sk_`
- Make sure you're using the key from the correct account

### "OpenAI API error"
- Verify your OpenAI API key is valid
- Check you have credits/quota
- Try a simple test: `curl https://api.openai.com/v1/models -H "Authorization: Bearer YOUR_KEY"`

### "Anthropic not tracking"
- Install SDK: `pip install anthropic`
- Verify API key format: `sk-ant-...`
- Check Anthropic account has credits

---

## ✅ Success Criteria

Your platform is working correctly if:

1. ✅ **Single User Tracking**: Costs appear in dashboard
2. ✅ **Multi-User Isolation**: User 1 can't see User 2's data
3. ✅ **Multiple Providers**: Both OpenAI and Anthropic costs tracked
4. ✅ **Customer Tracking**: Per-customer breakdown works
5. ✅ **Agent Labeling**: Section hierarchy appears correctly
6. ✅ **Real-time Updates**: Dashboard refreshes with new data

---

## 📝 Notes

- **Provider API keys** (OpenAI, Anthropic) are YOUR keys - the platform doesn't store them
- **LLMObserve API keys** authenticate with the platform and link costs to your account
- Multiple users can use the same provider API key (OpenAI) - costs are tracked separately
- Data isolation is enforced by `user_id` in the database
- All costs are calculated server-side using the pricing database





