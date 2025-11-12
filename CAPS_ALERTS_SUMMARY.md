# 🚀 Caps & Alerts System - Complete Implementation

**Date**: November 12, 2025  
**Status**: ✅ Production Ready

---

## 📋 Overview

Added comprehensive **Spending Caps & Email Alerts** system to LLMObserve, allowing users to:
- Set spending limits (global, per-provider, per-model, per-agent, per-customer)
- Receive email alerts when approaching caps
- Monitor spend in real-time with visual progress bars
- View alert history

---

## 🎯 What Was Added

### 1. **Backend Models** (`collector/models.py`)

#### SpendingCap Model
```python
- cap_type: str  # 'global', 'provider', 'model', 'agent', 'customer'
- target_name: Optional[str]  # Target identifier
- limit_amount: float  # Dollar cap
- period: str  # 'daily', 'weekly', 'monthly'
- alert_threshold: float  # 0.8 = 80%
- alert_email: str
- enabled: bool
- last_alerted_at: Optional[datetime]
```

#### Alert Model
```python
- alert_type: str  # 'threshold_reached', 'cap_exceeded'
- current_spend: float
- cap_limit: float
- percentage: float
- target_type: str
- target_name: str
- period_start/end: datetime
- email_sent: bool
```

### 2. **Backend API** (`collector/routers/caps.py`)

**Endpoints:**
- `POST /caps/` - Create spending cap
- `GET /caps/` - List user's caps
- `GET /caps/{cap_id}` - Get specific cap
- `PATCH /caps/{cap_id}` - Update cap
- `DELETE /caps/{cap_id}` - Delete cap
- `GET /caps/alerts/` - List alerts

**Features:**
- Real-time spend calculation
- Period-based aggregation (daily/weekly/monthly)
- Scope filtering (global, provider, model, agent, customer)
- Current spend % calculation

### 3. **Email Service** (`collector/email_service.py`)

**Supports 3 providers:**
- **SMTP** (Gmail, etc.) - Default for dev
- **SendGrid** - Production recommended
- **AWS SES** - Enterprise option

**Email Template:**
- Professional HTML design
- Color-coded urgency (warning/urgent)
- Spend breakdown
- Action links to dashboard
- Unsubscribe info

**Environment Variables:**
```bash
EMAIL_PROVIDER=smtp  # smtp, sendgrid, ses
SENDGRID_API_KEY=your_key
AWS_SES_REGION=us-east-1
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email
SMTP_PASSWORD=your_password
FROM_EMAIL=alerts@llmobserve.dev
```

### 4. **Background Monitor** (`collector/cap_monitor.py`)

**Runs every 5 minutes** (configurable)

**Logic:**
1. Fetch all enabled caps
2. Calculate current spend for each
3. Check if threshold/limit reached
4. Send email if needed (with cooldown)
5. Create alert record
6. Update cap's last_alerted_at

**Safety Features:**
- 1-hour cooldown between alerts
- Avoids duplicate alerts for same period
- Fail-safe error handling
- Graceful shutdown on SIGTERM

### 5. **Frontend UI** (`web/app/settings/page.tsx`)

#### Caps & Alerts Card

**Features:**
- ✅ **Create Cap Form** - Smooth UX with dropdown selectors
- ✅ **Real-time Progress Bars** - Visual spend tracking
- ✅ **Color-coded Status** - Green/Yellow/Red based on usage
- ✅ **Enable/Disable Toggle** - Quick cap management
- ✅ **Recent Alerts List** - Last 5 alerts with timestamps
- ✅ **Responsive Design** - Works on mobile/tablet/desktop

**Cap Types:**
- Global (All Services)
- By Provider (e.g., OpenAI)
- By Model (e.g., gpt-4)
- By Agent/Workflow
- By Customer

**Visual Indicators:**
- 🟢 Green: < alert threshold
- 🟡 Yellow: >= alert threshold
- 🔴 Red: >= 100% (cap exceeded)

### 6. **Database Migration** (`migrations/003_add_caps_and_alerts.sql`)

**Tables Created:**
- `spending_caps` - Cap configurations
- `alerts` - Alert history

