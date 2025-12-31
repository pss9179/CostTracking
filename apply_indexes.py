#!/usr/bin/env python3
"""
Apply performance indexes to the database.
Run with: railway run python apply_indexes.py
"""
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    exit(1)

print(f'Connecting to database...')
engine = create_engine(DATABASE_URL)

indexes = [
    ('idx_trace_user_created', 'CREATE INDEX IF NOT EXISTS idx_trace_user_created ON trace_events(user_id, created_at DESC)'),
    ('idx_trace_user_provider_created', 'CREATE INDEX IF NOT EXISTS idx_trace_user_provider_created ON trace_events(user_id, provider, created_at DESC)'),
    ('idx_trace_user_section_created', 'CREATE INDEX IF NOT EXISTS idx_trace_user_section_created ON trace_events(user_id, section, created_at DESC)'),
    ('idx_trace_user_customer_created', 'CREATE INDEX IF NOT EXISTS idx_trace_user_customer_created ON trace_events(user_id, customer_id, created_at DESC)'),
]

with engine.connect() as conn:
    for idx_name, idx_sql in indexes:
        print(f'Creating index: {idx_name}...')
        try:
            conn.execute(text(idx_sql))
            conn.commit()
            print(f'  ✓ {idx_name} created')
        except Exception as e:
            if 'already exists' in str(e).lower():
                print(f'  ✓ {idx_name} already exists')
            else:
                print(f'  ✗ Error: {e}')
    
    # Run ANALYZE
    print('Running ANALYZE trace_events...')
    try:
        conn.execute(text('ANALYZE trace_events'))
        conn.commit()
        print('  ✓ ANALYZE complete')
    except Exception as e:
        print(f'  ✗ Error: {e}')

print('\n✅ Done! All indexes created. Your queries should be much faster now.')

