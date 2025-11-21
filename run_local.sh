#!/bin/bash

# LLMObserve Local Development Runner
# This script starts all services needed for local development

set -e

echo "🚀 Starting LLMObserve Local Development Environment"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi

# Check if pnpm is installed (for web)
if ! command -v pnpm &> /dev/null; then
    echo -e "${YELLOW}⚠️  pnpm not found, trying npm instead...${NC}"
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}❌ npm is not installed${NC}"
        exit 1
    fi
    USE_NPM=true
else
    USE_NPM=false
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"
echo ""

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${YELLOW}⚠️  Port $1 is already in use${NC}"
        return 1
    fi
    return 0
}

# Check ports
echo "Checking ports..."
check_port 8000 || { echo -e "${RED}Port 8000 (collector) is in use. Please stop the service using it.${NC}"; exit 1; }
check_port 9000 || { echo -e "${RED}Port 9000 (proxy) is in use. Please stop the service using it.${NC}"; exit 1; }
check_port 3000 || { echo -e "${RED}Port 3000 (web) is in use. Please stop the service using it.${NC}"; exit 1; }
echo -e "${GREEN}✅ All ports available${NC}"
echo ""

# Check environment files
echo "Checking environment configuration..."

if [ ! -f "collector/.env" ]; then
    echo -e "${YELLOW}⚠️  collector/.env not found. Creating from template...${NC}"
    cat > collector/.env << EOF
DATABASE_URL=postgresql://postgres:password@localhost:5432/llmobserve
CLERK_SECRET_KEY=sk_test_your_clerk_secret_key_here
ENV=development
ALLOW_CONTENT_CAPTURE=false
EOF
    echo -e "${YELLOW}⚠️  Please update collector/.env with your actual credentials${NC}"
fi

if [ ! -f "web/.env.local" ]; then
    echo -e "${YELLOW}⚠️  web/.env.local not found. Creating from template...${NC}"
    cat > web/.env.local << EOF
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your_clerk_publishable_key_here
CLERK_SECRET_KEY=sk_test_your_clerk_secret_key_here
NEXT_PUBLIC_COLLECTOR_URL=http://localhost:8000
EOF
    echo -e "${YELLOW}⚠️  Please update web/.env.local with your actual Clerk keys${NC}"
fi

echo -e "${GREEN}✅ Environment files checked${NC}"
echo ""

# Install dependencies
echo "Installing dependencies..."

# Install collector dependencies
echo "📦 Installing collector dependencies..."
cd collector
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q -e .
cd ..

# Install proxy dependencies
echo "📦 Installing proxy dependencies..."
cd proxy
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
cd ..

# Install web dependencies
echo "📦 Installing web dependencies..."
cd web
if [ "$USE_NPM" = true ]; then
    npm install --silent
else
    pnpm install --silent
fi
cd ..

echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Create log directory
mkdir -p logs

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
    kill $COLLECTOR_PID $PROXY_PID $WEB_PID 2>/dev/null || true
    wait $COLLECTOR_PID $PROXY_PID $WEB_PID 2>/dev/null || true
    echo -e "${GREEN}✅ Services stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start collector
echo -e "${GREEN}🚀 Starting Collector API (port 8000)...${NC}"
cd collector
source venv/bin/activate
export $(cat .env | xargs)
python3 -m uvicorn main:app --reload --port 8000 > ../logs/collector.log 2>&1 &
COLLECTOR_PID=$!
cd ..
sleep 3

# Start proxy
echo -e "${GREEN}🚀 Starting Proxy Server (port 9000)...${NC}"
cd proxy
source venv/bin/activate
export LLMOBSERVE_COLLECTOR_URL="http://localhost:8000"
python3 -m uvicorn main:app --reload --port 9000 > ../logs/proxy.log 2>&1 &
PROXY_PID=$!
cd ..
sleep 2

# Start web
echo -e "${GREEN}🚀 Starting Web Dashboard (port 3000)...${NC}"
cd web
if [ "$USE_NPM" = true ]; then
    npm run dev > ../logs/web.log 2>&1 &
else
    pnpm dev > ../logs/web.log 2>&1 &
fi
WEB_PID=$!
cd ..
sleep 3

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ All services are running!${NC}"
echo ""
echo -e "${GREEN}📍 Services:${NC}"
echo -e "   • Collector API:  ${GREEN}http://localhost:8000${NC}"
echo -e "   • Proxy Server:   ${GREEN}http://localhost:9000${NC}"
echo -e "   • Web Dashboard:  ${GREEN}http://localhost:3000${NC}"
echo ""
echo -e "${GREEN}📋 Logs:${NC}"
echo -e "   • Collector: logs/collector.log"
echo -e "   • Proxy:     logs/proxy.log"
echo -e "   • Web:       logs/web.log"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo -e "   • Press Ctrl+C to stop all services"
echo -e "   • Check logs/ directory for detailed logs"
echo -e "   • Make sure your DATABASE_URL in collector/.env is correct"
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Wait for all processes
wait $COLLECTOR_PID $PROXY_PID $WEB_PID



