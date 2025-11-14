# 📊 Complete Guide: Adding Accurate API Pricing to Supabase

## Overview

This guide walks you through finding and adding accurate pricing for major APIs (Stripe, LLMs, Pinecone, databases, etc.) to Supabase.

**Important:** We want **100% accuracy** - if pricing isn't known, it shows $0.00 (not a default guess).

---

## Step 1: Understanding the Pricing Table Structure

The `pricing` table in Supabase has these fields:

```sql
- id (UUID) - Auto-generated
- provider (TEXT) - e.g., "openai", "stripe", "pinecone"
- model (TEXT, nullable) - e.g., "gpt-4", "charges.create", "serverless"
- pricing_type (TEXT) - "token_based", "per_call", "per_million", etc.
- pricing_data (JSONB) - The actual pricing structure
- description (TEXT) - Human-readable description
- source (TEXT) - Where you got the pricing from (URL)
- region (TEXT, nullable) - For region-specific pricing
- effective_date (TIMESTAMP) - When pricing became effective
- expires_at (TIMESTAMP, nullable) - When pricing expires (if applicable)
- is_active (BOOLEAN) - Whether this pricing is currently active
```

---

## Step 2: Finding Pricing for Major APIs

### LLM Providers

#### OpenAI
**Source:** https://openai.com/api/pricing/

**Examples:**
```sql
-- GPT-4o
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES (
  'openai',
  'gpt-4o',
  'token_based',
  '{"input": 0.0000025, "output": 0.00001}'::jsonb,
  'GPT-4o pricing per token',
  'https://openai.com/api/pricing/'
);

-- GPT-4 Turbo
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES (
  'openai',
  'gpt-4-turbo',
  'token_based',
  '{"input": 0.00001, "output": 0.00003}'::jsonb,
  'GPT-4 Turbo pricing per token',
  'https://openai.com/api/pricing/'
);

-- GPT-3.5 Turbo
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES (
  'openai',
  'gpt-3.5-turbo',
  'token_based',
  '{"input": 0.0000005, "output": 0.0000015}'::jsonb,
  'GPT-3.5 Turbo pricing per token',
  'https://openai.com/api/pricing/'
);
```

#### Anthropic (Claude)
**Source:** https://www.anthropic.com/pricing

```sql
-- Claude 3.5 Sonnet
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES (
  'anthropic',
  'claude-3-5-sonnet-20241022',
  'token_based',
  '{"input": 0.000003, "output": 0.000015}'::jsonb,
  'Claude 3.5 Sonnet pricing per token',
  'https://www.anthropic.com/pricing'
);

-- Claude 3 Opus
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES (
  'anthropic',
  'claude-3-opus-20240229',
  'token_based',
  '{"input": 0.000015, "output": 0.000075}'::jsonb,
  'Claude 3 Opus pricing per token',
  'https://www.anthropic.com/pricing'
);
```

#### Google (Gemini)
**Source:** https://ai.google.dev/pricing

```sql
-- Gemini 1.5 Pro
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES (
  'google',
  'gemini-1.5-pro',
  'token_based',
  '{"input": 0.00000125, "output": 0.000005}'::jsonb,
  'Gemini 1.5 Pro pricing per token',
  'https://ai.google.dev/pricing'
);
```

### Payment APIs

#### Stripe
**Source:** https://stripe.com/pricing

```sql
-- Charges API
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES (
  'stripe',
  'charges.create',
  'per_call',
  '{"per_call": 0.003}'::jsonb,
  'Stripe charge creation fee (2.9% + $0.30, but we track per-call cost)',
  'https://stripe.com/pricing'
);

-- Subscriptions
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES (
  'stripe',
  'subscriptions.create',
  'per_call',
  '{"per_call": 0.01}'::jsonb,
  'Stripe subscription creation',
  'https://stripe.com/pricing'
);
```

### Vector Databases

#### Pinecone
**Source:** https://www.pinecone.io/pricing/

