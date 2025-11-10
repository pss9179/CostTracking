# LLMObserve MVP

Lightweight AI workflow tracking and cost monitoring system.

## Quick Start

### Backend

```bash
cd backend
pip install -e .
uvicorn llmobserve.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Run Test Agents

```bash
cd backend
python test_agents.py
```

Then open http://localhost:3000 to see the dashboard!

## Features

- **Real-time Tracking**: Automatically tracks AI API calls, tool usage, and costs
- **Multi-Tenant Support**: Track usage per tenant and workflow
- **Beautiful Dashboard**: Professional ShadCN UI with tree visualization
- **Cost Analytics**: Charts and metrics for cost analysis
- **Workflow Traces**: Visual tree view of all API calls and tool invocations

## Test Agents

The `test_agents.py` script simulates two agents:

1. **Agent 1 - Customer Support**: Uses GPT, Pinecone, and Vapi
2. **Agent 2 - Calendar & Email Assistant**: Uses GPT, Google Calendar, and Gmail APIs

Each agent makes multiple tool calls and API calls before/after agent execution.
