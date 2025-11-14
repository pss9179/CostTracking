#!/bin/bash
# Automated deployment script for Render + Vercel

set -e

echo "🚀 Starting deployment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check Render login
echo -e "${YELLOW}Step 1: Checking Render authentication...${NC}"
if ! render whoami &>/dev/null; then
    echo "⚠️  Not logged into Render. Please run: render login"
    echo "   This will open your browser to authenticate."
    exit 1
fi
echo -e "${GREEN}✅ Logged into Render${NC}"

# Step 2: Create/Update Render service
echo -e "${YELLOW}Step 2: Setting up Render service...${NC}"
echo "Note: If service doesn't exist, create it in Render dashboard first:"
echo "  1. Go to https://dashboard.render.com"
echo "  2. Click 'New' → 'Web Service'"
echo "  3. Connect GitHub repo or use these settings:"
echo "     - Root Directory: collector"
echo "     - Build Command: pip install -r requirements.txt"
echo "     - Start Command: uvicorn main:app --host 0.0.0.0 --port \$PORT"
echo ""
read -p "Press Enter once service is created, or 's' to skip..."

# Step 3: Set Render environment variables
echo -e "${YELLOW}Step 3: Setting Render environment variables...${NC}"

# Read from .env file
if [ -f "collector/.env" ]; then
    DATABASE_URL=$(grep DATABASE_URL collector/.env | cut -d '=' -f2-)
    CLERK_SECRET_KEY=$(grep CLERK_SECRET_KEY collector/.env | cut -d '=' -f2-)
    
    echo "Setting DATABASE_URL..."
    render env set DATABASE_URL "$DATABASE_URL" || echo "⚠️  Could not set DATABASE_URL"
    
    echo "Setting CLERK_SECRET_KEY..."
    render env set CLERK_SECRET_KEY "$CLERK_SECRET_KEY" || echo "⚠️  Could not set CLERK_SECRET_KEY"
    
    echo "Setting other env vars..."
    render env set ENV "production" || true
    render env set SERVICE_NAME "llmobserve-api" || true
    render env set ALLOW_CONTENT_CAPTURE "false" || true
    render env set ALLOWED_ORIGINS "*" || true
    
    echo -e "${GREEN}✅ Environment variables set${NC}"
else
    echo "⚠️  collector/.env not found. Set env vars manually in Render dashboard."
fi

# Step 4: Get Render URL
echo -e "${YELLOW}Step 4: Getting Render service URL...${NC}"
RENDER_URL=$(render services list -o json | jq -r '.[0].service.serviceDetails.url' 2>/dev/null || echo "")
if [ -z "$RENDER_URL" ]; then
    echo "⚠️  Could not get Render URL automatically."
    echo "   Please get it from Render dashboard and set it manually."
    read -p "Enter your Render URL (e.g., https://llmobserve-api.onrender.com): " RENDER_URL
fi
echo -e "${GREEN}✅ Render URL: $RENDER_URL${NC}"

# Step 5: Deploy frontend to Vercel
echo -e "${YELLOW}Step 5: Deploying frontend to Vercel...${NC}"
cd web

# Check if already linked
if [ ! -f ".vercel/project.json" ]; then
    echo "Linking to Vercel project..."
    vercel --yes
fi

# Set environment variables
echo "Setting Vercel environment variables..."
if [ -f ".env.local" ]; then
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=$(grep NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY .env.local | cut -d '=' -f2-)
    CLERK_SECRET_KEY=$(grep CLERK_SECRET_KEY .env.local | cut -d '=' -f2-)
    
    echo "$NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY" | vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY production
    echo "$CLERK_SECRET_KEY" | vercel env add CLERK_SECRET_KEY production
    echo "$RENDER_URL" | vercel env add NEXT_PUBLIC_COLLECTOR_URL production
    
    echo -e "${GREEN}✅ Vercel environment variables set${NC}"
fi

# Deploy
echo "Deploying to Vercel production..."
vercel --prod --yes

echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Update ALLOWED_ORIGINS in Render with your Vercel URL"
echo "2. Test your deployment"
echo "3. Set up Clerk webhooks if needed"

