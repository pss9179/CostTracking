-- Migrate pricing data from registry.json to Supabase
-- Generated automatically

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'gpt-5', 'token_based', '{"input": 1.25e-06, "output": 1e-05, "cached_input": 1.25e-07}'::jsonb, 'openai gpt-5 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'gpt-5-mini', 'token_based', '{"input": 2.5e-07, "output": 2e-06, "cached_input": 2.5e-08}'::jsonb, 'openai gpt-5-mini pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'gpt-5-nano', 'token_based', '{"input": 5e-08, "output": 4e-07, "cached_input": 5e-09}'::jsonb, 'openai gpt-5-nano pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'gpt-5-pro', 'token_based', '{"input": 1.5e-05, "output": 0.00012, "cached_input": 1.5e-06}'::jsonb, 'openai gpt-5-pro pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'gpt-4.1', 'training', '{"training": 2.5e-05, "training_per_hour": null}'::jsonb, 'openai gpt-4.1 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'gpt-4.1-mini', 'training', '{"training": 5e-06, "training_per_hour": null}'::jsonb, 'openai gpt-4.1-mini pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'gpt-4.1-nano', 'training', '{"training": 1.5e-06, "training_per_hour": null}'::jsonb, 'openai gpt-4.1-nano pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'o4-mini', 'training', '{"training": null, "training_per_hour": 100.0}'::jsonb, 'openai o4-mini pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'gpt-realtime', 'token_based', '{"input": 4e-06, "output": 1.6e-05, "cached_input": 4e-07}'::jsonb, 'openai gpt-realtime pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'gpt-realtime-mini', 'token_based', '{"input": 6e-07, "output": 2.4e-06, "cached_input": 6e-08}'::jsonb, 'openai gpt-realtime-mini pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'gpt-realtime-audio', 'token_based', '{"input": 3.2e-05, "output": 6.4e-05, "cached_input": 4e-07}'::jsonb, 'openai gpt-realtime-audio pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'gpt-realtime-mini-audio', 'token_based', '{"input": 1e-05, "output": 2e-05, "cached_input": 3e-07}'::jsonb, 'openai gpt-realtime-mini-audio pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'gpt-realtime-image', 'token_based', '{"input": 5e-06, "output": 0.0, "cached_input": 5e-07}'::jsonb, 'openai gpt-realtime-image pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'gpt-realtime-mini-image', 'token_based', '{"input": 8e-07, "output": 0.0, "cached_input": 8e-08}'::jsonb, 'openai gpt-realtime-mini-image pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'sora-2', 'per_second', '{"per_second": 0.1}'::jsonb, 'openai sora-2 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'sora-2-pro-720', 'per_second', '{"per_second": 0.3}'::jsonb, 'openai sora-2-pro-720 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'sora-2-pro-1024', 'per_second', '{"per_second": 0.5}'::jsonb, 'openai sora-2-pro-1024 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'gpt-image-1', 'token_based', '{"input": 5e-06, "output": 4e-05, "cached_input": 1.25e-06}'::jsonb, 'openai gpt-image-1 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'gpt-image-1-mini', 'token_based', '{"input": 2.5e-06, "output": 8e-06, "cached_input": 2e-07}'::jsonb, 'openai gpt-image-1-mini pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'gpt-4o', 'token_based', '{"input": 2.5e-06, "output": 1e-05, "cached_input": 2.5e-07}'::jsonb, 'openai gpt-4o pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'gpt-4o-mini', 'token_based', '{"input": 1.5e-07, "output": 6e-07, "cached_input": 1.5e-08}'::jsonb, 'openai gpt-4o-mini pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'gpt-4-turbo', 'token_based', '{"input": 1e-05, "output": 3e-05, "cached_input": 1e-06}'::jsonb, 'openai gpt-4-turbo pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'gpt-4', 'token_based', '{"input": 3e-05, "output": 6e-05, "cached_input": 3e-06}'::jsonb, 'openai gpt-4 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'gpt-3.5-turbo', 'token_based', '{"input": 5e-07, "output": 1.5e-06, "cached_input": 5e-08}'::jsonb, 'openai gpt-3.5-turbo pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'text-embedding-3-small', 'token_based', '{"input": 2e-08, "output": 0.0, "cached_input": 0.0}'::jsonb, 'openai text-embedding-3-small pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'text-embedding-3-large', 'token_based', '{"input": 1.3e-07, "output": 0.0, "cached_input": 0.0}'::jsonb, 'openai text-embedding-3-large pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'text-embedding-ada-002', 'token_based', '{"input": 1e-07, "output": 0.0, "cached_input": 0.0}'::jsonb, 'openai text-embedding-ada-002 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'whisper-1', 'per_minute', '{"per_minute": 0.006}'::jsonb, 'openai whisper-1 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'tts-1', 'per_character', '{"per_character": 1.5e-05}'::jsonb, 'openai tts-1 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'tts-1-hd', 'per_character', '{"per_character": 3e-05}'::jsonb, 'openai tts-1-hd pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'dall-e-3', 'token_based', '{"input": 0.0, "output": 0.0, "cached_input": 0.0}'::jsonb, 'openai dall-e-3 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'dall-e-2', 'token_based', '{"input": 0.0, "output": 0.0, "cached_input": 0.0}'::jsonb, 'openai dall-e-2 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'o1-preview', 'token_based', '{"input": 1.5e-05, "output": 6e-05, "cached_input": 1.5e-06}'::jsonb, 'openai o1-preview pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'o1-mini', 'token_based', '{"input": 3e-06, "output": 1.2e-05, "cached_input": 3e-07}'::jsonb, 'openai o1-mini pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'code-interpreter', 'per_session', '{"per_session": 0.03}'::jsonb, 'openai code-interpreter pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'file-search-storage', 'per_gb_day', '{"per_gb_day": 0.1}'::jsonb, 'openai file-search-storage pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'file-search-tool', 'per_1k_calls', '{"per_1k_calls": 2.5}'::jsonb, 'openai file-search-tool pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'web-search-tool', 'per_1k_calls', '{"per_1k_calls": 10.0}'::jsonb, 'openai web-search-tool pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'moderation', 'token_based', '{"input": 0.0, "output": 0.0, "cached_input": 0.0}'::jsonb, 'openai moderation pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('openai', 'vector-store-storage', 'per_gb_day', '{"per_gb_day": 0.1}'::jsonb, 'openai vector-store-storage pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('anthropic', 'claude-3-opus', 'token_based', '{"input": 1.5e-05, "output": 7.5e-05, "cached_input": 0.0}'::jsonb, 'anthropic claude-3-opus pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('anthropic', 'claude-3-sonnet', 'token_based', '{"input": 3e-06, "output": 1.5e-05, "cached_input": 0.0}'::jsonb, 'anthropic claude-3-sonnet pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('pinecone', 'storage', 'per_gb_month', '{"per_gb_month": 0.33}'::jsonb, 'pinecone storage pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('pinecone', 'write-units', 'per_million', '{"per_million": 4.0}'::jsonb, 'pinecone write-units pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('pinecone', 'read-units', 'per_million', '{"per_million": 16.0}'::jsonb, 'pinecone read-units pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('pinecone', 'query', 'per_million', '{"per_million": 16.0}'::jsonb, 'pinecone query pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('pinecone', 'upsert', 'per_million', '{"per_million": 4.0}'::jsonb, 'pinecone upsert pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('pinecone', 'delete', 'per_million', '{"per_million": 4.0}'::jsonb, 'pinecone delete pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('pinecone', 'update', 'per_million', '{"per_million": 4.0}'::jsonb, 'pinecone update pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('pinecone', 'fetch', 'per_million', '{"per_million": 16.0}'::jsonb, 'pinecone fetch pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('pinecone', 'list', 'per_million', '{"per_million": 16.0}'::jsonb, 'pinecone list pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('pinecone', 'describe_index_stats', 'per_million', '{"per_million": 16.0}'::jsonb, 'pinecone describe_index_stats pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('pinecone', 'import-from-storage', 'per_gb', '{"per_gb": 1.0}'::jsonb, 'pinecone import-from-storage pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('pinecone', 'backup', 'per_gb_month', '{"per_gb_month": 0.1}'::jsonb, 'pinecone backup pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('pinecone', 'restore-from-backup', 'per_gb', '{"per_gb": 0.15}'::jsonb, 'pinecone restore-from-backup pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('pinecone', 'llama-text-embed-v2', 'per_million_tokens', '{"per_million_tokens": 0.16}'::jsonb, 'pinecone llama-text-embed-v2 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('pinecone', 'multilingual-e5-large', 'per_million_tokens', '{"per_million_tokens": 0.08}'::jsonb, 'pinecone multilingual-e5-large pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('pinecone', 'pinecone-sparse-english-v0', 'per_million_tokens', '{"per_million_tokens": 0.08}'::jsonb, 'pinecone pinecone-sparse-english-v0 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('pinecone', 'pinecone-rerank-v0', 'per_1k_requests', '{"per_1k_requests": 2.0}'::jsonb, 'pinecone pinecone-rerank-v0 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('pinecone', 'bge-reranker-v2-m3', 'per_1k_requests', '{"per_1k_requests": 2.0}'::jsonb, 'pinecone bge-reranker-v2-m3 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('pinecone', 'cohere-rerank-v3.5', 'per_1k_requests', '{"per_1k_requests": 2.0}'::jsonb, 'pinecone cohere-rerank-v3.5 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('anthropic', 'claude-3.5-sonnet', 'token_based', '{"input": 3e-06, "output": 1.5e-05, "cached_input": 0.0}'::jsonb, 'anthropic claude-3.5-sonnet pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('anthropic', 'claude-3-haiku', 'token_based', '{"input": 2.5e-07, "output": 1.25e-06, "cached_input": 0.0}'::jsonb, 'anthropic claude-3-haiku pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('google', 'gemini-1.5-pro', 'token_based', '{"input": 3.5e-06, "output": 1.05e-05, "cached_input": 0.0}'::jsonb, 'google gemini-1.5-pro pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('google', 'gemini-1.5-flash', 'token_based', '{"input": 7.5e-08, "output": 3e-07, "cached_input": 0.0}'::jsonb, 'google gemini-1.5-flash pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('google', 'gemini-1.0-pro', 'token_based', '{"input": 5e-07, "output": 1.5e-06, "cached_input": 0.0}'::jsonb, 'google gemini-1.0-pro pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('cohere', 'command', 'token_based', '{"input": 1e-06, "output": 2e-06, "cached_input": 0.0}'::jsonb, 'cohere command pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('cohere', 'command-light', 'token_based', '{"input": 3e-07, "output": 6e-07, "cached_input": 0.0}'::jsonb, 'cohere command-light pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('cohere', 'embed-english-v3.0', 'token_based', '{"input": 1e-07, "output": 0, "cached_input": 0.0}'::jsonb, 'cohere embed-english-v3.0 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('voyage', 'voyage-2', 'token_based', '{"input": 1.2e-07, "output": 0, "cached_input": 0.0}'::jsonb, 'voyage voyage-2 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('voyage', 'voyage-lite-02', 'token_based', '{"input": 6e-08, "output": 0, "cached_input": 0.0}'::jsonb, 'voyage voyage-lite-02 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('elevenlabs', 'eleven_multilingual_v2', 'per_1k_chars', '{"per_1k_chars": 0.18}'::jsonb, 'elevenlabs eleven_multilingual_v2 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('elevenlabs', 'eleven_turbo_v2', 'per_1k_chars', '{"per_1k_chars": 0.18}'::jsonb, 'elevenlabs eleven_turbo_v2 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('mistral', 'mistral-large-latest', 'token_based', '{"input": 2e-06, "output": 6e-06, "cached_input": 0.0}'::jsonb, 'mistral mistral-large-latest pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('mistral', 'mistral-small-latest', 'token_based', '{"input": 1e-06, "output": 3e-06, "cached_input": 0.0}'::jsonb, 'mistral mistral-small-latest pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('mistral', 'mistral-tiny', 'token_based', '{"input": 2.5e-07, "output": 7.5e-07, "cached_input": 0.0}'::jsonb, 'mistral mistral-tiny pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('groq', 'llama-3.1-405b', 'token_based', '{"input": 5.9e-07, "output": 7.9e-07, "cached_input": 0.0}'::jsonb, 'groq llama-3.1-405b pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('groq', 'llama-3.1-70b', 'token_based', '{"input": 5.9e-07, "output": 7.9e-07, "cached_input": 0.0}'::jsonb, 'groq llama-3.1-70b pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('groq', 'llama-3.1-8b', 'token_based', '{"input": 5e-08, "output": 8e-08, "cached_input": 0.0}'::jsonb, 'groq llama-3.1-8b pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('groq', 'mixtral-8x7b', 'token_based', '{"input": 2.4e-07, "output": 2.4e-07, "cached_input": 0.0}'::jsonb, 'groq mixtral-8x7b pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('ai21', 'j2-ultra', 'token_based', '{"input": 1.5e-05, "output": 1.5e-05, "cached_input": 0.0}'::jsonb, 'ai21 j2-ultra pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('ai21', 'j2-mid', 'token_based', '{"input": 1e-05, "output": 1e-05, "cached_input": 0.0}'::jsonb, 'ai21 j2-mid pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('huggingface', 'base', 'per_1k_tokens', '{"per_1k_tokens": 5e-05}'::jsonb, 'huggingface base pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('together', 'llama-3-70b', 'token_based', '{"input": 9e-07, "output": 9e-07, "cached_input": 0.0}'::jsonb, 'together llama-3-70b pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('together', 'mixtral-8x22b', 'token_based', '{"input": 1.2e-06, "output": 1.2e-06, "cached_input": 0.0}'::jsonb, 'together mixtral-8x22b pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('replicate', 'base', 'per_second', '{"per_second": 0.00023}'::jsonb, 'replicate base pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('perplexity', 'pplx-70b-online', 'token_based', '{"input": 1e-06, "output": 1e-06, "cached_input": 0.0}'::jsonb, 'perplexity pplx-70b-online pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('perplexity', 'pplx-7b-online', 'token_based', '{"input": 2e-07, "output": 2e-07, "cached_input": 0.0}'::jsonb, 'perplexity pplx-7b-online pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('azure_openai', 'gpt-4', 'token_based', '{"input": 3e-05, "output": 6e-05, "cached_input": 0.0}'::jsonb, 'azure_openai gpt-4 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('azure_openai', 'gpt-35-turbo', 'token_based', '{"input": 1.5e-06, "output": 2e-06, "cached_input": 0.0}'::jsonb, 'azure_openai gpt-35-turbo pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('aws_bedrock', 'claude-3-opus', 'token_based', '{"input": 1.5e-05, "output": 7.5e-05, "cached_input": 0.0}'::jsonb, 'aws_bedrock claude-3-opus pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('aws_bedrock', 'claude-3-sonnet', 'token_based', '{"input": 3e-06, "output": 1.5e-05, "cached_input": 0.0}'::jsonb, 'aws_bedrock claude-3-sonnet pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('aws_bedrock', 'llama-3-70b', 'token_based', '{"input": 2.65e-06, "output": 3.5e-06, "cached_input": 0.0}'::jsonb, 'aws_bedrock llama-3-70b pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('assemblyai', 'best', 'per_minute', '{"per_minute": 0.00062}'::jsonb, 'assemblyai best pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('assemblyai', 'nano', 'per_minute', '{"per_minute": 0.00018}'::jsonb, 'assemblyai nano pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('deepgram', 'nova-2', 'per_minute', '{"per_minute": 0.0043}'::jsonb, 'deepgram nova-2 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('deepgram', 'base', 'per_minute', '{"per_minute": 0.0125}'::jsonb, 'deepgram base pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('playht', 'standard', 'per_1k_chars', '{"per_1k_chars": 0.4}'::jsonb, 'playht standard pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('playht', 'premium', 'per_1k_chars', '{"per_1k_chars": 1.2}'::jsonb, 'playht premium pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('azure_speech', 'standard', 'per_1k_chars', '{"per_1k_chars": 0.001}'::jsonb, 'azure_speech standard pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('azure_speech', 'neural', 'per_1k_chars', '{"per_1k_chars": 0.016}'::jsonb, 'azure_speech neural pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('aws_polly', 'standard', 'per_1m_chars', '{"per_1m_chars": 4.0}'::jsonb, 'aws_polly standard pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('aws_polly', 'neural', 'per_1m_chars', '{"per_1m_chars": 16.0}'::jsonb, 'aws_polly neural pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('aws_transcribe', 'standard', 'per_minute', '{"per_minute": 0.024}'::jsonb, 'aws_transcribe standard pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('stability', 'sd-xl', 'per_image', '{"per_image": 0.04}'::jsonb, 'stability sd-xl pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('stability', 'sd-3', 'per_image', '{"per_image": 0.065}'::jsonb, 'stability sd-3 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('runway', 'gen-2', 'per_second', '{"per_second": 0.05}'::jsonb, 'runway gen-2 pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('aws_rekognition', 'detect_labels', 'per_1k_images', '{"per_1k_images": 1.0}'::jsonb, 'aws_rekognition detect_labels pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('weaviate', 'standard', 'token_based', '{"input": 0.0, "output": 0.0, "cached_input": 0.0}'::jsonb, 'weaviate standard pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('qdrant', 'cloud', 'token_based', '{"input": 0.0, "output": 0.0, "cached_input": 0.0}'::jsonb, 'qdrant cloud pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('milvus', 'cloud', 'token_based', '{"input": 0.0, "output": 0.0, "cached_input": 0.0}'::jsonb, 'milvus cloud pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('chroma', 'hosted', 'token_based', '{"input": 0.0, "output": 0.0, "cached_input": 0.0}'::jsonb, 'chroma hosted pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('mongodb', 'atlas_vector', 'token_based', '{"input": 0.0, "output": 0.0, "cached_input": 0.0}'::jsonb, 'mongodb atlas_vector pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('redis', 'vector', 'token_based', '{"input": 0.0, "output": 0.0, "cached_input": 0.0}'::jsonb, 'redis vector pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('elasticsearch', 'vector', 'token_based', '{"input": 0.0, "output": 0.0, "cached_input": 0.0}'::jsonb, 'elasticsearch vector pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('stripe', 'payment_intent', 'percentage', '{"percentage": 0.029, "fixed_fee": 0.3}'::jsonb, 'stripe payment_intent pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('stripe', 'transfer', 'percentage', '{"percentage": 0.0025, "fixed_fee": 0}'::jsonb, 'stripe transfer pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('paypal', 'standard', 'percentage', '{"percentage": 0.0349, "fixed_fee": 0.49}'::jsonb, 'paypal standard pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('twilio', 'sms_outbound', 'per_message', '{"per_message": 0.0075}'::jsonb, 'twilio sms_outbound pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('twilio', 'voice_outbound', 'per_minute', '{"per_minute": 0.014}'::jsonb, 'twilio voice_outbound pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('sendgrid', 'email', 'per_1k_emails', '{"per_1k_emails": 0.95}'::jsonb, 'sendgrid email pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('algolia', 'search', 'per_1k_requests', '{"per_1k_requests": 0.5}'::jsonb, 'algolia search pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('algolia', 'indexing', 'per_1k_records', '{"per_1k_records": 0.4}'::jsonb, 'algolia indexing pricing', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();

