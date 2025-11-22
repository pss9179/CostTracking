# Semantic Cost Tracking - Required Flow

## What User Wants

**Automatic semantic cost tracking** - Show ALL costs mapped to semantic code sections automatically.

**NOT optional** - This should happen automatically for all users.

---

## Required User Flow

### Step 1: Get API Key
```
Dashboard → Settings → Create API Key
```

### Step 2: Install Package
```bash
pip install llmobserve
# Installs SDK + CLI (both required)
```

### Step 3: Analyze Codebase (REQUIRED - Not Optional!)
```bash
llmobserve analyze .

# CLI:
# 1. Scans codebase
# 2. Understands semantic sections (summarization, streaming, botting, etc.)
# 3. Creates semantic mapping
# 4. Stores in .llmobserve/semantic_map.json
```

**This is REQUIRED** - Without this, semantic tracking won't work!

### Step 4: Use SDK in Code
```python
import llmobserve

llmobserve.observe(
    collector_url="...",
    api_key="llmo_sk_..."
)

# Code runs
# SDK automatically maps costs to semantic sections
```

### Step 5: View Dashboard
```
Dashboard automatically shows:
- Summarization: $45.20 (60%)
- Twitch Streaming: $18.50 (25%)
- Botting: $11.30 (15%)
```

**No manual labeling needed** - It's automatic!

---

## How It Works

### 1. CLI Analysis (Required First Step)
```bash
llmobserve analyze .
```

**What it does:**
- Scans all Python files
- Uses AI to understand semantic sections
- Creates mapping: `file:function → semantic_label`
- Saves to `.llmobserve/semantic_map.json`

**Example output:**
```json
{
  "agents/summarizer.py": {
    "summarize_article": "summarization",
    "summarize_batch": "summarization"
  },
  "streaming/twitch.py": {
    "stream_to_twitch": "twitch_streaming"
  },
  "bot/response.py": {
    "bot_response": "botting"
  }
}
```

### 2. SDK Runtime Tracking
When code runs:
- SDK intercepts API calls
- Looks up function name in semantic map
- Tags cost with semantic label
- Sends to backend

**Example:**
```python
# User's code
def summarize_article(text):
    response = openai.ChatCompletion.create(...)  # ← SDK intercepts

# SDK automatically:
# 1. Sees function name: "summarize_article"
# 2. Looks up in semantic_map.json → "summarization"
# 3. Tags cost: {semantic_label: "summarization", cost: $0.15}
# 4. Sends to backend
```

### 3. Dashboard Display
Backend aggregates costs by semantic label:
```sql
SELECT semantic_label, SUM(cost) 
FROM trace_events 
GROUP BY semantic_label
```

Dashboard shows:
```
Semantic Cost Breakdown:
├─ Summarization: $45.20 (60%)
├─ Twitch Streaming: $18.50 (25%)
└─ Botting: $11.30 (15%)
```

---

## Implementation Plan

### Phase 1: CLI Semantic Analysis
**Command:** `llmobserve analyze .`

**What it does:**
1. Scan codebase (AST parsing)
2. Identify functions with LLM calls
3. Use AI to label semantic sections
4. Save semantic map

**Output:**
```
📊 Semantic Analysis Complete!

Found 12 semantic sections:
├─ Summarization (3 functions)
├─ Twitch Streaming (2 functions)
├─ Botting (4 functions)
└─ Research (3 functions)

Saved to: .llmobserve/semantic_map.json
```

### Phase 2: SDK Auto-Mapping
**When SDK intercepts API call:**
1. Get function name from call stack
2. Look up in semantic_map.json
3. Tag cost with semantic label
4. Send to backend

**Code changes needed:**
- Modify `event_creator.py` to add semantic label
- Read semantic_map.json at startup
- Map function names to semantic labels

### Phase 3: Dashboard Display
**New view:** `/semantic-costs`

**Shows:**
- Semantic cost breakdown
- Code heatmap
- File/function breakdown

---

## Required vs Optional

### REQUIRED Steps:
1. ✅ Get API key
2. ✅ Install: `pip install llmobserve`
3. ✅ Run: `llmobserve analyze .` ← **REQUIRED!**
4. ✅ Use SDK: `llmobserve.observe(api_key="...")`
5. ✅ Run code
6. ✅ View dashboard → See semantic breakdown

### What Happens If User Skips Step 3?
**Fallback:** Show "Untracked" costs
- Costs still tracked
- But not mapped to semantic sections
- Dashboard shows: "Untracked: $75.00 (100%)"

**Solution:** Make it clear that `llmobserve analyze .` is required!

---

## Updated User Onboarding

### Dashboard Instructions:
```
Welcome! To enable semantic cost tracking:

1. Get your API key (already done ✓)
2. Install: pip install llmobserve
3. Run: llmobserve analyze .
4. Add to code: llmobserve.observe(api_key="...")
5. Run your code
6. View semantic breakdown here!
```

### CLI Output:
```
✅ Semantic analysis complete!

Next steps:
1. Add to your code:
   import llmobserve
   llmobserve.observe(api_key="llmo_sk_...")

2. Run your code

3. View dashboard to see semantic cost breakdown!
```

---

## Key Changes Needed

1. **Make CLI analysis required** - Not optional
2. **SDK auto-maps costs** - Uses semantic map automatically
3. **Dashboard shows semantic breakdown** - By default
4. **Clear onboarding** - Users know to run `llmobserve analyze .`

---

## Example Flow

```bash
# Step 1: User installs
pip install llmobserve

# Step 2: User runs analysis (REQUIRED)
llmobserve analyze .
# Output: "Found 5 semantic sections. Saved to .llmobserve/semantic_map.json"

# Step 3: User adds SDK to code
# Code: llmobserve.observe(api_key="...")

# Step 4: User runs code
python my_agent.py

# Step 5: Dashboard automatically shows:
# "Summarization: $45.20 (60%)"
# "Twitch Streaming: $18.50 (25%)"
# etc.
```

**No manual labeling** - Everything is automatic!

