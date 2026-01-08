-- Add missing pricing entries for OpenRouter-compatible providers
-- Run this against Supabase to enable cost tracking for all models

-- Meta/Llama Models
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES ('meta', 'llama-3.1-8b', 'per_token', '{"input": 5e-08, "output": 5e-08}', 'Meta Llama 3.1 8B Instruct', 'OpenRouter', true, NOW())
ON CONFLICT (provider, model) DO UPDATE SET pricing_data = EXCLUDED.pricing_data, is_active = true;

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES ('meta', 'llama-3.1-70b', 'per_token', '{"input": 3.5e-07, "output": 4e-07}', 'Meta Llama 3.1 70B Instruct', 'OpenRouter', true, NOW())
ON CONFLICT (provider, model) DO UPDATE SET pricing_data = EXCLUDED.pricing_data, is_active = true;

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES ('meta', 'llama-3.1-405b', 'per_token', '{"input": 3e-06, "output": 3e-06}', 'Meta Llama 3.1 405B', 'OpenRouter', true, NOW())
ON CONFLICT (provider, model) DO UPDATE SET pricing_data = EXCLUDED.pricing_data, is_active = true;

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES ('meta', 'llama-3.2-3b', 'per_token', '{"input": 3e-08, "output": 3e-08}', 'Meta Llama 3.2 3B', 'OpenRouter', true, NOW())
ON CONFLICT (provider, model) DO UPDATE SET pricing_data = EXCLUDED.pricing_data, is_active = true;

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES ('meta', 'llama-3.2-1b', 'per_token', '{"input": 2e-08, "output": 2e-08}', 'Meta Llama 3.2 1B', 'OpenRouter', true, NOW())
ON CONFLICT (provider, model) DO UPDATE SET pricing_data = EXCLUDED.pricing_data, is_active = true;

-- DeepSeek Models
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES ('deepseek', 'deepseek-chat', 'per_token', '{"input": 1.4e-07, "output": 2.8e-07}', 'DeepSeek Chat V3 - $0.14/M input, $0.28/M output', 'DeepSeek Official', true, NOW())
ON CONFLICT (provider, model) DO UPDATE SET pricing_data = EXCLUDED.pricing_data, is_active = true;

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES ('deepseek', 'deepseek-coder', 'per_token', '{"input": 1.4e-07, "output": 2.8e-07}', 'DeepSeek Coder', 'DeepSeek Official', true, NOW())
ON CONFLICT (provider, model) DO UPDATE SET pricing_data = EXCLUDED.pricing_data, is_active = true;

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES ('deepseek', 'deepseek-r1', 'per_token', '{"input": 5.5e-07, "output": 2.19e-06}', 'DeepSeek R1 reasoning - $0.55/M input, $2.19/M output', 'DeepSeek Official', true, NOW())
ON CONFLICT (provider, model) DO UPDATE SET pricing_data = EXCLUDED.pricing_data, is_active = true;

-- Mistral Models (additional variants)
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES ('mistral', 'mistral-7b', 'per_token', '{"input": 2.5e-07, "output": 2.5e-07}', 'Mistral 7B Instruct', 'OpenRouter', true, NOW())
ON CONFLICT (provider, model) DO UPDATE SET pricing_data = EXCLUDED.pricing_data, is_active = true;

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES ('mistral', 'mixtral-8x7b', 'per_token', '{"input": 6e-07, "output": 6e-07}', 'Mixtral 8x7B MoE', 'OpenRouter', true, NOW())
ON CONFLICT (provider, model) DO UPDATE SET pricing_data = EXCLUDED.pricing_data, is_active = true;

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES ('mistral', 'mistral-large', 'per_token', '{"input": 2e-06, "output": 6e-06}', 'Mistral Large', 'Mistral AI', true, NOW())
ON CONFLICT (provider, model) DO UPDATE SET pricing_data = EXCLUDED.pricing_data, is_active = true;

-- Qwen Models
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES ('qwen', 'qwen-2.5-72b', 'per_token', '{"input": 3.5e-07, "output": 4e-07}', 'Qwen 2.5 72B', 'OpenRouter', true, NOW())
ON CONFLICT (provider, model) DO UPDATE SET pricing_data = EXCLUDED.pricing_data, is_active = true;

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES ('qwen', 'qwen-2.5-7b', 'per_token', '{"input": 5e-08, "output": 5e-08}', 'Qwen 2.5 7B', 'OpenRouter', true, NOW())
ON CONFLICT (provider, model) DO UPDATE SET pricing_data = EXCLUDED.pricing_data, is_active = true;

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES ('qwen', 'qwen-2-72b', 'per_token', '{"input": 3.5e-07, "output": 4e-07}', 'Qwen 2 72B', 'OpenRouter', true, NOW())
ON CONFLICT (provider, model) DO UPDATE SET pricing_data = EXCLUDED.pricing_data, is_active = true;

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES ('qwen', 'qwen-2-7b', 'per_token', '{"input": 5e-08, "output": 5e-08}', 'Qwen 2 7B', 'OpenRouter', true, NOW())
ON CONFLICT (provider, model) DO UPDATE SET pricing_data = EXCLUDED.pricing_data, is_active = true;

-- Cohere Models (additional)
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES ('cohere', 'command-r', 'per_token', '{"input": 5e-07, "output": 1.5e-06}', 'Cohere Command R', 'Cohere Official', true, NOW())
ON CONFLICT (provider, model) DO UPDATE SET pricing_data = EXCLUDED.pricing_data, is_active = true;

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES ('cohere', 'command-r-plus', 'per_token', '{"input": 2.5e-06, "output": 1e-05}', 'Cohere Command R+', 'Cohere Official', true, NOW())
ON CONFLICT (provider, model) DO UPDATE SET pricing_data = EXCLUDED.pricing_data, is_active = true;

-- Google Gemini (additional variants)
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES ('google', 'gemini-2.0-flash', 'per_token', '{"input": 1e-07, "output": 4e-07}', 'Gemini 2.0 Flash', 'Google AI', true, NOW())
ON CONFLICT (provider, model) DO UPDATE SET pricing_data = EXCLUDED.pricing_data, is_active = true;

-- NousResearch
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES ('nous', 'hermes-3-llama-3.1-405b', 'per_token', '{"input": 2e-06, "output": 2e-06}', 'NousResearch Hermes 3 405B', 'OpenRouter', true, NOW())
ON CONFLICT (provider, model) DO UPDATE SET pricing_data = EXCLUDED.pricing_data, is_active = true;

-- Anthropic Claude 3.5 Haiku (if missing)
INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source, is_active, effective_date)
VALUES ('anthropic', 'claude-3.5-haiku', 'per_token', '{"input": 8e-07, "output": 4e-06}', 'Claude 3.5 Haiku', 'Anthropic Official', true, NOW())
ON CONFLICT (provider, model) DO UPDATE SET pricing_data = EXCLUDED.pricing_data, is_active = true;

-- Verify the inserts
SELECT provider, model, pricing_data FROM pricing WHERE provider IN ('meta', 'deepseek', 'qwen', 'nous') ORDER BY provider, model;