```sql
-- Serverless (per million vectors)
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES (
  'pinecone',
  'serverless',
  'per_million',
  '{"per_million": 0.096}'::jsonb,
  'Pinecone serverless pricing per million vectors',
  'https://www.pinecone.io/pricing/'
);

-- Standard (per million operations)
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES (
  'pinecone',
  'standard',
  'per_million',
  '{"per_million": 0.096}'::jsonb,
  'Pinecone standard pricing per million operations',
  'https://www.pinecone.io/pricing/'
);
```

#### Weaviate
**Source:** https://weaviate.io/pricing

```sql
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES (
  'weaviate',
  'standard',
  'per_million',
  '{"per_million": 0.10}'::jsonb,
  'Weaviate pricing per million operations',
  'https://weaviate.io/pricing'
);
```

### Communication APIs

#### Twilio
**Source:** https://www.twilio.com/pricing

```sql
-- SMS
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES (
  'twilio',
  'messages.create',
  'per_call',
  '{"per_call": 0.0075}'::jsonb,
  'Twilio SMS pricing per message',
  'https://www.twilio.com/pricing'
);

-- Voice calls
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES (
  'twilio',
  'calls.create',
  'per_minute',
  '{"per_minute": 0.013}'::jsonb,
  'Twilio voice call pricing per minute',
  'https://www.twilio.com/pricing'
);
```

#### SendGrid
**Source:** https://sendgrid.com/pricing/

```sql
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES (
  'sendgrid',
  'mail.send',
  'per_1k_emails',
  '{"per_1k_emails": 0.60}'::jsonb,
  'SendGrid email pricing per 1k emails',
  'https://sendgrid.com/pricing/'
);
```

### Database APIs

#### MongoDB Atlas
**Source:** https://www.mongodb.com/pricing

```sql
-- M0 Free tier (for reference)
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES (
  'mongodb',
  'atlas.m0',
  'per_call',
  '{"per_call": 0.0}'::jsonb,
  'MongoDB Atlas M0 free tier',
  'https://www.mongodb.com/pricing'
);
```

---

## Step 3: Pricing Data Formats

### Token-Based (LLMs)
```json
{
  "input": 0.000001,      // Cost per input token
  "output": 0.000002,    // Cost per output token
  "cached_input": 0.0000001  // Cost per cached input token (optional)
}
```

### Per-Call (Simple APIs)
```json
{
  "per_call": 0.001  // Fixed cost per API call
}
```

### Per Million (Vector DBs, Operations)
```json
{
  "per_million": 0.096  // Cost per million operations
}
```

### Per 1K (Emails, Requests)
```json
{
  "per_1k_emails": 0.60,     // Cost per 1k emails
  "per_1k_requests": 0.005   // Cost per 1k requests
}
```

### Per Minute (Voice, Audio)
```json
{
  "per_minute": 0.006  // Cost per minute
}
```

### Character-Based (TTS)
```json
{
  "per_1k_chars": 0.015  // Cost per 1k characters
}
```

---

## Step 4: Adding Pricing via SQL

### Method 1: Direct SQL Insert

```sql
INSERT INTO pricing (
  provider,
  model,
  pricing_type,
  pricing_data,
  description,
  source,
  is_active,
  effective_date
) VALUES (
  'openai',
  'gpt-4o',
  'token_based',
  '{"input": 0.0000025, "output": 0.00001}'::jsonb,
  'GPT-4o pricing per token',
  'https://openai.com/api/pricing/',
  true,
  NOW()
);
```

### Method 2: Bulk Insert (Multiple APIs)

