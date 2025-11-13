#!/bin/bash

# Production Deployment Setup Script
# Run this after providing domain, Clerk keys, and email service credentials

set -e

echo "🚀 LLMObserve Production Deployment Setup"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${YELLOW}⚠ Railway CLI not found. Installing...${NC}"
    npm install -g @railway/cli
fi

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${YELLOW}⚠ Vercel CLI not found. Installing...${NC}"
    npm install -g vercel
fi

# Prompt for domain
read -p "Enter your domain (e.g., llmobserve.com): " DOMAIN
if [ -z "$DOMAIN" ]; then
    echo -e "${RED}✗ Domain is required${NC}"
    exit 1
fi

FRONTEND_DOMAIN="app.$DOMAIN"
BACKEND_DOMAIN="api.$DOMAIN"

echo ""
echo -e "${GREEN}✓ Domain configured:${NC}"
echo "  Frontend: https://$FRONTEND_DOMAIN"
echo "  Backend: https://$BACKEND_DOMAIN"
echo ""

# Prompt for Clerk keys
read -p "Enter Clerk Publishable Key (pk_live_...): " CLERK_PUBLISHABLE_KEY
read -p "Enter Clerk Secret Key (sk_live_...): " CLERK_SECRET_KEY

if [ -z "$CLERK_PUBLISHABLE_KEY" ] || [ -z "$CLERK_SECRET_KEY" ]; then
    echo -e "${RED}✗ Clerk keys are required${NC}"
    exit 1
fi

# Prompt for email service
echo ""
echo "Email Service Options:"
echo "1) SendGrid (Recommended)"
echo "2) SMTP (Gmail/Outlook)"
echo "3) AWS SES"
read -p "Choose email service (1-3): " EMAIL_CHOICE

case $EMAIL_CHOICE in
    1)
        EMAIL_PROVIDER="sendgrid"
        read -p "Enter SendGrid API Key (SG.xxx): " SENDGRID_API_KEY
        if [ -z "$SENDGRID_API_KEY" ]; then
            echo -e "${RED}✗ SendGrid API key required${NC}"
            exit 1
        fi
        ;;
    2)
        EMAIL_PROVIDER="smtp"
        read -p "Enter SMTP Host (e.g., smtp.gmail.com): " SMTP_HOST
        read -p "Enter SMTP Port (e.g., 587): " SMTP_PORT
        read -p "Enter SMTP Username: " SMTP_USERNAME
        read -p "Enter SMTP Password: " SMTP_PASSWORD
        if [ -z "$SMTP_HOST" ] || [ -z "$SMTP_USERNAME" ] || [ -z "$SMTP_PASSWORD" ]; then
            echo -e "${RED}✗ SMTP credentials required${NC}"
            exit 1
        fi
        ;;
    3)
        EMAIL_PROVIDER="ses"
        read -p "Enter AWS SES Region (e.g., us-east-1): " AWS_SES_REGION
        read -p "Enter AWS Access Key ID: " AWS_ACCESS_KEY_ID
        read -p "Enter AWS Secret Access Key: " AWS_SECRET_ACCESS_KEY
        if [ -z "$AWS_SES_REGION" ] || [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
            echo -e "${RED}✗ AWS SES credentials required${NC}"
            exit 1
        fi
        ;;
    *)
        echo -e "${RED}✗ Invalid choice${NC}"
        exit 1
        ;;
esac

# Prompt for database
read -p "Enter Database URL (Supabase or Railway): " DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}✗ Database URL required${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ All credentials collected${NC}"
echo ""

# Deploy backend to Railway
echo -e "${YELLOW}📦 Deploying backend to Railway...${NC}"
cd collector

# Login to Railway
if ! railway whoami &> /dev/null; then
    echo "Please login to Railway:"
    railway login
fi

# Initialize Railway project if not already
if [ ! -f ".railway/config.json" ]; then
    railway init
fi

# Set environment variables
echo "Setting Railway environment variables..."
railway variables set DATABASE_URL="$DATABASE_URL"
railway variables set ENV=production
railway variables set SERVICE_NAME=llmobserve-api
railway variables set ALLOW_CONTENT_CAPTURE=false
railway variables set CLERK_SECRET_KEY="$CLERK_SECRET_KEY"
railway variables set EMAIL_PROVIDER="$EMAIL_PROVIDER"

case $EMAIL_CHOICE in
    1)
        railway variables set SENDGRID_API_KEY="$SENDGRID_API_KEY"
        ;;
    2)
        railway variables set SMTP_HOST="$SMTP_HOST"
        railway variables set SMTP_PORT="$SMTP_PORT"
        railway variables set SMTP_USERNAME="$SMTP_USERNAME"
        railway variables set SMTP_PASSWORD="$SMTP_PASSWORD"
        ;;
    3)
        railway variables set AWS_SES_REGION="$AWS_SES_REGION"
        railway variables set AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID"
        railway variables set AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY"
        ;;
esac

# Deploy
railway up

# Get Railway URL
RAILWAY_URL=$(railway domain 2>/dev/null || echo "your-app.up.railway.app")
echo -e "${GREEN}✓ Backend deployed to: $RAILWAY_URL${NC}"

cd ..

# Deploy frontend to Vercel
echo ""
echo -e "${YELLOW}📦 Deploying frontend to Vercel...${NC}"
cd web

# Login to Vercel
if ! vercel whoami &> /dev/null; then
    echo "Please login to Vercel:"
    vercel login
fi

# Set environment variables
echo "Setting Vercel environment variables..."
vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY production <<< "$CLERK_PUBLISHABLE_KEY"
vercel env add CLERK_SECRET_KEY production <<< "$CLERK_SECRET_KEY"
vercel env add NEXT_PUBLIC_COLLECTOR_URL production <<< "https://$BACKEND_DOMAIN"

# Deploy
vercel --prod

echo -e "${GREEN}✓ Frontend deployed${NC}"

cd ..

echo ""
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo ""
echo "Next Steps:"
echo "1. Add DNS records:"
echo "   - A record: app → Vercel IP (check Vercel dashboard)"
echo "   - CNAME record: api → $RAILWAY_URL"
echo ""
echo "2. Update Clerk webhook URL:"
echo "   https://$BACKEND_DOMAIN/webhooks/clerk"
echo ""
echo "3. Update Clerk allowed origins:"
echo "   https://$FRONTEND_DOMAIN"
echo ""
echo "4. Test deployment:"
echo "   - Frontend: https://$FRONTEND_DOMAIN"
echo "   - Backend: https://$BACKEND_DOMAIN/health"
echo ""
echo -e "${GREEN}🎉 Ready to launch!${NC}"