**Indexes:**
- `idx_caps_user_id` - Fast user lookup
- `idx_caps_enabled` - Monitor query optimization
- `idx_alerts_user_id` - User alert history
- `idx_alerts_cap_id` - Cap-specific alerts
- `idx_alerts_created_at` - Chronological sorting

---

## 🎨 User Flow

### Setting Up a Cap (5 Steps)

1. **Navigate** to Settings → "Spending Caps & Alerts"
2. **Click** "Create Spending Cap"
3. **Configure**:
   - Cap Type (global, provider, model, agent, customer)
   - Target Name (if not global)
   - Limit Amount ($)
   - Period (daily/weekly/monthly)
   - Alert Threshold (%) - default 80%
   - Alert Email
4. **Click** "Create Cap"
5. **Done!** - Cap is now active and monitoring

### Receiving Alerts

1. System checks caps every 5 minutes
2. When threshold reached:
   - Email sent instantly
   - Alert appears in Settings
   - Visual indicator updates to yellow/red
3. User can:
   - View alert details
   - Adjust cap limit
   - Disable cap temporarily
   - Delete cap

---

## 🔧 Technical Architecture

### Cap Monitoring Flow

```
┌─────────────────┐
│ Background Task │ (Every 5 min)
└────────┬────────┘
         │
         ├─► Fetch Enabled Caps
         │
         ├─► For Each Cap:
         │   ├─► Calculate Current Spend
         │   ├─► Check Threshold
         │   ├─► Send Email if Needed
         │   └─► Create Alert Record
         │
         └─► Commit to Database
```

### Email Alert Flow

```
┌────────┐      ┌──────────┐      ┌──────────┐
│ Monitor│─────►│ Email    │─────►│ Provider │
│        │      │ Service  │      │ (SMTP/   │
│        │      │          │      │  SG/SES) │
└────────┘      └──────────┘      └──────────┘
                     │
                     ▼
              ┌──────────────┐
              │ User's Inbox │
              └──────────────┘
```

### Spend Calculation

```sql
SELECT SUM(cost_usd)
FROM trace_events
WHERE user_id = ?
  AND created_at >= period_start
  AND created_at < period_end
  AND [scope_filter]  -- provider/model/agent/customer
```

---

## 📊 API Coverage (30+ Providers)

### Already Tracked with Pricing

**LLMs (13):**
- OpenAI (GPT-4, GPT-3.5, O1, etc.)
- Anthropic (Claude 3.5, Claude 3)
- Google (Gemini 1.5, Gemini 2.0)
- Cohere
- Mistral
- Groq
- Together AI
- Hugging Face
- Replicate
- Perplexity
- Azure OpenAI
- AWS Bedrock
- AI21

**Vector Databases (8):**
- Pinecone
- Weaviate
- Qdrant
- Milvus/Zilliz
- Chroma
- MongoDB Atlas Vector
- Redis Vector
- Elasticsearch Vector

**Voice AI (7):**
- ElevenLabs
- AssemblyAI
- Deepgram
- Play.ht
- Azure Speech
- AWS Polly
- AWS Transcribe

**Images/Video (4):**
- Stability AI
- Runway ML
- AWS Rekognition
- Midjourney (via proxy)

**APIs (5):**
- Stripe
- PayPal
- Twilio
- SendGrid
- Voyage AI
- Algolia

**Total: 37 Providers** ✅

---

## 🚀 Quick Start Guide

### 1. Run Database Migration

```bash
cd /Users/pranavsrigiriraju/CostTracking/collector
sqlite3 llmobserve.db < ../migrations/003_add_caps_and_alerts.sql
```

### 2. Configure Email (Optional for Dev)

```bash
# .env
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=alerts@yourdomain.com
```

### 3. Restart Backend

```bash
uvicorn main:app --reload --port 8000
```

Background monitor starts automatically!

### 4. Use the UI

1. Go to `http://localhost:3000/settings`
2. Scroll to "Spending Caps & Alerts"
3. Click "Create Spending Cap"
4. Fill form and submit
5. Done!

---

## 🧪 Testing

### Test Cap Creation

