#!/bin/bash
# Railway Deployment Script
# Run this AFTER you've linked a Railway project

set -e

echo "🚂 Setting Railway environment variables..."

# Database - Replace with your actual DATABASE_URL
railway variables --set "DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres"

# Environment
railway variables --set "ENV=production"
railway variables --set "SERVICE_NAME=llmobserve-api"
railway variables --set "ALLOW_CONTENT_CAPTURE=false"

# Clerk - Replace with your actual CLERK_SECRET_KEY
railway variables --set "CLERK_SECRET_KEY=sk_live_YOUR_CLERK_SECRET_KEY"

# CORS
railway variables --set "ALLOWED_ORIGINS=*"

# Multi-tenancy
railway variables --set "TENANT_HEADER=x-tenant-id"

echo "✅ Environment variables set!"
echo ""
echo "🚀 Deploying to Railway..."
railway up

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Get your URL:"
echo "   railway domain"
echo ""
echo "📊 View logs:"
echo "   railway logs"

