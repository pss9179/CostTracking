# Automatic Agent Detection 🎯

## No More Manual Tagging!

**Agents are now automatically detected from your code** - no need to manually wrap with `section()`!

## How It Works

The library analyzes your call stack to automatically detect:
- **Agents**: Functions/classes named like `*agent*`, `*orchestrat*`, `*workflow*`
- **Tools**: Functions/classes named like `*tool*`, `*function*`, `*call*`
- **Steps**: Functions named like `*step*`, `*stage*`, `*task*`

## Examples

### Before (Manual Tagging) ❌

```python
from llmobserve import observe, section

observe(collector_url="http://localhost:8000")

# Had to manually tag everything
with section("agent:research_assistant"):
    with section("tool:web_search"):
        response = client.chat.completions.create(...)
```

### After (Automatic) ✅

```python
from llmobserve import observe

observe(collector_url="http://localhost:8000")

# Just write your code - agents detected automatically!
def research_assistant(query: str):
    """This function is automatically detected as an agent!"""
    response = client.chat.completions.create(...)
    return response

def web_search_tool(query: str):
    """This function is automatically detected as a tool!"""
    response = requests.get(f"https://api.example.com/search?q={query}")
    return response

# Call them - automatically tagged!
research_assistant("What is AI?")
web_search_tool("AI research")
```

## Detection Patterns

### Function Names

```python
# These are automatically detected as agents:
def research_agent(query): ...
def run_agent(): ...
def execute_agent(): ...
def orchestrator(): ...

# These are detected as tools:
def web_search_tool(query): ...
def call_function(): ...
def invoke_tool(): ...

# These are detected as steps:
def analyze_step(data): ...
def process_stage(): ...
def execute_task(): ...
```

### Class Names

```python
# These classes are automatically detected:
class ResearchAgent: ...
class WorkflowOrchestrator: ...
class PipelineExecutor: ...

# Usage:
agent = ResearchAgent()
agent.run()  # Automatically tagged as "agent:research"
```

### Framework Detection

Automatically detects known frameworks:
- **LangChain**: `Agent`, `AgentExecutor`, `ReActAgent`
- **LlamaIndex**: `AgentRunner`, `OpenAIAgent`
- **AutoGPT**: `Agent` classes
- **CrewAI**: `Agent`, `Crew`

## Hierarchical Detection

The library can detect full hierarchies automatically:

```python
def research_agent(query):
    """Outermost agent"""
    web_search_tool(query)  # Tool inside agent
    analyze_step(data)      # Step inside agent

# Automatically detected as:
# "agent:research_agent/tool:web_search_tool/step:analyze_step"
```

## Configuration

Auto-detection is **enabled by default**, but you can disable it:

```python
from llmobserve import observe

# Disable auto-detection (use manual tagging)
observe(
    collector_url="http://localhost:8000",
    auto_detect_agents=False
)

# Or enable explicitly (default)
observe(
    collector_url="http://localhost:8000",
    auto_detect_agents=True  # Default
)
```

## Manual Tagging Still Works

You can still use manual tagging if you want more control:

```python
from llmobserve import observe, section

observe(collector_url="http://localhost:8000")

# Manual tags take priority over auto-detection
with section("agent:custom_name"):
    # This will use "agent:custom_name" instead of auto-detected name
    response = client.chat.completions.create(...)
```

## Priority Order

1. **Manual sections** (if you use `section()`)
2. **Auto-detected agents** (if no manual sections)
3. **"default"** (if nothing detected)

## Benefits

✅ **Zero boilerplate** - Just write your code
✅ **Works with any framework** - LangChain, LlamaIndex, custom agents
✅ **Backward compatible** - Manual tagging still works
✅ **Automatic hierarchy** - Detects nested agents/tools/steps
✅ **Framework-aware** - Recognizes LangChain, AutoGPT, etc.

## Examples

### Custom Agent

```python
from llmobserve import observe
from openai import OpenAI

observe(collector_url="http://localhost:8000")
client = OpenAI()

def my_research_agent(query: str):
    """Automatically detected as agent:my_research"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": query}]
    )
    return response

# Call it - automatically tracked as "agent:my_research"!
my_research_agent("What is AI?")
```

### LangChain Agent

```python
from llmobserve import observe
from langchain.agents import AgentExecutor

observe(collector_url="http://localhost:8000")

# LangChain agents are automatically detected!
agent = AgentExecutor(...)
agent.run("What is AI?")  # Automatically tagged as "agent:langchain"
```

### Nested Agents

```python
def coordinator_agent():
    """Outer agent"""
    planner_agent()  # Nested agent
    executor_agent()  # Nested agent

def planner_agent():
    """Nested agent"""
    response = client.chat.completions.create(...)

def executor_agent():
    """Nested agent"""
    response = client.chat.completions.create(...)

# Automatically detected as:
# "agent:coordinator_agent/agent:planner_agent"
# "agent:coordinator_agent/agent:executor_agent"
```

## Summary

**No more manual tagging!** Just write your code and agents are automatically detected. The library analyzes your call stack to find agent patterns, so you don't need to wrap everything in `section()` calls.

Works with:
- ✅ Custom agents
- ✅ LangChain
- ✅ LlamaIndex
- ✅ AutoGPT
- ✅ CrewAI
- ✅ Any framework!