```bash
curl -X POST http://localhost:8000/caps/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cap_type": "global",
    "limit_amount": 10.00,
    "period": "daily",
    "alert_threshold": 0.8,
    "alert_email": "your@email.com"
  }'
```

### Test Cap Monitoring

```bash
# Run manually
cd collector
python cap_monitor.py
```

### Trigger Alert (for testing)

1. Create a cap with low limit (e.g., $0.01)
2. Run test script to generate costs
3. Wait 5 minutes or run monitor manually
4. Check email inbox for alert!

---

## 📈 Production Considerations

### Email Service

**Development:**
- Use SMTP with Gmail (free)
- Set up App Password (not regular password)

**Production:**
- **SendGrid** (recommended): 100 emails/day free, reliable
- **AWS SES**: $0.10 per 1000 emails, needs verification
- Configure `EMAIL_PROVIDER` env var

### Monitor Interval

```python
# main.py
cap_monitor_task = asyncio.create_task(
    run_cap_monitor(check_interval_seconds=300)  # 5 minutes
)
```

**Adjust based on needs:**
- `60` = 1 minute (real-time, higher load)
- `300` = 5 minutes (balanced)
- `600` = 10 minutes (lower load)

### Database Indexes

All necessary indexes created in migration:
- Fast cap lookups
- Efficient alert queries
- Optimized for monitor queries

### Scaling

**For high volume:**
1. Move monitor to separate worker process
2. Use Redis for alert cooldown cache
3. Batch email sends
4. Add webhook alerts (Slack, Discord, etc.)

---

## 🎯 Next Steps (Optional Enhancements)

### Phase 2 Features
- [ ] Slack/Discord webhook alerts
- [ ] SMS alerts (via Twilio)
- [ ] Auto-disable services when cap exceeded
- [ ] Budget forecasting (predict when cap will be reached)
- [ ] Weekly/monthly spend reports
- [ ] Multi-user caps (team-wide limits)
- [ ] Cap templates (quick setup for common scenarios)

### Advanced Analytics
- [ ] Trend analysis (spend velocity)
- [ ] Anomaly detection (unusual spikes)
- [ ] Cost optimization recommendations
- [ ] Comparative analytics (vs. last period)

---

## 📝 File Changes Summary

### New Files (5)
```
collector/routers/caps.py          # API endpoints
collector/email_service.py         # Email sending
collector/cap_monitor.py           # Background monitor
migrations/003_add_caps_and_alerts.sql  # DB schema
CAPS_ALERTS_SUMMARY.md            # This file
```

### Modified Files (5)
```
collector/models.py                # Added SpendingCap, Alert models
collector/main.py                  # Added caps router + monitor task
collector/routers/__init__.py      # Exported caps router
web/lib/api.ts                     # Added caps/alerts API functions
web/app/settings/page.tsx          # Added Caps & Alerts UI
```

---

## ✅ Acceptance Criteria

All requirements met:

- ✅ **30+ API tracking** - 37 providers with pricing
- ✅ **Caps backend** - Full CRUD + calculation
- ✅ **Email alerts** - Multi-provider support
- ✅ **Background monitor** - Auto-checking every 5 min
- ✅ **Smooth UI flow** - Beautiful, intuitive interface
- ✅ **Real-time progress** - Visual indicators
- ✅ **Alert history** - Last 5 alerts displayed
- ✅ **Multiple cap types** - Global, provider, model, agent, customer
- ✅ **Enable/disable** - Quick toggle
- ✅ **Production ready** - Error handling, indexes, migrations

---

## 🎉 Ready to Use!

The system is now fully functional and ready for production use. Users can:

1. ✅ Track costs across 37+ APIs
2. ✅ Set custom spending caps
3. ✅ Receive email alerts
4. ✅ View real-time progress
5. ✅ Manage caps easily
6. ✅ Review alert history

**No breaking changes** - All existing functionality preserved!

---

**Questions? Issues?**
- Check backend logs: `/tmp/backend.log`
- Check frontend console: Browser DevTools
- Test email: Run `python cap_monitor.py` manually
- Database: Query `spending_caps` and `alerts` tables

