#!/bin/bash
# Copy and paste these commands one by one

# ============================================
# STEP 1: Login (run these manually - they open browser)
# ============================================
railway login
vercel login

# ============================================
# STEP 2: Deploy Backend to Railway
# ============================================
cd collector
railway init

# Set environment variables (replace with your actual values)
railway variables set DATABASE_URL="postgresql://postgres:EIPloItGt5NBmrLn@db.vcecetcumnreuzojtqin.supabase.co:5432/postgres"
railway variables set ENV=production
railway variables set SERVICE_NAME=llmobserve-api
railway variables set ALLOW_CONTENT_CAPTURE=false
railway variables set CLERK_SECRET_KEY="sk_live_xxxxx"  # REPLACE with production key
railway variables set EMAIL_PROVIDER=sendgrid
railway variables set SENDGRID_API_KEY="SG.xxxxx"  # REPLACE with your SendGrid key
railway variables set ALLOWED_ORIGINS="*"

# Deploy
railway up

# Get your Railway URL
railway domain
# COPY THIS URL - you'll need it for frontend

# ============================================
# STEP 3: Deploy Frontend to Vercel
# ============================================
cd ../web
vercel

# Set environment variables (replace with your actual values)
vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY production
# When prompted, paste: pk_live_xxxxx (REPLACE with production key)

vercel env add CLERK_SECRET_KEY production
# When prompted, paste: sk_live_xxxxx (REPLACE with production key)

vercel env add NEXT_PUBLIC_COLLECTOR_URL production
# When prompted, paste: https://your-app.up.railway.app (from Step 2)

# Deploy to production
vercel --prod

