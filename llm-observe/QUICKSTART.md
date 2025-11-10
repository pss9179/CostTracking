# Quick Start Guide

## 🚀 Run Everything

### Terminal 1: Backend
```bash
cd backend
uvicorn llmobserve.main:app --reload
```

### Terminal 2: Frontend  
```bash
cd frontend
npm run dev
```

### Terminal 3: Run Test Agents
```bash
cd backend
python test_agents.py
```

Then open **http://localhost:3000** to see the beautiful dashboard! 🎉

## What You'll See

1. **Workflow Traces Tab**: Professional tree visualization showing:
   - Agent workflows (customer-support-001, calendar-email-assistant-001)
   - All API calls (GPT, Pinecone, Vapi, Google APIs)
   - Costs and durations for each call
   - Expandable/collapsible tree structure

2. **Analytics Tab**: 
   - Cost by provider (pie chart)
   - Cost over time (line chart)

3. **Tenants Tab**:
   - Per-tenant cost breakdown
   - Click tenant badges to filter

## Test Agents

The `test_agents.py` script simulates:

**Agent 1 - Customer Support** (tenant: acme-corp):
- Pinecone query (before agent)
- GPT chat completion (tool call 1)
- GPT embedding (tool call 2)  
- Pinecone upsert (tool call 3)
- Vapi call creation (after agent)
- Vapi status check (after agent)

**Agent 2 - Calendar & Email Assistant** (tenant: tech-startup):
- Google Calendar list events (before agent)
- GPT analyze calendar (tool call 1)
- Gmail list messages (tool call 2)
- GPT analyze emails (tool call 3)
- Google Calendar create event (tool call 4)
- Gmail get message (after agent)

Each agent makes multiple API calls and tool invocations, all tracked automatically!

