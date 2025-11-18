# Stripe Webhook Setup for llmobserve.com

## Webhook URL
```
https://llmobserve.com/api/stripe/webhook
```

## Steps to Create Webhook in Stripe Dashboard

1. **Go to Stripe Dashboard**
   - Visit https://dashboard.stripe.com
   - Navigate to **Developers** → **Webhooks**

2. **Add Endpoint**
   - Click **"Add endpoint"**
   - Enter endpoint URL: `https://llmobserve.com/api/stripe/webhook`
   - Description: "LLM Observe Subscription Webhook"

3. **Select Events to Listen For**
   Select these events:
   - ✅ `checkout.session.completed` - When user completes checkout
   - ✅ `customer.subscription.updated` - When subscription changes (upgrade/downgrade)
   - ✅ `customer.subscription.deleted` - When subscription is canceled

4. **Get Webhook Signing Secret**
   - After creating the webhook, click on it
   - Copy the **"Signing secret"** (starts with `whsec_...`)
   - Add it to your environment variables as `STRIPE_WEBHOOK_SECRET`

5. **Test the Webhook**
   - In Stripe Dashboard, click **"Send test webhook"**
   - Select event type: `checkout.session.completed`
   - Verify it reaches your endpoint successfully

## Environment Variables Required

Add these to your production environment (Vercel/Railway):

```bash
# Stripe API Keys
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...  # From webhook settings
NEXT_PUBLIC_APP_URL=https://llmobserve.com
```

## Webhook Events Handled

### 1. `checkout.session.completed`
- Triggered when user completes Stripe Checkout
- Updates user subscription status to "active"
- Links Stripe customer ID and subscription ID to user

### 2. `customer.subscription.updated`
- Triggered when subscription changes (plan, status, etc.)
- Updates subscription status in database

### 3. `customer.subscription.deleted`
- Triggered when subscription is canceled
- Sets subscription status to "canceled"

## Testing Locally

For local testing, use Stripe CLI:

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhooks to local server
stripe listen --forward-to localhost:3000/api/stripe/webhook

# Trigger test event
stripe trigger checkout.session.completed
```

The CLI will give you a webhook signing secret (starts with `whsec_`) - use this for `STRIPE_WEBHOOK_SECRET` in local development.

## Verification

The webhook endpoint verifies:
- ✅ Stripe signature (prevents unauthorized requests)
- ✅ Event type (only processes subscription events)
- ✅ User exists in database (by Clerk user ID)

## Troubleshooting

1. **Webhook not receiving events**
   - Check webhook URL is correct: `https://llmobserve.com/api/stripe/webhook`
   - Verify webhook is enabled in Stripe Dashboard
   - Check Vercel deployment logs

2. **Signature verification fails**
   - Ensure `STRIPE_WEBHOOK_SECRET` matches the signing secret from Stripe
   - Verify secret is from the correct webhook endpoint

3. **User not found errors**
   - Ensure `clerk_user_id` is passed in checkout session metadata
   - Verify user exists in database before checkout

## Production Checklist

- [ ] Webhook endpoint created in Stripe Dashboard
- [ ] Webhook signing secret added to environment variables
- [ ] All three events selected (checkout.session.completed, customer.subscription.updated, customer.subscription.deleted)
- [ ] Test webhook sent and verified
- [ ] Production environment variables set in Vercel
- [ ] Webhook URL accessible (no Cloudflare/authentication blocking)

