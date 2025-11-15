# 🚀 Deploy to Render - Quick Guide

## Step 1: Login to Render

```bash
render login
```

This will open your browser to authenticate.

## Step 2: Create Service from render.yaml

```bash
# From the project root
render blueprint launch
```

This will:
- Read `render.yaml`
- Create the web service
- Prompt you to set environment variables that are marked `sync: false`

## Step 3: Set Environment Variables

After the service is created, set these in the Render dashboard or via CLI:

```bash
# Set DATABASE_URL (your Supabase connection string)
render env set DATABASE_URL "postgresql://postgres:xxx@db.xxx.supabase.co:5432/postgres"

# Set Clerk secret key
render env set CLERK_SECRET_KEY "sk_live_xxxxx"

# Set email provider (choose one):
# Option 1: SendGrid
render env set EMAIL_PROVIDER "sendgrid"
render env set SENDGRID_API_KEY "SG.xxxxx"

# Option 2: SMTP
# render env set EMAIL_PROVIDER "smtp"
# render env set SMTP_HOST "smtp.gmail.com"
# render env set SMTP_PORT "587"
# render env set SMTP_USERNAME "your-email@gmail.com"
# render env set SMTP_PASSWORD "your-app-password"

# Update ALLOWED_ORIGINS with your frontend URL (after deploying frontend)
render env set ALLOWED_ORIGINS "https://your-frontend.vercel.app"
```

## Step 4: Deploy

```bash
# Trigger a deployment
render deploys create

# Or just push to your connected repo (if you connected GitHub)
git push
```

## Step 5: Get Your Backend URL

```bash
# Get service URL
render services list

# Or check in Render dashboard
# Your service will have a URL like: https://llmobserve-api.onrender.com
```

## Step 6: Deploy Frontend to Vercel

```bash
cd web
vercel login
vercel

# Set environment variables
vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY production
vercel env add CLERK_SECRET_KEY production
vercel env add NEXT_PUBLIC_COLLECTOR_URL production
# Paste your Render URL: https://llmobserve-api.onrender.com

vercel --prod
```

## Useful Render CLI Commands

```bash
# View logs
render logs

# Restart service
render services restart

# View service status
render services list

# View environment variables
render env list

# Set environment variable
render env set KEY_NAME "value"

# Delete environment variable
render env unset KEY_NAME
```

## Troubleshooting

### Service won't start
```bash
# Check logs
render logs

# Common issues:
# - DATABASE_URL wrong → Check connection string
# - Missing env vars → Check render env list
# - Port binding → Make sure using $PORT in start command
```

### Database connection fails
- Verify DATABASE_URL is correct
- Check Supabase allows connections from Render IPs
- Test connection: `psql "your-database-url" -c "SELECT 1;"`

## Cost

Render Free Tier:
- 750 hours/month free
- Sleeps after 15 min inactivity (wakes on request)
- Perfect for development/testing

Paid Plans:
- Starter: $7/month (always on)
- Standard: $25/month (better performance)

---

**Quick Start:**
1. `render login`
2. `render blueprint launch`
3. Set env vars
4. Deploy frontend to Vercel
5. Update ALLOWED_ORIGINS with Vercel URL
6. Done! 🎉


