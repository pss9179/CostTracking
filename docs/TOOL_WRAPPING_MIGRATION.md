# Tool Wrapping Migration Guide

This guide explains how to migrate from manual `section()` labeling to the new auto-wrapping architecture.

## Why Migrate?

### Problems with Manual Labeling

❌ **Setup code not captured**: API calls before `with section()` are missed  
❌ **Nested tools break**: Tools calling other tools lose structure  
❌ **Framework limitations**: Can't modify framework internal code  
❌ **Dynamic calls**: LLM-selected tools can't be pre-labeled  
❌ **3rd party libraries**: Can't add labels to external code

### Benefits of Tool Wrapping

✅ **Automatic nesting**: Tools calling tools maintain hierarchy  
✅ **Framework support**: Works with LangChain, CrewAI, AutoGen, LlamaIndex  
✅ **No manual labor**: Wrap once, track forever  
✅ **Setup code included**: Everything inside wrapped functions is tracked  
✅ **Async safe**: Full support for async/await patterns

## Migration Path

### Step 1: Update SDK

```python
pip install --upgrade llmobserve
```

### Step 2: Enable Tool Wrapping

```python
import llmobserve

llmobserve.observe(
    collector_url="http://localhost:8000",
    enable_tool_wrapping=True,  # Enable the new system
)
```

### Step 3: Migrate Your Code

#### Old Way (Manual `section()`)

```python
from llmobserve import section

def my_agent(query):
    with section("agent:researcher"):
        # Agent logic
        with section("tool:web_search"):
            results = search_web(query)
        
        with section("tool:analyze"):
            analysis = analyze_results(results)
        
        return analysis
```

**Problems:**
- If `search_web()` calls another tool internally, it won't be tracked
- Setup code before `with section()` is missed
- Have to remember to wrap every single function

#### New Way (Auto-Wrapping)

```python
from llmobserve import agent, tool, wrap_all_tools

@agent("researcher")
def my_agent(query):
    # All tools below are automatically wrapped
    results = search_tool(query)
    analysis = analyze_tool(results)
    return analysis

@tool("web_search")
def search_tool(query):
    # Even if this calls another tool, it's tracked
    return search_web(query)

@tool("analyze")
def analyze_tool(results):
    return analyze_results(results)
```

**Benefits:**
- Nested tool calls automatically tracked
- Setup code included
- Cleaner, more maintainable code

### Step 4: Wrap Framework Tools

If you use LangChain, CrewAI, AutoGen, or LlamaIndex:

```python
from llmobserve import wrap_all_tools

# LangChain
from langchain.tools import DuckDuckGoSearchRun

search = DuckDuckGoSearchRun()
tools = wrap_all_tools([search, calculator, scraper])
agent = initialize_agent(tools=tools, llm=llm)

# CrewAI
tools = wrap_all_tools([search_tool, scrape_tool])
agent = Agent(role="researcher", tools=tools)

# AutoGen
function_map = wrap_all_tools({"search": search_fn, "calc": calc_fn})
assistant = AssistantAgent(function_map=function_map)

# LlamaIndex
tools = wrap_all_tools([search_tool, qa_tool])
agent = OpenAIAgent.from_tools(tools)
```

### Step 5: Wrap LLM Clients (Optional)

For tool-calling workflows with OpenAI/Anthropic:

```python
from llmobserve import wrap_openai_client, wrap_anthropic_client
import openai

# Wrap your OpenAI client
client = openai.OpenAI(api_key="...")
client = wrap_openai_client(client)

# Now tool_calls will be extracted from responses
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Search for AI"}],
    tools=[{"type": "function", "function": {"name": "web_search"}}]
)
```

## Backward Compatibility

✅ **Old code still works**: Manual `section()` calls are still supported  
✅ **Mix old and new**: You can use both approaches simultaneously  
✅ **No breaking changes**: Existing instrumentation continues to work

## Migration Checklist

- [ ] Update SDK to latest version
- [ ] Enable `enable_tool_wrapping=True` in `observe()`
- [ ] Add `@agent()` decorator to agent entrypoints
- [ ] Add `@tool()` decorator to custom tools
- [ ] Wrap framework tools with `wrap_all_tools()` before passing to frameworks
- [ ] (Optional) Wrap LLM clients with `wrap_openai_client()` / `wrap_anthropic_client()`
- [ ] Remove manual `section()` calls (or keep for backward compat)
- [ ] Test in development
- [ ] Deploy to production

## Common Issues

### Issue: "Untracked Costs" showing in dashboard

**Cause**: Some API calls are not wrapped with agents/tools.

**Solution**: 
1. Ensure all agent entrypoints have `@agent()` decorator
2. Wrap all tools with `wrap_all_tools()` or `@tool()`
3. Check the "Untracked Costs" card on dashboard for details

### Issue: Nested tools not showing in tree

**Cause**: Inner tools are not wrapped.

**Solution**: Wrap ALL tools at registration, not just top-level ones:

```python
# Bad: Only outer tool wrapped
@tool("outer")
def outer_tool():
    inner_tool()  # ❌ Not tracked

# Good: All tools wrapped
@tool("outer")
def outer_tool():
    inner_tool_wrapped()  # ✓ Tracked

@tool("inner")
def inner_tool_wrapped():
    pass
```

### Issue: Framework tools not tracked

**Cause**: Forgot to call `wrap_all_tools()`.

**Solution**:
```python
# Before passing to framework
tools = wrap_all_tools([search, calc, scraper])
agent = initialize_agent(tools=tools, llm=llm)
```

## Need Help?

- See `docs/TOOL_WRAPPING_GUIDE.md` for detailed examples
- See `docs/ARCHITECTURE_TOOL_WRAPPING.md` for how it works
- Run tests: `python scripts/test_tool_wrapping.py`

