#!/bin/bash
# One-command Railway deployment
# Run this AFTER creating a service in Railway dashboard

set -e

echo "🚂 Setting all environment variables..."

railway variables \
  --set "DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres" \
  --set "ENV=production" \
  --set "SERVICE_NAME=llmobserve-api" \
  --set "ALLOW_CONTENT_CAPTURE=false" \
  --set "CLERK_SECRET_KEY=sk_live_YOUR_CLERK_SECRET_KEY" \
  --set "ALLOWED_ORIGINS=*" \
  --set "TENANT_HEADER=x-tenant-id"

echo "✅ Variables set!"
echo ""
echo "🚀 Deploying..."
railway up

echo ""
echo "✅ Deployed! Getting URL..."
railway domain

