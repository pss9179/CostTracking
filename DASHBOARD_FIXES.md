# Dashboard UI Fixes - Clean Agent-Level View

## 🎯 Problems Fixed

### **Before:**
- ❌ Dashboard showed internal sections like `retry:llm_analysis:attempt_1`
- ❌ "Top Sections" showed run-by-run data, not agent aggregation
- ❌ 7-day cost trend chart was useless with 1 day of data
- ❌ No clear distinction between agent-level and internal logs

### **After:**
- ✅ Dashboard shows top-level agent sections: `agent:research_assistant`
- ✅ "Top Agents & Workflows" shows clean agent-level data
- ✅ API cost breakdown with visual bars (replaces useless 7-day chart)
- ✅ Internal retry/test sections filtered out

---

## 🔧 Technical Changes

### **Backend (`collector/routers/runs.py`)**

1. **Added `extract_top_level_section()` helper**
   ```python
   def extract_top_level_section(section_path: str) -> str:
       # "agent:research_assistant/step:analyze/retry:attempt_1" 
       # → "agent:research_assistant"
       
       first_segment = section_path.split("/")[0]
       
       # Filter out internal sections
       if first_segment.startswith("retry:") or first_segment.startswith("test:"):
           return None
       
       return first_segment
   ```

2. **Updated `/runs/latest` endpoint**
   - Now extracts `top_section` from `section_path` (not leaf `section`)
   - Returns: `"top_section": "agent:research_assistant"` ✅
   - Instead of: `"top_section": "retry:llm_analysis:attempt_1"` ❌

3. **Added `/runs/sections/top` endpoint** (NEW)
   - Aggregates costs by agent/tool/step level
   - Filters out internal retry/test sections
   - Returns clean list of agents with costs

### **Frontend (`web/app/page.tsx`)**

1. **Replaced 7-Day Trend Chart** with **API Cost Breakdown**
   - Shows provider costs with visual bars
   - Displays percentage of total
   - Actually useful for devs! 📊

2. **Added "Top Agents & Workflows" Card**
   - Shows `agent:research_assistant`, not `retry:llm_analysis`
   - Filters out test/retry sections client-side
   - Clean agent-level view

3. **Removed Duplicate/Unused Code**
   - Removed duplicate "Costs by API Provider" card
   - Removed unused `costTrendData` calculation
   - Removed unused `CostTrendChart` import

---

## 📊 New Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│ LLM Cost Dashboard              [Tenant: acme-corp ▼]       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [$0.000138]  [2 Calls]  [$0.000069/call]  [2 Runs]        │
│  Total Cost   API Calls   Avg Cost/Call    Total Runs      │
│                                                               │
├──────────────────────────────┬──────────────────────────────┤
│                              │                              │
│  Costs by API Provider (24h) │  Top Agents & Workflows     │
│  ───────────────────────────│  ──────────────────────────  │
│  openai      ████████░░  $0.1│  agent:research_assistant   │
│  pinecone    ██░░░░░░░░  $0.0│    $0.00014 | 2 calls      │
│                              │                              │
└──────────────────────────────┴──────────────────────────────┘
```

**Left Card:** Shows API-level costs (OpenAI, Pinecone)
**Right Card:** Shows agent-level costs (agent:*, tool:*, step:*)

---

## 🎨 What You See Now

### **Dashboard (acme-corp tenant):**
```
Top Agents & Workflows (24h)
┌──────────────────────────────┬──────┬───────┐
│ Agent/Tool                   │ Cost │ Calls │
├──────────────────────────────┼──────┼───────┤
│ agent:research_assistant     │ $0.  │ 4     │
│                              │00014 │       │
└──────────────────────────────┴──────┴───────┘
```

### **Runs Page:**
```
Run ID          Cost      Top Section
b69f6a28...     $0.0121   agent:research_assistant ✅
```

### **Run Detail Page:**
Hierarchical tree shows:
```
🤖 agent:research_assistant ($0.00007, 2.7s)
   🔍 tool:web_search
   💾 tool:database_lookup
   🧠 step:analyze_results
      🔁 retry:llm_analysis:attempt_1  ← Hidden unless expanded
```

---

## 🧪 Test It

```bash
# 1. Filter to clean agent data
Visit: http://localhost:3000
Select tenant: "acme-corp" or "bigco-inc"

# 2. Generate more agent data
python3 scripts/test_agent.py

# 3. Clean up test pollution (optional)
sqlite3 collector/collector.db \
  "DELETE FROM trace_events 
   WHERE tenant_id IN ('test-all-methods', 'test-tenant') 
   OR tenant_id IS NULL;"
```

---

## 🎯 User Experience Improvements

| Before | After |
|--------|-------|
| Shows `retry:llm_analysis:attempt_1` | Shows `agent:research_assistant` ✅ |
| Run-by-run cost list | Agent-level aggregation ✅ |
| Useless 7-day empty chart | Useful API breakdown ✅ |
| Internal logs pollute UI | Clean agent view ✅ |

---

## 📝 Developer Guidelines

### **When Naming Sections:**

✅ **DO** use semantic prefixes:
```python
with section("agent:chatbot"):
    with section("tool:search_api"):
        with section("step:format_results"):
            ...
```

✅ **DO** use descriptive names:
- `agent:research_assistant`
- `agent:customer_support`
- `tool:web_search`
- `tool:database_query`
- `step:analyze_results`
- `step:format_response`

❌ **DON'T** use these (they're auto-filtered):
- `retry:*` (internal, auto-added)
- `test:*` (test code)
- Function names (`_track_openai_call`)

---

## 🚀 Result

**Your dashboard now shows:**
1. ✅ Clean agent-level sections
2. ✅ API cost breakdown (not useless 7-day chart)
3. ✅ Hierarchical trace on drill-down
4. ✅ Internal logs hidden unless expanded

**Perfect for developers monitoring agent costs!** 🎯

