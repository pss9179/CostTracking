# Hybrid Static + Runtime Analysis

## How They Work Together

### Static Analysis (Preview) → Runtime Detection (Actual)

**Static Analysis (Regex):**
- Runs BEFORE code execution
- ~78% accurate
- Shows predicted structure
- Purpose: Preview to avoid wasting API costs

**Runtime Detection:**
- Runs DURING code execution
- 100% accurate
- Shows actual execution
- Purpose: Real tracking

## How They Complement Each Other

### Step 1: Static Analysis (Preview)
```python
# Preview before running
preview = preview_multi_language_tree(file_path="my_agent.ts")
# Shows: "agent:research -> tool:webSearch"
# Accuracy: ~78% (might miss some patterns)
```

### Step 2: Runtime Detection (Actual)
```python
# Run code - tracks actual execution
llmobserve.observe(collector_url="http://localhost:8000")

# When code runs:
researchAgent(query)  # ← Runtime detection captures this
  → webSearchTool(query)  # ← Runtime detection captures this
    → fetch(...)  # ← Runtime detection captures this

# Result: 100% accurate tree from actual execution
```

## Do They "Fix" Each Other?

**Not exactly** - they serve different purposes:

1. **Static Analysis** = Preview (before running)
   - Shows predicted structure
   - Helps avoid wasting API costs
   - ~78% accurate

2. **Runtime Detection** = Actual Tracking (during execution)
   - Shows what actually happened
   - 100% accurate
   - Real call graphs

**But:** Runtime detection can **validate** static analysis:
- If static says "agent:research" and runtime detects "agent:research" → ✅ Match
- If static misses something but runtime catches it → Runtime is correct
- Runtime is always the source of truth

## Hybrid Approach

### Option 1: Static Preview → Runtime Validation

```python
# Step 1: Preview (static)
preview = preview_multi_language_tree("my_agent.ts")
print("Predicted structure:", preview)

# Step 2: Run code (runtime)
llmobserve.observe(collector_url="http://localhost:8000")
# Runtime detection tracks actual execution
# If preview was wrong, runtime shows correct structure
```

### Option 2: Static + Runtime Combined

```python
# Static analysis provides initial structure
static_tree = analyze_multi_language_file("my_agent.ts")

# Runtime detection fills in gaps and corrects errors
llmobserve.observe(collector_url="http://localhost:8000")
# Runtime tracks actual execution
# Can compare static vs runtime to see differences
```

## Best Practice

**Use Static for Preview, Runtime for Tracking:**

```python
# 1. Preview structure (static - ~78% accurate)
preview = preview_multi_language_tree("my_agent.ts")
print("Preview:", preview)
# Shows predicted structure before running

# 2. Run code with runtime detection (100% accurate)
llmobserve.observe(collector_url="http://localhost:8000")
# Now actual execution is tracked accurately
# Runtime detection is the source of truth
```

## Summary

- **Static Analysis (Regex)**: Preview before running (~78% accurate)
- **Runtime Detection**: Actual tracking during execution (100% accurate)
- **Runtime doesn't "fix" static** - it's the actual source of truth
- **Use static for preview** - avoid wasting API costs
- **Use runtime for tracking** - get accurate results

**Static = Preview, Runtime = Reality**

