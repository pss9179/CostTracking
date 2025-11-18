# Quick Start: Stripe Webhook Setup

Updated: Webhook configured and ready - Build fix applied

## Webhook URL for Stripe Dashboard
```
https://llmobserve.com/api/stripe/webhook
```

## Quick Setup Steps

1. **Go to Stripe Dashboard** → Developers → Webhooks → Add endpoint

2. **Enter URL**: `https://llmobserve.com/api/stripe/webhook`

3. **Select these 3 events**:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`

4. **Copy the webhook signing secret** (starts with `whsec_...`)

5. **Add to Vercel environment variables**:
   ```
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```

6. **Test it**: In Stripe Dashboard, click "Send test webhook" → Select `checkout.session.completed`

## That's it! ✅

The webhook will automatically:
- Activate subscriptions when checkout completes
- Update subscription status when changed
- Cancel subscriptions when deleted

## Need Help?

See `STRIPE_WEBHOOK_SETUP.md` for detailed instructions and troubleshooting.

