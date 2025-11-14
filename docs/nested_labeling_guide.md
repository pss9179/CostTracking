# Nested Labeling Problem & Solutions

## ❌ The Problem

When you have **nested tools/agents** with **setup code** before entering a section, that code isn't properly tracked.

### Example Problem Scenario

```python
def tool_B():
    # ❌ PROBLEM: Setup code runs OUTSIDE any section
    config = fetch_config()  # If this makes an API call, it's NOT tracked as tool:B
    validate_input()         # Also not tracked
    
    # Only NOW do we enter the section
    with section("tool:B"):
        response = client.chat.completions.create(...)  # ✅ This IS tracked
    
    # ❌ More code after section - also not tracked
    cleanup()

def tool_A():
    with section("tool:A"):
        tool_B()  # Calls tool_B
```

**What happens:**
- Setup code in `tool_B()` runs while still inside `tool:A` section
- Any API calls in setup are attributed to `tool:A`, not `tool:B`
- Code after the section isn't tracked at all

## ✅ Solutions

### Solution 1: Wrap Entire Function (Simplest)

**Best for:** Simple tools with minimal setup

```python
def tool_B():
    with section("tool:B"):
        # ✅ All code is now inside tool:B section
        config = fetch_config()  # Tracked as tool:B
        validate_input()        # Tracked as tool:B
        response = client.chat.completions.create(...)  # Tracked as tool:B
        cleanup()                # Tracked as tool:B
```

**Pros:**
- Simple, no extra code
- Everything is tracked

**Cons:**
- Less granular (can't distinguish setup vs main work)

---

### Solution 2: Use `step:` Sections (Most Granular)

**Best for:** Complex tools with multiple phases

```python
def tool_B():
    with section("tool:B"):
        # Setup phase
        with section("step:setup"):
            config = fetch_config()  # Tracked as tool:B/step:setup
            validate_input()        # Tracked as tool:B/step:setup
        
        # Main work
        response = client.chat.completions.create(...)  # Tracked as tool:B
        
        # Cleanup phase
        with section("step:cleanup"):
            cleanup()  # Tracked as tool:B/step:cleanup
```

**Pros:**
- Very granular tracking
- Can see breakdown of setup/main/cleanup costs
- Clear hierarchy in UI

**Cons:**
- More verbose
- More sections to manage

---

### Solution 3: Use `@trace` Decorator (Most Convenient)

**Best for:** Many tools, want automatic wrapping

```python
from llmobserve import trace

@trace(tool="B")
def tool_B():
    # ✅ Entire function automatically wrapped in tool:B section
    config = fetch_config()  # Tracked as tool:B
    validate_input()         # Tracked as tool:B
    response = client.chat.completions.create(...)  # Tracked as tool:B
    cleanup()                # Tracked as tool:B
```

**Pros:**
- Zero boilerplate
- Automatic wrapping
- Works with async functions
- Clean code

**Cons:**
- Less control (can't exclude parts)
- Can't use `step:` inside easily

---

### Solution 4: Hybrid (Decorator + Steps)

**Best for:** Complex tools that need granularity

```python
@trace(tool="B")
def tool_B():
    with section("step:setup"):
        config = fetch_config()  # Tracked as tool:B/step:setup
        validate_input()         # Tracked as tool:B/step:setup
    
    response = client.chat.completions.create(...)  # Tracked as tool:B
    
    with section("step:cleanup"):
        cleanup()  # Tracked as tool:B/step:cleanup
```

**Pros:**
- Automatic function wrapping
- Granular step tracking
- Best of both worlds

**Cons:**
- Slightly more complex

---

## 📊 Real-World Example

### Before (Broken)

```python
def web_search_tool(query: str):
    # ❌ Setup code outside section
    api_key = os.getenv("SEARCH_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # ❌ API call to validate query (not tracked as web_search_tool!)
    validation = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Validate: {query}"}]
    )
    
    # Only NOW enter section
    with section("tool:web_search"):
        # ✅ Main API call (tracked)
        response = requests.get("https://api.search.com", headers=headers, params={"q": query})
    
    # ❌ Post-processing (not tracked)
    results = parse_results(response.json())
    return results
```

**Problem:** Validation API call is tracked as whatever section was active before (maybe `agent:researcher`), not `tool:web_search`.

### After (Fixed with Solution 1)

```python
def web_search_tool(query: str):
    with section("tool:web_search"):
        # ✅ All code inside section
        api_key = os.getenv("SEARCH_API_KEY")
        headers = {"Authorization": f"Bearer {api_key}"}
        
        # ✅ Validation API call (tracked as tool:web_search)
        validation = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Validate: {query}"}]
        )
        
        # ✅ Main API call (tracked as tool:web_search)
        response = requests.get("https://api.search.com", headers=headers, params={"q": query})
        
        # ✅ Post-processing (tracked as tool:web_search)
        results = parse_results(response.json())
        return results
```

### After (Fixed with Solution 3 - Decorator)

```python
from llmobserve import trace

@trace(tool="web_search")
def web_search_tool(query: str):
    # ✅ Entire function automatically wrapped
    api_key = os.getenv("SEARCH_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # ✅ Validation API call (tracked as tool:web_search)
    validation = client.chat.completions.create(...)
    
    # ✅ Main API call (tracked as tool:web_search)
    response = requests.get("https://api.search.com", ...)
    
    # ✅ Post-processing (tracked as tool:web_search)
    results = parse_results(response.json())
    return results
```

---

## 🎯 Recommendations

| Scenario | Solution | Why |
|----------|----------|-----|
| Simple tool (1-2 API calls) | **Solution 1** (wrap function) | Simple, clear |
| Complex tool (multiple phases) | **Solution 2** (use `step:`) | Granular tracking |
| Many tools (10+) | **Solution 3** (`@trace` decorator) | Less boilerplate |
| Complex + Many tools | **Solution 4** (decorator + steps) | Best of both |

---

## ⚠️ Key Takeaway

**Always wrap the ENTIRE function** in a section, not just the API call part.

**Bad:**
```python
def tool():
    setup()  # ❌ Not tracked
    with section("tool:name"):
        api_call()  # ✅ Tracked
    cleanup()  # ❌ Not tracked
```

**Good:**
```python
def tool():
    with section("tool:name"):
        setup()     # ✅ Tracked
        api_call()  # ✅ Tracked
        cleanup()   # ✅ Tracked
```

Or use `@trace` decorator for automatic wrapping:
```python
@trace(tool="name")
def tool():
    setup()     # ✅ Automatically tracked
    api_call()  # ✅ Automatically tracked
    cleanup()   # ✅ Automatically tracked
```

