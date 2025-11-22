# Execution Visualization & Semantic Cost Attribution - Architecture Plan

## Current State

**What we have:**
- SDK tracks `section_path` (hierarchical labels: `agent:researcher/tool:web_search`)
- CLI can scan code and auto-instrument with labels
- Dashboard shows costs by section labels
- HTTP interception captures API calls

**What's missing:**
1. **Semantic understanding** - We don't know what code sections actually DO (summarization vs twitch streaming)
2. **Execution flow visualization** - No way to see the actual call tree/execution path
3. **Code-to-cost mapping** - Can't say "summarization.py is 60% of costs"

---

## Feature 1: Execution Flow Visualization

### Goal
Show exactly how code executes: which functions call which APIs, tool calls, nested calls, etc.

### Architecture

#### A. Runtime Execution Tracing

**For Local Development:**
```python
# SDK automatically tracks:
- Function entry/exit (using decorators or AST instrumentation)
- Call stack depth
- Parent-child relationships
- Tool calls (if using frameworks like LangChain)
- API calls (already tracked)
```

**For Deployed Code:**
- Same runtime tracing, but data sent to collector
- Collector stores execution traces
- Dashboard visualizes traces

**Implementation:**
1. **Function-level tracing** (using `sys.settrace` or decorators):
   ```python
   # Auto-instrument functions
   @trace_function(name="summarize_article")
   def summarize_article(text):
       # All calls inside tracked
       response = openai_call()
   ```

2. **Call stack tracking**:
   ```python
   # Track parent-child relationships
   execution_tree = {
       "id": "span-123",
       "function": "summarize_article",
       "parent": "span-122",  # parent function
       "children": ["span-124", "span-125"],  # child calls
       "api_calls": [...],
       "start_time": "...",
       "end_time": "..."
   }
   ```

3. **Tool call detection** (for frameworks):
   ```python
   # Detect LangChain tool calls
   # Detect OpenAI function calling
   # Detect custom tool wrappers
   ```

#### B. Dashboard Visualization

**Execution Tree View:**
```
Run: abc-123
├─ main()
│  ├─ summarize_article() [2.3s, $0.15]
│  │  ├─ openai.ChatCompletion.create() [1.8s, $0.12]
│  │  └─ process_results() [0.5s, $0.03]
│  ├─ stream_to_twitch() [5.2s, $0.45]
│  │  ├─ openai.ChatCompletion.create() [3.1s, $0.28]
│  │  └─ twitch_api.send() [2.1s, $0.17]
│  └─ bot_response() [1.1s, $0.08]
```

**Timeline View:**
```
Timeline:
[====summarize====][====stream====][==bot==]
    2.3s             5.2s           1.1s
```

---

## Feature 2: Semantic Code Chunking & Cost Attribution

### Goal
Understand which semantic parts of codebase cost the most (e.g., "summarization is 60% of costs")

### Architecture

#### A. CLI Semantic Analysis

**New CLI Command: `llmobserve analyze`**
```bash
llmobserve analyze .
# Scans codebase
# Uses AST + AI to understand semantic sections
# Maps code sections to costs
```

**What it does:**
1. **AST Analysis**:
   - Parse Python files
   - Identify functions, classes, modules
   - Build dependency graph
   - Find LLM API call sites

2. **Semantic Understanding** (using AI):
   ```python
   # Send code chunks to AI with prompt:
   "What does this code section do? 
   Options: summarization, streaming, botting, research, etc."
   
   # AI responds:
   {
     "file": "agents/summarizer.py",
     "function": "summarize_article",
     "semantic_label": "summarization",
     "confidence": 0.95,
     "description": "Summarizes long articles using GPT-4"
   }
   ```

3. **Cost Mapping**:
   ```python
   # Match semantic sections to cost data
   semantic_costs = {
     "summarization": {
       "files": ["agents/summarizer.py"],
       "functions": ["summarize_article", "summarize_batch"],
       "total_cost": 45.20,  # $45.20
       "percentage": 0.60,   # 60% of total
       "api_calls": 1234,
       "avg_cost_per_call": 0.037
     },
     "twitch_streaming": {
       "files": ["streaming/twitch.py"],
       "functions": ["stream_to_twitch"],
       "total_cost": 18.50,
       "percentage": 0.25,
       ...
     }
   }
   ```

#### B. Dashboard Integration