```sql
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES
  ('openai', 'gpt-4o', 'token_based', '{"input": 0.0000025, "output": 0.00001}'::jsonb, 'GPT-4o', 'https://openai.com/api/pricing/', true, NOW()),
  ('openai', 'gpt-4-turbo', 'token_based', '{"input": 0.00001, "output": 0.00003}'::jsonb, 'GPT-4 Turbo', 'https://openai.com/api/pricing/', true, NOW()),
  ('anthropic', 'claude-3-5-sonnet-20241022', 'token_based', '{"input": 0.000003, "output": 0.000015}'::jsonb, 'Claude 3.5 Sonnet', 'https://www.anthropic.com/pricing', true, NOW()),
  ('stripe', 'charges.create', 'per_call', '{"per_call": 0.003}'::jsonb, 'Stripe charges', 'https://stripe.com/pricing', true, NOW()),
  ('pinecone', 'serverless', 'per_million', '{"per_million": 0.096}'::jsonb, 'Pinecone serverless', 'https://www.pinecone.io/pricing/', true, NOW());
```

---

## Step 5: Finding Pricing Sources

### Where to Look:

1. **Official Pricing Pages:**
   - OpenAI: https://openai.com/api/pricing/
   - Anthropic: https://www.anthropic.com/pricing
   - Google: https://ai.google.dev/pricing
   - Stripe: https://stripe.com/pricing
   - Twilio: https://www.twilio.com/pricing
   - Pinecone: https://www.pinecone.io/pricing/

2. **API Documentation:**
   - Most APIs have a "Pricing" or "Billing" section
   - Look for "per token", "per request", "per million" rates

3. **Billing Dashboards:**
   - Check your actual usage/billing in provider dashboards
   - Divide total cost by usage to get per-unit cost

4. **Pricing Calculators:**
   - Many providers have pricing calculators
   - Use these to reverse-engineer unit costs

---

## Step 6: Verification Checklist

Before adding pricing, verify:

- [ ] Pricing is from official source (not third-party)
- [ ] Pricing is current (check effective date)
- [ ] Pricing matches your usage region (if applicable)
- [ ] Pricing format matches expected structure
- [ ] Units are correct (per token, per call, etc.)
- [ ] Source URL is included for reference

---

## Step 7: Updating Existing Pricing

If pricing changes:

```sql
-- Mark old pricing as inactive
UPDATE pricing
SET is_active = false, expires_at = NOW()
WHERE provider = 'openai' AND model = 'gpt-4o';

-- Add new pricing
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES (
  'openai',
  'gpt-4o',
  'token_based',
  '{"input": 0.0000025, "output": 0.00001}'::jsonb,
  'GPT-4o pricing (updated)',
  'https://openai.com/api/pricing/',
  true,
  NOW()
);
```

---

## Step 8: Querying Pricing

### Get all active pricing for a provider:
```sql
SELECT * FROM pricing
WHERE provider = 'openai' AND is_active = true;
```

### Get pricing for a specific model:
```sql
SELECT * FROM pricing
WHERE provider = 'openai' AND model = 'gpt-4o' AND is_active = true;
```

### Get all pricing without a model (provider-level):
```sql
SELECT * FROM pricing
WHERE provider = 'stripe' AND model IS NULL AND is_active = true;
```

---

## Next Steps

1. **Start with major APIs:** OpenAI, Anthropic, Stripe, Twilio
2. **Add as you use them:** Don't add everything at once
3. **Keep it accurate:** Only add pricing you've verified
4. **Update regularly:** Check for pricing changes monthly
5. **Document sources:** Always include the source URL

---

## Common APIs to Add

**Priority 1 (Most Used):**
- OpenAI (all models)
- Anthropic (Claude models)
- Stripe (charges, subscriptions)
- Pinecone (serverless, standard)

**Priority 2 (Common):**
- Google (Gemini models)
- Twilio (SMS, voice)
- SendGrid (emails)
- Vector DBs (Weaviate, Qdrant)

**Priority 3 (As Needed):**
- Other LLM providers (Cohere, Mistral, etc.)
- Database APIs (MongoDB, PostgreSQL cloud)
- Storage APIs (AWS S3, GCS)
- Other services you use

---

**Remember:** Accuracy > Completeness. It's better to have accurate pricing for 10 APIs than inaccurate pricing for 100 APIs!

