#!/bin/bash

# Add SendGrid configuration to Railway
echo "🔧 Setting up SendGrid email alerts..."
echo ""
echo "Add these environment variables to Railway:"
echo ""
echo "EMAIL_PROVIDER=sendgrid"
echo "SENDGRID_API_KEY=<your_sendgrid_api_key>"
echo "FROM_EMAIL=alerts@llmobserve.com"
echo ""
echo "✅ Once added, restart the Railway service"
echo ""
echo "🧪 Test by creating a spending cap with a low limit ($0.10)"
echo "   and triggering it with a few API calls."
echo ""

