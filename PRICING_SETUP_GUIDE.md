# 🎯 Quick Start: Adding API Pricing to Supabase

## Overview

Pricing is now stored in **Supabase** (not JSON files). This ensures accuracy - if pricing isn't found, cost = $0.00 (no defaults).

---

## Step 1: Access Supabase SQL Editor

1. Go to your Supabase dashboard
2. Click **SQL Editor** in the sidebar
3. Click **New Query**

---

## Step 2: Add Pricing for Major APIs

### Quick Copy-Paste: Major APIs

Copy and paste this into the SQL editor:

```sql
-- OpenAI Models
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES
  ('openai', 'gpt-4o', 'token_based', '{"input": 0.0000025, "output": 0.00001, "cached_input": 0.00000025}'::jsonb, 'GPT-4o', 'https://openai.com/api/pricing/', true, NOW()),
  ('openai', 'gpt-4-turbo', 'token_based', '{"input": 0.00001, "output": 0.00003}'::jsonb, 'GPT-4 Turbo', 'https://openai.com/api/pricing/', true, NOW()),
  ('openai', 'gpt-3.5-turbo', 'token_based', '{"input": 0.0000005, "output": 0.0000015, "cached_input": 0.00000005}'::jsonb, 'GPT-3.5 Turbo', 'https://openai.com/api/pricing/', true, NOW()),
  ('openai', 'gpt-4o-mini', 'token_based', '{"input": 0.00000015, "output": 0.0000006, "cached_input": 0.000000015}'::jsonb, 'GPT-4o Mini', 'https://openai.com/api/pricing/', true, NOW()),

-- Anthropic Models
  ('anthropic', 'claude-3-5-sonnet-20241022', 'token_based', '{"input": 0.000003, "output": 0.000015}'::jsonb, 'Claude 3.5 Sonnet', 'https://www.anthropic.com/pricing', true, NOW()),
  ('anthropic', 'claude-3-opus-20240229', 'token_based', '{"input": 0.000015, "output": 0.000075}'::jsonb, 'Claude 3 Opus', 'https://www.anthropic.com/pricing', true, NOW()),
  ('anthropic', 'claude-3-haiku-20240307', 'token_based', '{"input": 0.00000025, "output": 0.00000125}'::jsonb, 'Claude 3 Haiku', 'https://www.anthropic.com/pricing', true, NOW()),

-- Google Models
  ('google', 'gemini-1.5-pro', 'token_based', '{"input": 0.00000125, "output": 0.000005}'::jsonb, 'Gemini 1.5 Pro', 'https://ai.google.dev/pricing', true, NOW()),
  ('google', 'gemini-1.5-flash', 'token_based', '{"input": 0.000000075, "output": 0.0000003}'::jsonb, 'Gemini 1.5 Flash', 'https://ai.google.dev/pricing', true, NOW()),

-- Stripe
  ('stripe', 'charges.create', 'per_call', '{"per_call": 0.003}'::jsonb, 'Stripe charges (2.9% + $0.30)', 'https://stripe.com/pricing', true, NOW()),
  ('stripe', 'subscriptions.create', 'per_call', '{"per_call": 0.01}'::jsonb, 'Stripe subscriptions', 'https://stripe.com/pricing', true, NOW()),

-- Pinecone
  ('pinecone', 'serverless', 'per_million', '{"per_million": 0.096}'::jsonb, 'Pinecone serverless', 'https://www.pinecone.io/pricing/', true, NOW()),
  ('pinecone', 'standard', 'per_million', '{"per_million": 0.096}'::jsonb, 'Pinecone standard', 'https://www.pinecone.io/pricing/', true, NOW()),

-- Twilio
  ('twilio', 'messages.create', 'per_call', '{"per_call": 0.0075}'::jsonb, 'Twilio SMS', 'https://www.twilio.com/pricing', true, NOW()),
  ('twilio', 'calls.create', 'per_minute', '{"per_minute": 0.013}'::jsonb, 'Twilio voice', 'https://www.twilio.com/pricing', true, NOW()),

-- SendGrid
  ('sendgrid', 'mail.send', 'per_1k', '{"per_1k_emails": 0.60}'::jsonb, 'SendGrid emails', 'https://sendgrid.com/pricing/', true, NOW())
ON CONFLICT DO NOTHING;
```