**New View: "Code Analysis"**
```
Semantic Cost Breakdown:

📊 Summarization (60% - $45.20)
   ├─ agents/summarizer.py:summarize_article
   ├─ 1,234 API calls
   └─ Avg: $0.037/call
   
📊 Twitch Streaming (25% - $18.50)
   ├─ streaming/twitch.py:stream_to_twitch
   ├─ 456 API calls
   └─ Avg: $0.041/call
   
📊 Botting (15% - $11.30)
   ├─ bot/response.py:bot_response
   ├─ 789 API calls
   └─ Avg: $0.014/call
```

**Code Heatmap:**
```
File: agents/summarizer.py
├─ Line 15-30: summarize_article() [🔥 HIGH - $30.20]
├─ Line 32-45: summarize_batch() [🔥 MEDIUM - $15.00]
└─ Line 47-60: helper_function() [❄️ LOW - $0.00]
```

---

## Implementation Plan

### Phase 1: Execution Tracing (Runtime)

1. **Add function tracing to SDK**:
   - Use `sys.settrace` or decorators
   - Track function entry/exit
   - Build call tree
   - Send to collector

2. **Collector stores execution traces**:
   - New table: `execution_traces`
   - Links to `trace_events` via `span_id`

3. **Dashboard shows execution tree**:
   - New component: `ExecutionTreeView`
   - Shows call hierarchy
   - Click to see details

### Phase 2: Semantic Analysis (CLI)

1. **Enhance CLI scanner**:
   - Add semantic analysis step
   - Use AI to label code sections
   - Store semantic labels

2. **Map to costs**:
   - Query cost data by file/function
   - Aggregate by semantic label
   - Calculate percentages

3. **Dashboard integration**:
   - New page: `/code-analysis`
   - Show semantic cost breakdown
   - Code heatmap view

### Phase 3: Integration

1. **Link execution traces to semantic labels**:
   - When function runs, check semantic label
   - Group costs by semantic section

2. **Real-time updates**:
   - As code runs, update semantic costs
   - Show live execution in dashboard

---

## Technical Details

### Execution Tracing Implementation

**Option A: Decorator-based (explicit)**
```python
from llmobserve import trace_function

@trace_function(name="summarize_article")
def summarize_article(text):
    # Automatically tracked
    pass
```

**Option B: AST instrumentation (automatic)**
```python
# CLI auto-instruments all functions
# No code changes needed
```

**Option C: sys.settrace (runtime)**
```python
# Intercept all function calls at runtime
# Most comprehensive but slower
```

**Recommendation:** Start with Option A (decorators), add Option B (AST) for auto-instrumentation.

### Semantic Analysis Implementation

**Using AI (Claude/GPT-4):**
```python
def analyze_semantic_section(code: str) -> dict:
    prompt = f"""
    Analyze this code section and identify its semantic purpose:
    
    {code}
    
    Return JSON:
    {{
        "semantic_label": "summarization|streaming|botting|research|...",
        "confidence": 0.0-1.0,
        "description": "..."
    }}
    """
    # Call AI API
    return ai_response
```

**Caching:**
- Cache semantic labels per function
- Only re-analyze if code changes
- Store in `.llmobserve/semantic_labels.json`

---

## User Flow

1. **User runs CLI**:
   ```bash
   llmobserve analyze .
   # Scans codebase
   # Analyzes semantic sections
   # Maps to costs
   ```

2. **CLI outputs**:
   ```
   📊 Semantic Cost Analysis:
   
   Summarization: $45.20 (60%)
   Twitch Streaming: $18.50 (25%)
   Botting: $11.30 (15%)
   
   View in dashboard: http://localhost:3000/code-analysis
   ```

3. **User views dashboard**:
   - See semantic breakdown
   - See execution traces
   - See code heatmap

4. **User optimizes**:
   - Focus on high-cost sections
   - See which functions to optimize
   - Track improvements over time

---

## Questions to Resolve

1. **For deployed code**: How do we trace execution?
   - Option A: SDK sends traces to collector (already works)
   - Option B: Add more detailed tracing
   - Option C: Use distributed tracing (OpenTelemetry)

2. **Performance impact**: Will tracing slow down code?
   - Need to benchmark
   - Maybe make it opt-in for production

3. **Semantic labels**: How do we handle code changes?
   - Re-analyze on file change?
   - User can manually label?
   - Hybrid approach?

4. **Visualization**: What's the best UI?
   - Tree view?
   - Timeline?
   - Code heatmap?
   - All of the above?

---

## Next Steps

1. **Prototype execution tracing** (Phase 1)
2. **Prototype semantic analysis** (Phase 2)
3. **Build dashboard views** (Phase 3)
4. **Test with real codebase**
5. **Iterate based on feedback**

