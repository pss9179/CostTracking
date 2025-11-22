# What Does the CLI Actually Do?

## Quick Answer

**The CLI does NOT run your code or track costs automatically.**

The CLI's job is to:
1. **Analyze your codebase** - Understand structure, find LLM calls
2. **Auto-instrument code** - Add labels/sections automatically
3. **Map costs to code** - Show which parts cost the most

**The SDK tracks costs** when you run your code.

---

## Two Separate Things

### 1. CLI = Code Analysis Tool (Static)
- Runs BEFORE you execute code
- Analyzes code files
- Modifies code (adds labels)
- Shows cost breakdown

### 2. SDK = Cost Tracking (Runtime)
- Runs WHEN you execute code
- Tracks API calls
- Sends costs to backend
- Shows in dashboard

---

## User Flow

### Step 1: Get API Key
```
Dashboard → Settings → Create API Key
```

### Step 2: Install Library
```bash
pip install llmobserve
# Installs both SDK + CLI
```

### Step 3A: Use CLI (Optional - Code Analysis)
```bash
# Analyze codebase structure
llmobserve analyze .

# Output:
# 📊 Semantic Cost Analysis:
# Summarization: $45.20 (60%)
# Twitch Streaming: $18.50 (25%)
# Botting: $11.30 (15%)
```

**What CLI does:**
- Scans your code files
- Understands semantic sections
- Maps to costs (if SDK already integrated)
- Shows breakdown

**What CLI does NOT do:**
- ❌ Run your code
- ❌ Track costs automatically
- ❌ Execute anything

### Step 3B: Use SDK (Required - Cost Tracking)
```python
import llmobserve

llmobserve.observe(
    collector_url="...",
    api_key="llmo_sk_..."
)

# Your code runs here
# SDK tracks costs automatically
```

**What SDK does:**
- Tracks API calls as code runs
- Sends costs to backend
- Shows in dashboard

**What SDK does NOT do:**
- ❌ Analyze code structure
- ❌ Add labels automatically (unless you use CLI first)

---

## Two Use Cases

### Use Case 1: CLI for Code Analysis
**When:** Before integrating SDK or to understand existing code

```bash
# User runs CLI
llmobserve analyze .

# CLI:
# 1. Scans codebase
# 2. Finds LLM API calls
# 3. Understands semantic sections
# 4. Maps to costs (if SDK integrated)
# 5. Shows breakdown
```

**Output:**
```
📊 Semantic Cost Analysis:

Summarization (60% - $45.20)
├─ agents/summarizer.py:summarize_article
├─ 1,234 API calls
└─ Avg: $0.037/call

Twitch Streaming (25% - $18.50)
├─ streaming/twitch.py:stream_to_twitch
└─ 456 API calls
```

**User sees:** Which parts of code cost the most

### Use Case 2: SDK for Cost Tracking
**When:** Code is running

```python
import llmobserve

llmobserve.observe(api_key="...")

# Code runs
response = openai.ChatCompletion.create(...)

# SDK automatically:
# 1. Intercepts API call
# 2. Calculates cost
# 3. Sends to backend
# 4. Shows in dashboard
```

**User sees:** Costs in dashboard as code runs

---

## Complete Flow

### Option A: CLI First (Recommended)
```
1. Get API key
2. pip install llmobserve
3. llmobserve analyze .  ← Understand codebase
4. Add SDK to code: llmobserve.observe(api_key="...")
5. Run code → Costs tracked → Dashboard
```

### Option B: SDK First
```
1. Get API key
2. pip install llmobserve
3. Add SDK to code: llmobserve.observe(api_key="...")
4. Run code → Costs tracked → Dashboard
5. llmobserve analyze .  ← See cost breakdown later
```

### Option C: CLI Auto-Instrumentation
```
1. Get API key
2. pip install llmobserve
3. llmobserve scan .  ← Find LLM code
4. llmobserve review  ← Review suggestions
5. llmobserve apply   ← Auto-add labels to code
6. Add SDK to code: llmobserve.observe(api_key="...")
7. Run code → Costs tracked with labels → Dashboard
```

---

## What CLI Commands Do

### `llmobserve scan`
- Scans codebase for LLM-related code
- Finds API calls, agent patterns
- **Does NOT modify code**
- **Does NOT run code**

### `llmobserve analyze` (New - Needs Implementation)
- Analyzes semantic sections
- Maps to costs
- Shows breakdown
- **Does NOT modify code**
- **Does NOT run code**

### `llmobserve review`
- Shows suggested code changes
- Interactive approval
- **Does NOT modify code yet**
- **Does NOT run code**

### `llmobserve apply`
- Applies suggested changes
- Adds labels to code
- **Modifies code files**
- **Does NOT run code**

### `llmobserve instrument` (Legacy)
- Auto-instruments single file
- Adds labels automatically
- **Modifies code file**
- **Does NOT run code**

---

## Key Point

**CLI = Code Analysis & Modification Tool**
- Works on code files
- Doesn't execute anything
- Helps understand and improve code

**SDK = Runtime Cost Tracking**
- Works when code runs
- Tracks API calls
- Sends costs to backend

**User runs their own code** - CLI and SDK don't execute it!

---

## Example

```bash
# Step 1: Analyze codebase
llmobserve analyze .
# Output: "Summarization is 60% of costs"

# Step 2: User modifies code (manually or via CLI)
# Maybe optimize summarization function

# Step 3: User runs their code
python my_agent.py
# SDK tracks costs as code runs

# Step 4: Check dashboard
# See updated costs
```

---

## Summary

**User does:**
1. Get API key
2. `pip install llmobserve` (gets SDK + CLI)
3. **CLI**: Analyze codebase (optional)
4. **SDK**: Track costs (required)
5. **User**: Run their own code
6. **Dashboard**: See costs

**CLI role:**
- Analyze code structure
- Auto-instrument code
- Map costs to code sections

**SDK role:**
- Track costs when code runs
- Send to backend
- Show in dashboard

**User role:**
- Run their code
- View dashboard

