-- Example SQL queries to add pricing for major APIs
-- Run these in your Supabase SQL editor

-- ============================================
-- LLM PROVIDERS
-- ============================================

-- OpenAI GPT-4o
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES (
  'openai',
  'gpt-4o',
  'token_based',
  '{"input": 0.0000025, "output": 0.00001, "cached_input": 0.00000025}'::jsonb,
  'GPT-4o pricing per token',
  'https://openai.com/api/pricing/',
  true,
  NOW()
)
ON CONFLICT DO NOTHING;

-- OpenAI GPT-4 Turbo
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES (
  'openai',
  'gpt-4-turbo',
  'token_based',
  '{"input": 0.00001, "output": 0.00003}'::jsonb,
  'GPT-4 Turbo pricing per token',
  'https://openai.com/api/pricing/',
  true,
  NOW()
)
ON CONFLICT DO NOTHING;

-- OpenAI GPT-3.5 Turbo
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES (
  'openai',
  'gpt-3.5-turbo',
  'token_based',
  '{"input": 0.0000005, "output": 0.0000015, "cached_input": 0.00000005}'::jsonb,
  'GPT-3.5 Turbo pricing per token',
  'https://openai.com/api/pricing/',
  true,
  NOW()
)
ON CONFLICT DO NOTHING;

-- Anthropic Claude 3.5 Sonnet
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES (
  'anthropic',
  'claude-3-5-sonnet-20241022',
  'token_based',
  '{"input": 0.000003, "output": 0.000015}'::jsonb,
  'Claude 3.5 Sonnet pricing per token',
  'https://www.anthropic.com/pricing',
  true,
  NOW()
)
ON CONFLICT DO NOTHING;

-- Anthropic Claude 3 Opus
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES (
  'anthropic',
  'claude-3-opus-20240229',
  'token_based',
  '{"input": 0.000015, "output": 0.000075}'::jsonb,
  'Claude 3 Opus pricing per token',
  'https://www.anthropic.com/pricing',
  true,
  NOW()
)
ON CONFLICT DO NOTHING;

-- Google Gemini 1.5 Pro
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES (
  'google',
  'gemini-1.5-pro',
  'token_based',
  '{"input": 0.00000125, "output": 0.000005}'::jsonb,
  'Gemini 1.5 Pro pricing per token',
  'https://ai.google.dev/pricing',
  true,
  NOW()
)
ON CONFLICT DO NOTHING;

-- ============================================
-- PAYMENT APIs
-- ============================================

-- Stripe Charges
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES (
  'stripe',
  'charges.create',
  'per_call',
  '{"per_call": 0.003}'::jsonb,
  'Stripe charge creation (2.9% + $0.30 per transaction)',
  'https://stripe.com/pricing',
  true,
  NOW()
)
ON CONFLICT DO NOTHING;

-- Stripe Subscriptions
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES (
  'stripe',
  'subscriptions.create',
  'per_call',
  '{"per_call": 0.01}'::jsonb,
  'Stripe subscription creation',
  'https://stripe.com/pricing',
  true,
  NOW()
)
ON CONFLICT DO NOTHING;

-- ============================================
-- VECTOR DATABASES
-- ============================================

-- Pinecone Serverless
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES (
  'pinecone',
  'serverless',
  'per_million',
  '{"per_million": 0.096}'::jsonb,
  'Pinecone serverless pricing per million vectors',
  'https://www.pinecone.io/pricing/',
  true,
  NOW()
)
ON CONFLICT DO NOTHING;

-- Pinecone Standard
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES (
  'pinecone',
  'standard',
  'per_million',
  '{"per_million": 0.096}'::jsonb,
  'Pinecone standard pricing per million operations',
  'https://www.pinecone.io/pricing/',
  true,
  NOW()
)
ON CONFLICT DO NOTHING;

-- Weaviate
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES (
  'weaviate',
  'standard',
  'per_million',
  '{"per_million": 0.10}'::jsonb,
  'Weaviate pricing per million operations',
  'https://weaviate.io/pricing',
  true,
  NOW()
)
ON CONFLICT DO NOTHING;

-- ============================================
-- COMMUNICATION APIs
-- ============================================

-- Twilio SMS
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES (
  'twilio',
  'messages.create',
  'per_call',
  '{"per_call": 0.0075}'::jsonb,
  'Twilio SMS pricing per message',
  'https://www.twilio.com/pricing',
  true,
  NOW()
)
ON CONFLICT DO NOTHING;

-- Twilio Voice
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES (
  'twilio',
  'calls.create',
  'per_minute',
  '{"per_minute": 0.013}'::jsonb,
  'Twilio voice call pricing per minute',
  'https://www.twilio.com/pricing',
  true,
  NOW()
)
ON CONFLICT DO NOTHING;

-- SendGrid Emails
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES (
  'sendgrid',
  'mail.send',
  'per_1k',
  '{"per_1k_emails": 0.60}'::jsonb,
  'SendGrid email pricing per 1k emails',
  'https://sendgrid.com/pricing/',
  true,
  NOW()
)
ON CONFLICT DO NOTHING;

-- ============================================
-- QUERY EXAMPLES
-- ============================================

-- View all active pricing
-- SELECT provider, model, pricing_type, pricing_data, source FROM pricing WHERE is_active = true ORDER BY provider, model;

-- View pricing for a specific provider
-- SELECT * FROM pricing WHERE provider = 'openai' AND is_active = true;

-- Update pricing (mark old as inactive, add new)
-- UPDATE pricing SET is_active = false WHERE provider = 'openai' AND model = 'gpt-4o';
-- INSERT INTO pricing (...) VALUES (...);

