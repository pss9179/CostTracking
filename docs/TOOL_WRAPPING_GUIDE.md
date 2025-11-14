# Tool Wrapping Guide

Complete guide to using the tool wrapping system for agent cost tracking.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Agent Decorator](#agent-decorator)
3. [Tool Decorator](#tool-decorator)
4. [Framework Integration](#framework-integration)
5. [LLM Wrappers](#llm-wrappers)
6. [Advanced Patterns](#advanced-patterns)
7. [Troubleshooting](#troubleshooting)

## Quick Start

```python
import llmobserve
from llmobserve import agent, tool, wrap_all_tools

# Initialize SDK
llmobserve.observe(
    collector_url="http://localhost:8000",
    enable_tool_wrapping=True
)

# Mark your agent
@agent("researcher")
def my_agent(query):
    result = search_tool(query)
    return result

# Mark your tools
@tool("web_search")
def search_tool(query):
    return search_api(query)

# Run your agent
my_agent("AI agents")
```

## Agent Decorator

The `@agent()` decorator marks a function as an agent entrypoint, creating a root span.

### Basic Usage

```python
from llmobserve import agent

@agent("planner")
def planning_agent(task):
    # All code here is tracked under "agent:planner"
    plan = create_plan(task)
    results = execute_plan(plan)
    return results
```

### Async Support

```python
@agent("async_researcher")
async def async_research_agent(query):
    results = await async_search(query)
    analysis = await async_analyze(results)
    return analysis
```

### Error Handling

Exceptions are captured but re-raised (doesn't break your code):

```python
@agent("robust_agent")
def robust_agent(query):
    try:
        return risky_operation(query)
    except Exception as e:
        # Exception is logged to llmobserve and re-raised
        return fallback_operation(query)
```

## Tool Decorator

The `@tool()` decorator marks a function as a tool, creating a tool span.

### Basic Usage

```python
from llmobserve import tool

@tool("web_search")
def search_web(query):
    # This function's execution is tracked as "tool:web_search"
    return call_search_api(query)

@tool("calculator")
def calculate(expression):
    return eval(expression)
```

### Nested Tools

Tools can call other tools - nesting is automatic:

```python
@tool("research")
def research_tool(topic):
    # Span: tool:research
    
    search_results = search_tool(topic)  # Span: tool:research/tool:search
    filtered = filter_tool(search_results)  # Span: tool:research/tool:filter
    
    return filtered

@tool("search")
def search_tool(query):
    return search_api(query)

@tool("filter")
def filter_tool(data):
    return [item for item in data if item.relevance > 0.5]
```

### Async Tools

```python
@tool("async_scraper")
async def scrape_async(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
```

## Framework Integration

Use `wrap_all_tools()` to wrap tools before passing them to frameworks.

### LangChain

```python
from llmobserve import agent, wrap_all_tools
from langchain.agents import initialize_agent
from langchain.tools import DuckDuckGoSearchRun, Tool

# Create tools
search = DuckDuckGoSearchRun()
calculator = Tool(name="Calculator", func=lambda x: eval(x))

# Wrap before passing to LangChain
tools = wrap_all_tools([search, calculator])

# Create agent
@agent("langchain_agent")
def create_agent():
    return initialize_agent(tools=tools, llm=llm, agent="zero-shot-react-description")

agent = create_agent()
agent.run("Search for AI and calculate 2+2")
```

### CrewAI

```python
from llmobserve import agent, wrap_all_tools
from crewai import Agent, Task, Crew

# Define tools
def search(query):
    return search_api(query)

def scrape(url):
    return scrape_url(url)

# Wrap tools
tools = wrap_all_tools([search, scrape])

# Create CrewAI agent
@agent("crew_researcher")
def create_crew():
    researcher = Agent(
        role="Researcher",
        goal="Research topics",
        tools=tools
    )
    
    task = Task(description="Research AI", agent=researcher)
    crew = Crew(agents=[researcher], tasks=[task])
    return crew.kickoff()

result = create_crew()
```

### AutoGen

```python
from llmobserve import agent, wrap_all_tools
from autogen import AssistantAgent

# Define tool functions
def search(query):
    return f"Search results for {query}"

def calculate(expr):
    return eval(expr)

# Wrap as dict for AutoGen
function_map = wrap_all_tools({
    "search": search,
    "calculate": calculate
})

# Create AutoGen agent
@agent("autogen_assistant")
def create_assistant():
    return AssistantAgent(
        name="assistant",
        function_map=function_map
    )

assistant = create_assistant()
```

### LlamaIndex

```python
from llmobserve import agent, wrap_all_tools
from llama_index.agent import OpenAIAgent
from llama_index.tools import FunctionTool

# Create tools
search_tool = FunctionTool.from_defaults(fn=search, name="search")
qa_tool = FunctionTool.from_defaults(fn=qa, name="qa")

# Wrap tools
tools = wrap_all_tools([search_tool, qa_tool])

# Create LlamaIndex agent
@agent("llama_agent")
def create_llama_agent():
    return OpenAIAgent.from_tools(tools)

agent = create_llama_agent()
agent.chat("Research AI")
```

## LLM Wrappers

For tool-calling workflows, wrap your LLM clients to extract tool_calls metadata.

### OpenAI

```python
from llmobserve import wrap_openai_client, agent, tool
import openai

# Wrap your client
client = openai.OpenAI(api_key="...")
client = wrap_openai_client(client)

@agent("openai_agent")
def openai_agent(query):
    # Define tools
    tools_spec = [
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    }
                }
            }
        }
    ]
    
    # Call OpenAI with tools
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": query}],
        tools=tools_spec
    )
    
    # tool_calls are extracted and logged
    if response.choices[0].message.tool_calls:
        for tool_call in response.choices[0].message.tool_calls:
            # Call the actual tool
            if tool_call.function.name == "web_search":
                result = web_search_tool(tool_call.function.arguments)
    
    return response

@tool("web_search")
def web_search_tool(args):
    return search_api(args)
```

### Anthropic

```python
from llmobserve import wrap_anthropic_client, agent, tool
import anthropic

# Wrap your client
client = anthropic.Anthropic(api_key="...")
client = wrap_anthropic_client(client)

@agent("anthropic_agent")
def anthropic_agent(query):
    tools_spec = [
        {
            "name": "web_search",
            "description": "Search the web",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                }
            }
        }
    ]
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": query}],
        tools=tools_spec
    )
    
    # tool_use blocks are extracted and logged
    for block in response.content:
        if block.type == "tool_use":
            if block.name == "web_search":
                result = web_search_tool(block.input)
    
    return response

@tool("web_search")
def web_search_tool(args):
    return search_api(args)
```

## Advanced Patterns

### Dynamic Tool Selection

LLM chooses which tool to call:

```python
@agent("dynamic_agent")
def dynamic_agent(query):
    # Tools
    tools_map = {
        "search": search_tool,
        "calculate": calc_tool,
        "summarize": summarize_tool
    }
    
    # Wrap all tools
    from llmobserve import wrap_all_tools
    wrapped_tools = wrap_all_tools(tools_map)
    
    # LLM decides which tool
    tool_name = llm_choose_tool(query)
    result = wrapped_tools[tool_name](query)
    
    return result
```

### Background Workers

Maintain trace continuity across processes:

```python
from llmobserve import agent, tool, export_distributed_context, import_distributed_context
from celery import Celery

app = Celery('tasks')

@agent("main_agent")
def main_agent(query):
    # Export context
    ctx = export_distributed_context()
    
    # Enqueue background task
    process_task.apply_async(args=[ctx, query])
    
    return "Task enqueued"

@app.task
def process_task(ctx, query):
    # Import context (maintains trace_id)
    import_distributed_context(ctx)
    
    # This tool is part of the same trace
    @tool("background_processor")
    def process():
        return heavy_processing(query)
    
    return process()
```

### Multi-Agent Systems

Multiple agents in one workflow:

```python
@agent("coordinator")
def coordinator(task):
    # Coordinator agent
    subtasks = break_down_task(task)
    results = []
    
    for subtask in subtasks:
        # Each specialist is a separate agent
        if "research" in subtask:
            results.append(researcher_agent(subtask))
        elif "code" in subtask:
            results.append(coder_agent(subtask))
    
    return combine_results(results)

@agent("researcher")
def researcher_agent(subtask):
    return research(subtask)

@agent("coder")
def coder_agent(subtask):
    return write_code(subtask)
```

## Troubleshooting

### Untracked Costs

**Problem**: Dashboard shows "Untracked Costs"

**Solution**: 
1. Add `@agent()` to all agent entrypoints
2. Wrap all tools with `wrap_all_tools()` or `@tool()`
3. Check that framework tools are wrapped before passing to framework

### Nested Tools Not Showing

**Problem**: Inner tool calls don't appear in tree

**Solution**: Ensure ALL tools are wrapped, not just top-level ones:

```python
# Wrap all tools upfront
@tool("outer")
def outer():
    pass

@tool("inner")
def inner():
    pass

@agent("agent")
def agent():
    outer()  # Both outer and inner will be tracked
```

### Double Wrapping

**Problem**: Worried about wrapping the same tool twice

**Solution**: Don't worry! Wrapping is idempotent (safe to wrap multiple times):

```python
from llmobserve import wrap_tool

def my_tool():
    pass

wrapped1 = wrap_tool(my_tool)
wrapped2 = wrap_tool(wrapped1)  # Returns same object, no double wrapping

assert wrapped1 is wrapped2  # True
```

### Async Issues

**Problem**: Async agents/tools not working

**Solution**: Ensure you're using `async def` and `await`:

```python
@agent("async_agent")
async def async_agent():  # ← Must be async def
    result = await async_tool()  # ← Must await
    return result

@tool("async_tool")
async def async_tool():  # ← Must be async def
    await asyncio.sleep(1)
    return "result"

# Run with asyncio.run()
asyncio.run(async_agent())
```

## Best Practices

1. **Wrap at the edges**: Add `@agent()` at the very top of your agent logic
2. **Wrap all tools**: Don't forget nested or helper tools
3. **Use descriptive names**: `@agent("customer_support")` not `@agent("agent1")`
4. **Wrap frameworks tools**: Always call `wrap_all_tools()` before passing to frameworks
5. **Test locally**: Use the test scripts in `scripts/` to verify your setup
6. **Check the dashboard**: Monitor "Untracked Costs" to find gaps

## Examples

See full examples in:
- `scripts/test_tool_wrapping.py` - Basic wrapping tests
- `scripts/test_framework_integration.py` - Framework examples
- `scripts/test_e2e_tool_wrapping.py` - Complete workflows

