# 📧 Email Alerts Setup Guide

## ✅ SendGrid Configuration

**Status:** API Key obtained, ready to configure

---

## 🔑 Environment Variables for Railway

Add these to your Railway backend service:

```bash
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=<your_sendgrid_api_key>
FROM_EMAIL=alerts@llmobserve.com
```

---

## 🚀 How to Add to Railway

### Option 1: Railway Dashboard (Easiest)
1. Go to https://railway.app
2. Select your backend service (collector)
3. Go to **Variables** tab
4. Click **+ New Variable**
5. Add each variable:
   - `EMAIL_PROVIDER` = `sendgrid`
   - `SENDGRID_API_KEY` = `<your_sendgrid_api_key>`
   - `FROM_EMAIL` = `alerts@llmobserve.com`
6. Railway will automatically restart the service

### Option 2: Railway CLI
```bash
railway variables set EMAIL_PROVIDER=sendgrid
railway variables set SENDGRID_API_KEY=<your_sendgrid_api_key>
railway variables set FROM_EMAIL=alerts@llmobserve.com
```

---

## 🧪 Testing Email Alerts

### Step 1: Create a Test Cap
1. Log into https://llmobserve.com
2. Go to **Settings**
3. Create a spending cap:
   - **Type:** Global
   - **Limit:** $0.10 (very low for testing)
   - **Period:** Daily
   - **Alert Threshold:** 50% (will alert at $0.05)
   - **Alert Email:** Your email address
   - **Enforcement:** Alert (not hard block)

### Step 2: Trigger the Cap
Run some LLM API calls in your code:
```python
import llmobserve
from openai import OpenAI

llmobserve.observe(
    api_key="your_llmobserve_api_key",
    collector_url="https://llmobserve-production.up.railway.app"
)

client = OpenAI()

# Make a few calls to reach $0.05
for i in range(5):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=50
    )
    print(f"Call {i+1} completed")
```

### Step 3: Check Your Email
Within 5 minutes, you should receive an email:

```
⚠️ LLMObserve Alert: 50% of your daily spending cap reached

Your daily spending is at:
$0.05 / $0.10
50% of your cap used
```

---

## 🔍 Troubleshooting

### Email not received?

1. **Check spam folder** (emails might go there initially)

2. **Verify Railway env vars:**
   ```bash
   railway variables
   ```
   Should show `EMAIL_PROVIDER`, `SENDGRID_API_KEY`, `FROM_EMAIL`

3. **Check Railway logs:**
   ```bash
   railway logs
   ```
   Look for:
   - `[CapMonitor] Starting service`
   - `[CapMonitor] Checking X enabled caps`
   - `Sent alert email via SendGrid to...`

4. **Verify cap monitor is running:**
   The cap monitor runs every 5 minutes. Check logs for:
   ```
   [CapMonitor] Starting cap check cycle...
   [CapMonitor] Checking 1 enabled caps
   ```

5. **Check SendGrid dashboard:**
   - Go to https://app.sendgrid.com
   - **Activity** → See if emails were sent
   - Look for delivery status, bounces, blocks

### SendGrid shows "blocked"?

You need to verify your sender email:
1. Go to **Settings → Sender Authentication**
2. Click **Verify a Single Sender**
3. Enter: `alerts@llmobserve.com`
4. Verify your email
5. Retry sending

**OR** use a verified email you already own:
```bash
FROM_EMAIL=your-verified-email@example.com
```

---

## 🎯 Cap Monitor Service

The cap monitor is a background service that checks spending caps every 5 minutes.

### Is it running?

Check Railway logs:
```bash
railway logs --tail
```

Look for:
```
[CapMonitor] Starting service (check interval: 300s)
[CapMonitor] Starting cap check cycle...
```

### Start it manually (if needed):

The cap monitor should start automatically with the FastAPI app. If not, you can run it as a separate Railway service:

**Option 1: Add to main.py (already done)**
```python
# collector/main.py already imports and includes cap monitoring
```

**Option 2: Standalone service**
```bash
python -m collector.cap_monitor
```

---

## 📊 Monitoring

### View Alerts in Dashboard

Users can view their alert history:
- **Endpoint:** `GET /caps/alerts/`
- **Dashboard:** Coming soon (can add to settings page)

### Alert Log Example
```json
{
  "id": "uuid",
  "alert_type": "threshold_reached",
  "current_spend": 0.05,
  "cap_limit": 0.10,
  "percentage": 50.0,
  "target_type": "global",
  "email_sent": true,
  "created_at": "2024-11-19T20:30:00Z"
}
```

---

## 🔐 Security Notes

1. **API Key Security:**
   - ✅ Stored in Railway env vars (not in code)
   - ✅ Not exposed to frontend
   - ✅ Backend only

2. **Email Rate Limiting:**
   - ✅ Cooldown: Max 1 email per hour per cap
   - ✅ Prevents spam if spending fluctuates

3. **User Privacy:**
   - ✅ Emails only sent to cap owner's email
   - ✅ No cross-user data leaks

---

## 📈 SendGrid Limits

**Free Tier:**
- 100 emails/day
- Should be plenty for alerts

**If you need more:**
- Upgrade to SendGrid paid plan
- Or switch to AWS SES (unlimited in free tier)

---

## ✅ Next Steps

1. ✅ Add env vars to Railway
2. ✅ Restart Railway service
3. ✅ Create test cap with low limit
4. ✅ Trigger it with API calls
5. ✅ Check email (and spam folder)
6. ✅ View alert in dashboard: `GET /caps/alerts/`

Once test email arrives, email alerts are **production ready**! 🚀

---

## 💡 Improving Deliverability (Optional)

To prevent emails going to spam, set up DNS authentication:

1. Go to SendGrid → **Settings → Sender Authentication**
2. Click **Authenticate Your Domain**
3. Follow the DNS setup for `llmobserve.com`
4. Add CNAME records to your domain registrar
5. Wait for verification (usually 24-48 hours)

**Result:** Emails will go straight to inbox, not spam

---

## 📝 Email Template Preview

```html
⚠️ Warning: Spending Cap Alert

Your daily spending is at:
$8.42 / $10.00
84% of your cap used

Details:
• Scope: Global
• Target: All services
• Period: Daily
• Current Spend: $8.4200
• Cap Limit: $10.00

Next Steps:
⚠️ Monitor your usage closely to avoid exceeding the cap.
Review your Dashboard for detailed cost breakdown
Adjust your cap limits or optimize usage in Settings
View cost trends by provider, model, and agent

💡 Tip: Set up multiple caps (global, per-provider, per-model) 
for granular cost control.
```

Beautiful, branded, professional. 🎨

---

**Status: Ready to deploy!** ✅

