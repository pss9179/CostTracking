# Agent Tree Visualization: How It Works

## Yes - Tree is Built DURING Execution

**The tree/hierarchy is built in real-time as your code runs**, not before.

## How It Works: Agent Loops & Multiple Tool Calls

### Example: Agent with Loop and Multiple Tools

```python
from llmobserve import observe
from openai import OpenAI

observe(collector_url="http://localhost:8000")
client = OpenAI()

def research_agent(query: str, max_iterations: int = 3):
    """Agent that loops and calls multiple tools"""
    
    for i in range(max_iterations):
        # Tool call 1: Search
        search_results = web_search_tool(query)
        
        # Tool call 2: Analyze
        analysis = analyze_tool(search_results)
        
        # Tool call 3: LLM call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": analysis}]
        )
        
        if response.choices[0].message.content == "DONE":
            break
    
    return response

def web_search_tool(query: str):
    """Tool that makes API call"""
    # When this API call happens, call stack is:
    # [research_agent() -> web_search_tool() -> requests.get()]
    # Detected: "agent:research/tool:web_search"
    response = requests.get(f"https://api.example.com/search?q={query}")
    return response

def analyze_tool(data: str):
    """Another tool"""
    # When this API call happens, call stack is:
    # [research_agent() -> analyze_tool() -> client.chat.completions.create()]
    # Detected: "agent:research/tool:analyze"
    response = client.chat.completions.create(...)
    return response

# Run it
research_agent("What is AI?")
```

## What Happens During Execution

### Iteration 1:

```
1. research_agent() called
   ↓
2. web_search_tool() called
   ↓
3. requests.get() → API call happens
   📊 Event captured:
      section: "agent:research"
      section_path: "agent:research/tool:web_search"
      (from call stack analysis)
   ↓
4. analyze_tool() called
   ↓
5. client.chat.completions.create() → API call happens
   📊 Event captured:
      section: "agent:research"
      section_path: "agent:research/tool:analyze"
   ↓
6. client.chat.completions.create() → API call happens (in research_agent)
   📊 Event captured:
      section: "agent:research"
      section_path: "agent:research"
```

### Iteration 2:

```
1. Loop continues...
   ↓
2. web_search_tool() called again
   ↓
3. requests.get() → API call happens
   📊 Event captured:
      section: "agent:research"
      section_path: "agent:research/tool:web_search"
      (same pattern, but different event)
```

## Tree Visualization: Built from Events

The tree is built from **events emitted during execution**:

```json
// Event 1 (from iteration 1, tool call 1)
{
  "section": "agent:research",
  "section_path": "agent:research/tool:web_search",
  "cost_usd": 0.0001,
  "timestamp": "2024-01-01T10:00:00"
}

// Event 2 (from iteration 1, tool call 2)
{
  "section": "agent:research",
  "section_path": "agent:research/tool:analyze",
  "cost_usd": 0.0002,
  "timestamp": "2024-01-01T10:00:01"
}

// Event 3 (from iteration 1, LLM call)
{
  "section": "agent:research",
  "section_path": "agent:research",
  "cost_usd": 0.0003,
  "timestamp": "2024-01-01T10:00:02"
}

// Event 4 (from iteration 2, tool call 1)
{
  "section": "agent:research",
  "section_path": "agent:research/tool:web_search",
  "cost_usd": 0.0001,
  "timestamp": "2024-01-01T10:00:03"
}
```

### Tree Visualization (Built from Events)

```
agent:research ($0.0007 total)
├── tool:web_search ($0.0002 total - 2 calls)
│   ├── Call 1 ($0.0001)
│   └── Call 2 ($0.0001)
├── tool:analyze ($0.0002 - 1 call)
└── Direct LLM calls ($0.0003 - 1 call)
```

## How Call Stack Analysis Works

### For Each API Call:

1. **API call happens** (e.g., `client.chat.completions.create()`)
2. **HTTP interceptor captures call stack**:
   ```python
   Call Stack:
     0: research_agent()           ← Detected as "agent:research"
     1: web_search_tool()          ← Detected as "tool:web_search"
     2: client.chat.completions.create()
     3: httpx.Client.send()        ← Interceptor here
     4: agent_detector.detect_hierarchical_context()
   ```
3. **Analyzer walks up the stack**:
   - Finds `research_agent` → adds "agent:research"
   - Finds `web_search_tool` → adds "tool:web_search"
   - Result: `["agent:research", "tool:web_search"]`
4. **Event emitted** with `section_path: "agent:research/tool:web_search"`

## Handling Complex Scenarios

### Nested Agents

```python
def coordinator_agent():
    planner_agent()  # Nested agent
    executor_agent()  # Nested agent

def planner_agent():
    client.chat.completions.create(...)
    # Call stack: [coordinator_agent() -> planner_agent() -> API call]
    # Detected: "agent:coordinator/agent:planner"
```

### Agent Loops

```python
def agent_with_loop():
    for i in range(5):
        tool_call()
        # Each iteration creates separate events
        # All tagged with same section_path, but different timestamps
```

### Multiple Tool Calls

```python
def agent():
    tool1()  # Event: "agent:agent/tool:tool1"
    tool2()  # Event: "agent:agent/tool:tool2"
    tool3()  # Event: "agent:agent/tool:tool3"
    # All captured separately, tree shows all three
```

## Tree Building Process

### Step 1: Code Runs
```python
research_agent("What is AI?")
```

### Step 2: Events Emitted (During Execution)
- Each API call emits an event with `section_path`
- Events are sent to collector in real-time

### Step 3: Tree Visualization (After Execution)
- Dashboard reads events from database
- Groups by `section_path`
- Builds tree visualization:
  ```
  agent:research
    ├── tool:web_search (2 calls, $0.0002)
    ├── tool:analyze (1 call, $0.0001)
    └── direct (1 call, $0.0003)
  ```

## Key Points

✅ **Tree is built DURING execution** - not before
✅ **Each API call captures its call stack** - shows hierarchy
✅ **Agent loops create multiple events** - all tagged with same path
✅ **Multiple tool calls create separate events** - tree shows all
✅ **Nested agents detected from call stack** - shows full hierarchy

## Timeline

```
Time 0: You write code
Time 1: You run code
Time 2: API calls happen → Events emitted (tree built here)
Time 3: Events stored in database
Time 4: Dashboard visualizes tree from events
```

**The tree is built from events captured during execution, not from analyzing source code!**

