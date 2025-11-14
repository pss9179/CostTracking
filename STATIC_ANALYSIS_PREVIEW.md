# Static Analysis: Preview Agent Tree BEFORE Execution 🎯

## Problem Solved

**Preview your agent tree BEFORE running code** - see what will happen without wasting API costs!

## Features

✅ **Analyze code without running it** - No API costs, no execution
✅ **Preview agent structure** - See agents/tools/steps hierarchy
✅ **Detect API calls** - See what APIs will be called
✅ **Understand flow** - See function call relationships
✅ **Cost estimation** - Know what will cost before running

## Usage

### Command Line

```bash
# Preview agent tree from Python file
python -m llmobserve.static_analyzer my_agent.py

# Or use the script
python scripts/preview_agent_tree.py my_agent.py
```

### Python API

```python
from llmobserve import preview_agent_tree, analyze_code_file

# Preview from file
preview = preview_agent_tree(file_path="my_agent.py")
print(preview)

# Or analyze code string
code = """
def research_agent(query):
    web_search_tool(query)
    analyze_tool(results)
"""
preview = preview_agent_tree(code=code)
print(preview)

# Get structured data
result = analyze_code_file("my_agent.py")
print(result["agents"])
```

## Example Output

```
📊 Agent Tree Preview (my_agent.py)
============================================================
Total Agents: 1
Total Functions: 3

🤖 agent:research (line 5)
  └─ API: openai_chat (line 12)
  └─ Calls: web_search_tool()
  └─ Calls: analyze_tool()
  🔧 tool:web_search (line 15)
    └─ API: http_request (line 18)
  🔧 tool:analyze (line 22)
    └─ API: openai_chat (line 25)
```

## What It Detects

### Agents
- Functions with `*agent*`, `*orchestrat*`, `*workflow*` in name
- Classes with `Agent`, `Workflow`, `Pipeline` in name

### Tools
- Functions with `*tool*`, `*function*`, `*call*` in name
- Classes with `Tool`, `Function` in name

### Steps
- Functions with `*step*`, `*stage*`, `*task*` in name

### API Calls
- OpenAI: `client.chat.completions.create()`, `client.embeddings.create()`
- Anthropic: `client.messages.create()`
- HTTP: `requests.get()`, `requests.post()`, `httpx.get()`, `httpx.post()`

## Example Code

```python
# my_agent.py
from openai import OpenAI

client = OpenAI()

def research_agent(query: str):
    """Main research agent"""
    # Tool call
    results = web_search_tool(query)
    
    # Analysis
    analysis = analyze_tool(results)
    
    # LLM call
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": analysis}]
    )
    return response

def web_search_tool(query: str):
    """Web search tool"""
    import requests
    response = requests.get(f"https://api.example.com/search?q={query}")
    return response

def analyze_tool(data: str):
    """Analysis tool"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Analyze: {data}"}]
    )
    return response
```

### Preview Output

```
📊 Agent Tree Preview (my_agent.py)
============================================================
Total Agents: 1
Total Functions: 3

🤖 agent:research (line 5)
  └─ API: openai_chat (line 12)
  └─ Calls: web_search_tool()
  └─ Calls: analyze_tool()
  🔧 tool:web_search (line 15)
    └─ API: http_request (line 18)
  🔧 tool:analyze (line 22)
    └─ API: openai_chat (line 25)
```

## Benefits

### 1. **No API Costs**
Preview structure without running code - save money!

### 2. **Understand Flow**
See what agents/tools will be called before execution

### 3. **Debug Structure**
Find issues in agent structure before running

### 4. **Documentation**
Auto-generate agent tree documentation

### 5. **Cost Estimation**
See what APIs will be called (estimate costs)

## Use Cases

### Before Running Expensive Agents
```bash
# Preview first - see what will happen
python scripts/preview_agent_tree.py expensive_agent.py

# Then decide if you want to run it
python expensive_agent.py
```

### Code Review
```bash
# Review agent structure before merging
python scripts/preview_agent_tree.py new_feature.py
```

### Documentation
```bash
# Generate agent tree docs
python scripts/preview_agent_tree.py agent.py > agent_tree.txt
```

## Limitations

⚠️ **Static analysis limitations:**
- Can't detect dynamic calls (e.g., `getattr(obj, method_name)()`)
- Can't detect calls made via reflection
- Can't see runtime values (only structure)
- Can't detect calls in imported modules (only current file)

But it's still super useful for understanding structure before execution!

## Summary

**Preview agent tree BEFORE running code:**
- ✅ No API costs
- ✅ See structure
- ✅ Understand flow
- ✅ Debug issues
- ✅ Estimate costs

**Perfect for:**
- Testing agent structure
- Code review
- Documentation
- Cost estimation
- Debugging