**Click "Run"** to execute.

---

## Step 3: Verify Pricing Was Added

```sql
-- Check how many pricing entries you have
SELECT COUNT(*) FROM pricing WHERE is_active = true;

-- View all OpenAI pricing
SELECT provider, model, pricing_type, pricing_data, source 
FROM pricing 
WHERE provider = 'openai' AND is_active = true;
```

---

## Step 4: Finding Pricing for Other APIs

### Where to Find Pricing:

1. **Official Pricing Pages:**
   - OpenAI: https://openai.com/api/pricing/
   - Anthropic: https://www.anthropic.com/pricing
   - Google: https://ai.google.dev/pricing
   - Stripe: https://stripe.com/pricing
   - Twilio: https://www.twilio.com/pricing
   - Pinecone: https://www.pinecone.io/pricing/

2. **API Documentation:**
   - Look for "Pricing" or "Billing" sections
   - Check for "per token", "per request", "per million" rates

3. **Your Billing Dashboard:**
   - Check actual usage in provider dashboards
   - Divide total cost by usage to get per-unit cost

---

## Step 5: Adding Custom API Pricing

### Example: Adding a Custom API

```sql
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES (
  'myapi',                    -- Provider name
  'endpoint',                 -- Model/endpoint name (or NULL for provider-level)
  'per_call',                 -- Pricing type
  '{"per_call": 0.001}'::jsonb,  -- Pricing data
  'My API endpoint pricing',  -- Description
  'https://myapi.com/pricing', -- Source URL
  true,                       -- Is active
  NOW()                       -- Effective date
);
```

### Pricing Types:

- `token_based`: `{"input": 0.001, "output": 0.002}`
- `per_call`: `{"per_call": 0.001}`
- `per_million`: `{"per_million": 0.096}`
- `per_1k`: `{"per_1k_emails": 0.60}`
- `per_minute`: `{"per_minute": 0.013}`
- `per_second`: `{"per_second": 0.1}`

---

## Step 6: Updating Pricing

When pricing changes:

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
  'GPT-4o (updated pricing)',
  'https://openai.com/api/pricing/',
  true,
  NOW()
);
```

---

## Step 7: Restart Services

After adding pricing, restart the collector and proxy to load new pricing:

```bash
# Restart collector (loads pricing from Supabase)
pkill -f "uvicorn.*8000"
cd collector && python3 -m uvicorn main:app --reload --port 8000 &

# Restart proxy (loads pricing from collector API)
pkill -f "uvicorn.*9000"
cd proxy && python3 -m uvicorn main:app --port 9000 &
```

---

## Important Notes

✅ **Accuracy First:** Only add pricing you've verified from official sources  
✅ **No Defaults:** If pricing isn't found, cost = $0.00 (not a guess)  
✅ **Source URLs:** Always include source URL for reference  
✅ **Update Regularly:** Check for pricing changes monthly  
✅ **Test After Adding:** Make an API call and verify cost is calculated correctly

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
- Database APIs (MongoDB Atlas, etc.)
- Storage APIs (AWS S3, GCS)
- Other services you use

---

## Troubleshooting

**Pricing not loading?**
- Check Supabase connection in `collector/.env`
- Verify `DATABASE_URL` is set correctly
- Check collector logs for errors

**Cost showing $0.00?**
- Verify pricing exists in Supabase: `SELECT * FROM pricing WHERE provider = 'your_provider'`
- Check pricing key format: `provider:model` or just `provider`
- Restart collector and proxy after adding pricing

**Need help?**
- See `ADD_PRICING_GUIDE.md` for detailed examples
- Check `scripts/add_pricing_examples.sql` for more SQL examples

