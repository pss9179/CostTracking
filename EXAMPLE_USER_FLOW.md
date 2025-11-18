# Complete User Flow Example: AI Auto-Instrumentation

## Scenario: Sarah, a SaaS founder building an AI research assistant

---

## Step 1: Sarah signs up and gets her API key

**On llmobserve.com:**
1. Clicks "Get Started - $8/month"
2. Signs up with email
3. Subscribes ($8/month)
4. Goes to Settings → Gets her API key: `llm_abc123xyz...`

---

## Step 2: Sarah installs LLMObserve

```bash
pip install llmobserve

# Sets up credentials (she got these from dashboard)
export LLMOBSERVE_COLLECTOR_URL="https://llmobserve-production.up.railway.app"
export LLMOBSERVE_API_KEY="llm_abc123xyz..."
```

---

## Step 3: Sarah adds basic tracking to her agent

**Her current code** (`research_agent.py`):

```python
import openai

def research_agent(topic):
    """Research agent that finds and synthesizes information."""
    client = openai.OpenAI()
    
    # Generate research questions
    questions = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a research assistant."},
            {"role": "user", "content": f"Generate 3 research questions about {topic}"}
        ]
    )
    
    # Synthesize findings
    synthesis = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Synthesize these findings."},
            {"role": "user", "content": questions.choices[0].message.content}
        ]
    )
    
    return synthesis.choices[0].message.content


def writer_agent(content):
    """Polish content for publication."""
    client = openai.OpenAI()
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional writer."},
            {"role": "user", "content": f"Polish this:\n{content}"}
        ]
    )
    
    return response.choices[0].message.content


# Main workflow
if __name__ == "__main__":
    result = research_agent("quantum computing")
    final = writer_agent(result)
    print(final)
```

**She adds 2 lines at the top:**

```python
import llmobserve

llmobserve.observe(
    collector_url="https://llmobserve-production.up.railway.app",
    api_key="llm_abc123xyz..."
)
```

**Runs her code:**
```bash
python research_agent.py
```

---

## Step 4: Sarah checks her dashboard

**Goes to llmobserve.com/dashboard**

She sees:
```
Total Cost (24h): $0.42

Untracked / Non-Agent Costs (24h)
├─ Untracked Cost: $0.42
├─ Untracked Calls: 3
└─ % of Total: 100%

💡 Tip: Untracked costs occur when API calls are not wrapped with agents/tools.
```

**She thinks:** "Hmm, all my costs are untracked. I want to see which agent costs what!"

She sees two buttons:
- **📚 Learn How to Label Costs**
- **✨ AI Auto-Instrument** ← She clicks this

---

## Step 5: AI Auto-Instrumentation (Magic Moment)

**On the docs page, she reads:**

> ✨ **Included with your subscription!** No extra API keys needed.

**She runs:**

```bash
# Preview what AI suggests
llmobserve preview research_agent.py
```

**Output:**
```
🔍 Analysis of research_agent.py

Found 2 suggestions:

1. Line 3 - decorator
   Label: researcher
   Function: research_agent
   Reason: Main agent function orchestrating multiple LLM calls for research
   Before: def research_agent(topic):
   After:  @agent("researcher")
           def research_agent(topic):

2. Line 27 - decorator
   Label: writer
   Function: writer_agent
   Reason: Agent function that polishes content using LLM
   Before: def writer_agent(content):
   After:  @agent("writer")
           def writer_agent(content):

💡 To apply these changes, run with --auto-apply flag
   A backup (.bak) will be created automatically
```

**She thinks:** "Perfect! Let's do it."

```bash
llmobserve instrument research_agent.py --auto-apply
```

**Output:**
```
✅ Applied 2 changes to research_agent.py
   Backup created: research_agent.py.bak

📊 Suggestions:
  1. decorator at line 3
     → researcher
  2. decorator at line 27
     → writer
```

---

## Step 6: Her code is now instrumented

**Updated code** (automatic):

```python
import llmobserve
from llmobserve import agent  # Added automatically

llmobserve.observe(
    collector_url="https://llmobserve-production.up.railway.app",
    api_key="llm_abc123xyz..."
)

@agent("researcher")  # ← AI added this
def research_agent(topic):
    """Research agent that finds and synthesizes information."""
    client = openai.OpenAI()
    
    # Generate research questions
    questions = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a research assistant."},
            {"role": "user", "content": f"Generate 3 research questions about {topic}"}
        ]
    )
    
    # Synthesize findings
    synthesis = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Synthesize these findings."},
            {"role": "user", "content": questions.choices[0].message.content}
        ]
    )
    
    return synthesis.choices[0].message.content


@agent("writer")  # ← AI added this
def writer_agent(content):
    """Polish content for publication."""
    client = openai.OpenAI()
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional writer."},
            {"role": "user", "content": f"Polish this:\n{content}"}
        ]
    )
    
    return response.choices[0].message.content


# Main workflow
if __name__ == "__main__":
    result = research_agent("quantum computing")
    final = writer_agent(result)
    print(final)
```

---

## Step 7: Sarah runs her agent again

```bash
python research_agent.py
```

*(Same output, but now tracking is labeled)*

---

## Step 8: Dashboard shows organized costs

**Back to llmobserve.com/dashboard**

Now she sees:
```
Total Cost (24h): $0.84

Agent Breakdown:
├─ researcher: $0.28 (2 calls)
├─ writer: $0.14 (1 call)
└─ Untracked: $0.42 (3 calls from earlier run)

By Provider:
├─ OpenAI (gpt-4): $0.84
```

**She can now:**
- See which agent is most expensive (researcher)
- Track costs per run
- Optimize the expensive parts
- Show her investors clear cost breakdown

---

## Total Time: 5 minutes
## Extra setup: Zero (used existing API key)
## Cost: $0 extra (included in $8/month)

---

## What Just Happened:

1. **Zero-config tracking** - 2 lines of code, costs appear automatically
2. **AI labels her agents** - One CLI command, no manual work
3. **Organized dashboard** - Clear breakdown by agent, provider, time
4. **Included in subscription** - No extra API keys, no extra costs

**Sarah's reaction:** "Holy shit, that was easy."

---

## Compare to Competitors:

**Without LLMObserve:**
- Manually track every API call
- Build own pricing database
- Write custom dashboards
- No agent-level breakdown

**With other tools:**
- Complex SDK setup
- Framework-specific integration
- Manual labeling (boring)
- Extra costs for analytics

**With LLMObserve:**
- 2 lines of code
- AI labels everything
- Beautiful dashboard
- $8/month total

---

## The Killer Feature:

**That "✨ AI Auto-Instrument" button on untracked costs.**

Most users won't read docs. They'll:
1. See untracked costs
2. Click the shiny button
3. Run one command
4. Get organized data

**This is the "make it yourself vs order takeout" moment.**

We made it easier to use our tool than to ignore it.

