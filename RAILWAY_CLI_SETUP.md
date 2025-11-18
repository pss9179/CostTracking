# Railway CLI Setup - For Suriya's Account

## Option 1: Get Suriya's Railway Token (Easiest)

**Suriya needs to:**
1. Run: `railway login`
2. Go to: https://railway.app/account/tokens
3. Create a new token (or copy existing one)
4. Share the token with you

**Then you run:**
```bash
railway login --token <token-from-suriya>
cd collector
railway service  # Select the service
railway run python migrate_add_stripe_columns.py
```

## Option 2: Suriya Runs It (2 minutes)

**Suriya runs:**
```bash
cd collector
railway login  # If not already logged in
railway service  # Select the service if prompted
railway run python migrate_add_stripe_columns.py
```

## Option 3: Add You as Collaborator

**Suriya:**
1. Railway Dashboard → Project → Settings → Team
2. Add your email as collaborator
3. You'll get an invite email
4. Accept invite, then you can run:
```bash
railway login
cd collector
railway service
railway run python migrate_add_stripe_columns.py
```

## Quick Check

After any method, verify it worked:
```bash
railway run python -c "
from sqlalchemy import create_engine, text
import os
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    result = conn.execute(text(\"SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name IN ('stripe_customer_id', 'stripe_subscription_id', 'subscription_status', 'promo_code')\"))
    print('Columns found:', [r[0] for r in result])
"
```

