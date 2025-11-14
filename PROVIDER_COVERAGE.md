# Provider Coverage Status

## ✅ Fully Tracked (Cost + Instrumentation)

### 1. **OpenAI** ✅
- **Status:** 100% complete
- **Pricing:** ✅ All models (GPT-4o, GPT-4, GPT-3.5, O1, embeddings, DALL-E, Whisper, TTS, etc.)
- **Instrumentation:** ✅ Direct SDK patching
- **Tested:** ✅ Yes

### 2. **Pinecone** ✅
- **Status:** 100% complete
- **Pricing:** ✅ All operations (upsert, query, fetch, update, delete, storage, embeddings, reranking)
- **Instrumentation:** ✅ Direct SDK patching
- **Tested:** ✅ Yes

---

## ⚠️ Partially Tracked (Instrumentation ✅, Pricing ❌)

These providers have instrumentors that **track API calls** but **don't calculate costs** because pricing is missing:

### 3. **Anthropic (Claude)** ⚠️
- **Status:** Partial
- **Pricing:** ⚠️ Only 2 models (claude-3-opus, claude-3-sonnet) - missing others
- **Instrumentation:** ✅ Direct SDK patching
- **Cost Calculation:** ⚠️ Returns $0.00 for untracked models

### 4. **Google Gemini** ⚠️
- **Status:** Partial
- **Pricing:** ❌ None in registry
- **Instrumentation:** ✅ Direct SDK patching
- **Cost Calculation:** ❌ Returns $0.00

### 5. **Cohere** ⚠️
- **Status:** Partial
- **Pricing:** ❌ None in registry
- **Instrumentation:** ✅ Direct SDK patching
- **Cost Calculation:** ❌ Returns $0.00

### 6. **ElevenLabs** ⚠️
- **Status:** Partial
- **Pricing:** ❌ None in registry
- **Instrumentation:** ✅ Direct SDK patching
- **Cost Calculation:** ❌ Returns $0.00

### 7. **Voyage AI** ⚠️
- **Status:** Partial
- **Pricing:** ⚠️ Hardcoded in instrumentor (not in registry)
- **Instrumentation:** ✅ Direct SDK patching
- **Cost Calculation:** ⚠️ Works but not centralized

### 8. **Stripe** ⚠️
- **Status:** Partial
- **Pricing:** ❌ None in registry
- **Instrumentation:** ✅ Direct SDK patching
- **Cost Calculation:** ❌ Returns $0.00

### 9. **Twilio** ⚠️
- **Status:** Partial
- **Pricing:** ❌ None in registry
- **Instrumentation:** ✅ Direct SDK patching
- **Cost Calculation:** ❌ Returns $0.00

---

## 🔄 Proxy-Only (No Direct Instrumentation)

These providers are **only tracked via HTTP proxy** (if proxy is enabled):

- Mistral
- Groq
- AI21
- HuggingFace
- Together AI
- Replicate
- Perplexity
- Azure OpenAI
- AWS Bedrock
- AssemblyAI
- Deepgram
- Play.ht
- Azure Speech
- AWS Polly
- AWS Transcribe
- Stability AI
- Runway
- AWS Rekognition
- Weaviate
- Qdrant
- Milvus
- Chroma
- MongoDB Vector
- Redis Vector
- Elasticsearch Vector
- Algolia
- PayPal
- SendGrid

**Note:** Proxy requires `proxy_url` to be set. Without proxy, these are **NOT tracked**.

---

## 📊 Summary

| Category | Count | Status |
|----------|-------|--------|
| **Fully Tracked** | 2 | OpenAI, Pinecone |
| **Partially Tracked** | 7 | Anthropic, Google, Cohere, ElevenLabs, Voyage, Stripe, Twilio |
| **Proxy-Only** | 28+ | Various (requires proxy) |
| **Total** | 37+ | Mixed |

---

## 🎯 What This Means

**For Cost Tracking:**
- ✅ **OpenAI** - Full cost tracking
- ✅ **Pinecone** - Full cost tracking
- ⚠️ **Anthropic** - Partial (only 2 models)
- ❌ **Others** - API calls tracked, but costs = $0.00

**For API Call Tracking:**
- ✅ **9 providers** - Direct instrumentation (calls tracked even without pricing)
- ✅ **28+ providers** - Via proxy (if proxy enabled)

---

## 🚀 To Fix

1. **Add pricing to registry** for:
   - Anthropic (all models)
   - Google Gemini
   - Cohere
   - ElevenLabs
   - Stripe
   - Twilio
   - Voyage (move from hardcoded to registry)

2. **Enable proxy** for users who need 28+ other providers

3. **Add more instrumentors** for commonly used providers

