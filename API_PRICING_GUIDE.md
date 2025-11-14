# 🎯 API Pricing Guide - What to Test Next

## ✅ Already Configured (174 pricing entries, 37 providers)

You already have pricing for:
- **LLMs**: OpenAI, Anthropic, Google, Cohere, Mistral, Groq, AI21, Together, Perplexity, Azure OpenAI, AWS Bedrock
- **Voice AI**: ElevenLabs, AssemblyAI, Deepgram, PlayHT, Azure Speech, AWS Polly, AWS Transcribe
- **Vector DBs**: Pinecone, Weaviate, Qdrant, Milvus, Chroma, MongoDB, Redis, Elasticsearch
- **Payments**: Stripe, PayPal
- **Communication**: Twilio, SendGrid
- **Images**: Stability AI, Runway, AWS Rekognition
- **Search**: Algolia

## 🧪 APIs You Can Test RIGHT NOW (Already Have Pricing)

### 1. **Anthropic Claude** (Easy to test)
**Status:** ✅ Pricing configured  
**Test:** https://www.anthropic.com/api  
**Pricing Source:** https://www.anthropic.com/pricing

```python
from anthropic import Anthropic
from llmobserve import observe, section

observe(collector_url="http://localhost:8000", proxy_url="http://localhost:9000", api_key="your_key")

client = Anthropic(api_key="your_anthropic_key")
with section("test:claude"):
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=100,
        messages=[{"role": "user", "content": "Hello"}]
    )
```

### 2. **Google Gemini** (Easy to test)
**Status:** ✅ Pricing configured  
**Test:** https://ai.google.dev/  
**Pricing Source:** https://ai.google.dev/pricing

```python
import google.generativeai as genai
from llmobserve import observe, section

observe(collector_url="http://localhost:8000", proxy_url="http://localhost:9000", api_key="your_key")

genai.configure(api_key="your_google_key")
with section("test:gemini"):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello")
```

### 3. **Stripe** (Easy to test - use test mode)
**Status:** ✅ Pricing configured  
**Test:** https://stripe.com/docs/testing  
**Pricing Source:** https://stripe.com/pricing

```python
import stripe
from llmobserve import observe, section

observe(collector_url="http://localhost:8000", proxy_url="http://localhost:9000", api_key="your_key")

stripe.api_key = "sk_test_your_key"  # Use test key
with section("test:stripe"):
    charge = stripe.Charge.create(
        amount=1000,
        currency="usd",
        source="tok_visa"  # Test token
    )
```

### 4. **Twilio** (Easy to test - use test credentials)
**Status:** ✅ Pricing configured  
**Test:** https://www.twilio.com/docs/usage  
**Pricing Source:** https://www.twilio.com/pricing

```python
from twilio.rest import Client
from llmobserve import observe, section

observe(collector_url="http://localhost:8000", proxy_url="http://localhost:9000", api_key="your_key")

client = Client("your_account_sid", "your_auth_token")
with section("test:twilio"):
    message = client.messages.create(
        body="Test",
        from_="+1234567890",
        to="+1234567890"
    )
```

### 5. **Pinecone** (If you have an account)
**Status:** ✅ Pricing configured  
**Test:** https://www.pinecone.io/learn/quickstart/  
**Pricing Source:** https://www.pinecone.io/pricing/

```python
from pinecone import Pinecone
from llmobserve import observe, section

observe(collector_url="http://localhost:8000", proxy_url="http://localhost:9000", api_key="your_key")

pc = Pinecone(api_key="your_pinecone_key")
with section("test:pinecone"):
    indexes = pc.list_indexes()
```

## 🔍 APIs Missing Pricing (Need to Add)

### Priority 1: Most Common APIs

#### **Supabase** (You're already using it!)
**Why:** You're making Supabase calls but they show $0.00  
**Pricing Source:** https://supabase.com/pricing  
**How to add:**
```sql
-- Supabase REST API calls (free tier)
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES (
  'supabase',
  'rest_api',
  'per_call',
  '{"per_call": 0.0}'::jsonb,
  'Supabase REST API (free tier)',
  'https://supabase.com/pricing',
  true,
  NOW()
);
```

#### **HTTPBin** (Testing API)
**Why:** You tested it but it shows $0.00  
**Pricing:** Free (no cost)  
**How to add:**
```sql
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES (
  'httpbin',
  'json',
  'per_call',
  '{"per_call": 0.0}'::jsonb,
  'HTTPBin test API (free)',
  'https://httpbin.org/',
  true,
  NOW()
);
```

