#!/bin/bash
# Deploy to Vercel for Google OAuth testing

echo "🚀 Deploying to Vercel..."
echo ""
echo "Step 1: Login to Vercel (will open browser)"
vercel login

echo ""
echo "Step 2: Link project"
vercel link

echo ""
echo "Step 3: Setting environment variables from .env.local..."
# Read .env.local and set variables
if [ -f .env.local ]; then
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue
        
        # Remove quotes from value
        value=$(echo "$value" | sed 's/^"//;s/"$//')
        
        echo "Setting $key..."
        vercel env add "$key" production <<< "$value" 2>/dev/null || \
        vercel env add "$key" preview <<< "$value" 2>/dev/null || \
        vercel env add "$key" development <<< "$value" 2>/dev/null || echo "  ⚠️  Could not set $key automatically"
    done < .env.local
fi

echo ""
echo "Step 4: Deploying to production..."
vercel --prod

echo ""
echo "✅ Deployment complete!"
echo "📝 Next steps:"
echo "1. Copy your Vercel URL (e.g., https://your-app.vercel.app)"
echo "2. Go to https://dashboard.clerk.com"
echo "3. Add your Vercel URL to 'Allowed Origins'"
echo "4. Configure Google OAuth in Clerk dashboard"