### Priority 2: Popular APIs You Might Use

#### **Cohere** (LLM)
**Status:** ⚠️ Pricing configured but might need updates  
**Pricing Source:** https://cohere.com/pricing  
**Test:** https://cohere.com/docs

#### **Mistral** (LLM)
**Status:** ⚠️ Pricing configured but might need updates  
**Pricing Source:** https://mistral.ai/pricing/  
**Test:** https://docs.mistral.ai/

#### **Groq** (Fast LLM)
**Status:** ⚠️ Pricing configured but might need updates  
**Pricing Source:** https://groq.com/pricing/  
**Test:** https://console.groq.com/

## 📚 Where to Find Pricing

### Official Pricing Pages:

1. **LLMs:**
   - OpenAI: https://openai.com/api/pricing/
   - Anthropic: https://www.anthropic.com/pricing
   - Google: https://ai.google.dev/pricing
   - Cohere: https://cohere.com/pricing
   - Mistral: https://mistral.ai/pricing/
   - Groq: https://groq.com/pricing/

2. **Vector DBs:**
   - Pinecone: https://www.pinecone.io/pricing/
   - Weaviate: https://weaviate.io/pricing
   - Qdrant: https://qdrant.tech/pricing/
   - Chroma: https://www.trychroma.com/pricing

3. **Payments:**
   - Stripe: https://stripe.com/pricing
   - PayPal: https://www.paypal.com/us/webapps/mpp/merchant-fees

4. **Communication:**
   - Twilio: https://www.twilio.com/pricing
   - SendGrid: https://sendgrid.com/pricing/

5. **Databases:**
   - Supabase: https://supabase.com/pricing
   - MongoDB Atlas: https://www.mongodb.com/pricing

## 🚀 Quick Start: Test These APIs

### Step 1: Pick an API from the list above

### Step 2: Get API Key
- Sign up for free tier (most APIs have one)
- Get your API key from dashboard

### Step 3: Add Pricing to Supabase
```sql
-- Example: Add Supabase pricing
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES (
  'supabase',
  'rest_api',
  'per_call',
  '{"per_call": 0.0}'::jsonb,
  'Supabase REST API calls',
  'https://supabase.com/pricing',
  true,
  NOW()
);
```

### Step 4: Test It!
```python
from llmobserve import observe, section
import httpx

observe(
    collector_url="http://localhost:8000",
    proxy_url="http://localhost:9000",
    api_key="your_llmobserve_key"
)

with section("test:supabase"):
    response = httpx.get(
        "https://your-project.supabase.co/rest/v1/",
        headers={"apikey": "your_supabase_key"}
    )
```

## 🎯 Recommended Testing Order

1. **Supabase** (You're already using it - add pricing!)
2. **Anthropic Claude** (Easy, free tier available)
3. **Google Gemini** (Easy, free tier available)
4. **Stripe** (Use test mode - no real charges)
5. **Twilio** (Use test credentials)

## 💡 Pro Tips

1. **Start with free tiers** - Most APIs have free tiers for testing
2. **Use test mode** - Stripe, Twilio have test modes
3. **Check pricing pages** - Always verify current pricing
4. **Add as you go** - Don't add everything at once
5. **Document sources** - Always include the pricing URL

## 📝 Adding Pricing Format

```sql
INSERT INTO pricing (
  provider,           -- e.g., 'supabase', 'stripe', 'openai'
  model,              -- e.g., 'rest_api', 'charges.create', 'gpt-4o' (or NULL for provider-level)
  pricing_type,       -- 'token_based', 'per_call', 'per_million', 'per_1k_chars', etc.
  pricing_data,       -- JSON with actual pricing values
  description,        -- Human-readable description
  source,             -- URL to pricing page
  is_active,          -- true
  effective_date      -- NOW()
) VALUES (
  'provider_name',
  'model_or_endpoint',
  'pricing_type',
  '{"key": value}'::jsonb,
  'Description',
  'https://pricing-url.com',
  true,
  NOW()
);
```

## 🔗 Quick Links

- **Add pricing via Supabase Dashboard:** Go to your Supabase project → Table Editor → `pricing` table → Insert row
- **Check current pricing:** Run the Python script in the repo to see what's configured
- **Test APIs:** Use the examples above with your API keys

---

**Next Steps:** Pick an API from the list above, get an API key, add pricing to Supabase, and test it! 🚀

