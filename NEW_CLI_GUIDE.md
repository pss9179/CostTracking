# New Production-Grade CLI - Complete Guide

## 🎉 What Changed

**Old way (single-file, risky):**
```bash
llmobserve preview my_agent.py      # One file at a time
llmobserve instrument --auto-apply  # Immediate modification
```

**New way (whole codebase, safe):**
```bash
llmobserve scan .          # Scans entire project
llmobserve review          # Interactive approval
llmobserve apply           # Safe application with validation
```

---

## 📋 New Commands

### `llmobserve scan <path>`
**Scans codebase for LLM-related code WITHOUT modifying anything.**

```bash
# Scan current directory
llmobserve scan .

# Scan specific directory
llmobserve scan agents/

# With custom instructions
llmobserve scan . --instruct "Don't touch utils/ folder"

# Adjust batch size
llmobserve scan . --batch-size 5
```

**What it does:**
1. Finds all Python/JS/TS files
2. Uses AST parsing to detect LLM API calls, agent patterns
3. Builds dependency graph
4. Sends candidates to Claude in batches (3-5 files at once)
5. Generates patches and saves to `.llmobserve/`
6. **DOES NOT modify any files**

**Output:**
```
🔍 Scanning . for LLM-related code...

📊 Found 12 files with LLM code:
  1. research_agent.py (confidence: 90%)
  2. writer_agent.py (confidence: 85%)
  3. utils/tools.py (confidence: 60%)
  ...

💾 Saved candidates to .llmobserve/candidates.json

📤 Send to Claude for refinement? [y/N]: y

🤖 Sending to Claude API for analysis...

✅ Analysis complete!
   12 files analyzed
   24 suggestions generated

📝 Next steps:
   llmobserve review   - Review changes interactively
   llmobserve diff     - Show unified diff
   llmobserve apply    - Apply all changes
```

---

### `llmobserve review`
**Interactive review and approval of suggested changes.**

```bash
llmobserve review
```

**What it does:**
- Shows each suggestion one by one
- Lets you approve (y), reject (n), view full context, or skip
- Saves your decisions

**Example:**
```
📋 Reviewing suggested changes...

[1/12] research_agent.py
   Claude says: This function orchestrates multiple LLM calls...

   Suggestion 1: decorator
   Label: researcher
   Line 15: Main agent function making LLM calls

   - def research_agent(query):
   + @agent("researcher")
   + def research_agent(query):

   Apply this? [y/n/view/skip/quit]: y
   ✅ Approved

   ...

📊 Review complete:
   ✅ Approved: 18
   ❌ Rejected: 6

Run 'llmobserve apply' to apply approved changes.
```

---

### `llmobserve diff`
**Show unified diff of all pending changes (like `git diff`).**

```bash
llmobserve diff
```

**Output:**
```
--- a/research_agent.py
+++ b/research_agent.py
@@ -1,4 +1,6 @@
 import openai
+from llmobserve import agent
 
+@agent("researcher")
 def research_agent(query):
     client = openai.OpenAI()
     ...
```

---

### `llmobserve apply`
**Apply all changes with automatic backups and syntax validation.**

```bash
llmobserve apply

# Skip syntax validation (not recommended)
llmobserve apply --skip-validation
```

**What it does:**
1. Shows unified diff for review
2. Asks for confirmation
3. Creates timestamped backup in `.llmobserve/backups/`
4. Applies patches
5. Runs syntax validation (`python -m py_compile`, `tsc --noEmit`)
6. If validation fails, automatically restores backup
7. Saves apply record for rollback

**Example:**
```
📝 Changes to be applied:

[Shows full unified diff]

Apply all changes? [y/N]: y

🔧 Applying patches...

✅ Successfully applied 18 patches
   Backups saved to .llmobserve/backups/20241118_143025

💡 To undo: llmobserve rollback
```

---

### `llmobserve rollback`
**Undo last changes (or specific backup).**

```bash
# Rollback to latest backup
llmobserve rollback

# Rollback to specific backup
llmobserve rollback --timestamp 20241118_143025
```

**What it does:**
- Restores all files from backup
- Reverts code to exact previous state

---

## 🔒 Safety Features

### 1. **Two-Phase Workflow**
- **Phase 1 (scan):** Analyzes code, generates patches, saves to disk
- **Phase 2 (apply):** User reviews and approves, then applies

**Nothing is modified during scan phase.**

### 2. **Automatic Backups**
Every `apply` creates timestamped backups:
```
.llmobserve/
  backups/
    20241118_143025/
      research_agent.py
      writer_agent.py
      ...
```

### 3. **Syntax Validation**
Before committing changes:
- Python: `python -m py_compile <file>`
- TypeScript: `tsc --noEmit <file>`
- JavaScript: `node --check <file>`

**If validation fails → automatic rollback.**

### 4. **Unified Diff Preview**
Always shows exactly what will change before applying.

### 5. **Dependency Graph**
Scanner builds import dependency graph to provide better context to Claude.

### 6. **Caching**
Only re-analyzes files that changed (based on SHA256 hash).

---

## 🧠 How It Works

### Static Analysis (No LLM)
Scanner uses AST parsing to detect:
- Imports: `openai`, `anthropic`, `langchain`, etc.
- LLM API calls: `.chat.completions.create()`, etc.
- Agent-like patterns: Functions with "agent", "workflow", "task" in name
- Confidence scoring: Higher confidence = more likely to need labeling

### AI Refinement (Claude API)
Refiner batches 3-5 files, sends to Claude:
- Claude sees file content + metadata (imports, LLM calls, patterns)
- Suggests labels based on function purpose
- Generates safe patches (decorators, context managers)
- Returns structured JSON with suggestions

### Patch Generation
Patcher creates unified diffs:
- Standard `diff` format (works with `patch` command)
- One patch file per source file
- Stored in `.llmobserve/patches/`

### Application
Safe application with validation:
1. Backup original files
2. Apply patches using `patch -p1`
3. Validate syntax
4. If fail → restore backup
5. If success → save apply record

---

## 📂 Directory Structure

```
your_project/
  .llmobserve/
    candidates.json       # Detected files from scan
    scan.json            # Claude's analysis results
    cache.json           # File hashes for caching
    apply_history.json   # Record of all applies
    patches/             # Generated patch files
      research_agent.py.patch
      writer_agent.py.patch
    backups/             # Timestamped backups
      20241118_143025/
        research_agent.py
        ...
```

---

## 🎯 Use Cases

### 1. **New Project**
```bash
# Add llmobserve tracking
# ... (add observe() to code)

# Scan and label everything
llmobserve scan .
llmobserve review
llmobserve apply
```

### 2. **Existing Project**
```bash
# Already tracking but costs show "Untracked"
llmobserve scan .
llmobserve diff
llmobserve apply
```

### 3. **Selective Labeling**
```bash
# Only label agents/ directory
llmobserve scan agents/

# Or use custom instructions
llmobserve scan . --instruct "Only label files with 'agent' in the name"
```

### 4. **Safe Experimentation**
```bash
llmobserve scan .
llmobserve apply
# Test your code...
# If something breaks:
llmobserve rollback
```

---

## 🆚 Comparison

| Feature | Old CLI | New CLI |
|---------|---------|---------|
| **Scope** | Single file | Whole codebase |
| **Safety** | Immediate modification | Two-phase scan → apply |
| **Validation** | None | Syntax validation |
| **Backups** | `.bak` files | Timestamped backups |
| **Rollback** | Manual | One command |
| **Batching** | 1 file = 1 API call | 3-5 files = 1 API call |
| **Caching** | None | SHA256-based caching |
| **Dependencies** | No awareness | Dependency graph |
| **Review** | None | Interactive review mode |
| **Custom Instructions** | No | Plain English via `--instruct` |

---

## 💰 Cost Savings

**Old way:**
- 50 files × 1 API call each = 50 API calls
- 50 × $0.01 = $0.50 per scan

**New way:**
- 50 files ÷ 3 per batch = 17 API calls
- 17 × $0.01 = $0.17 per scan

**70% cost reduction + caching = even more savings.**

---

## 🔄 Migration

**Old commands still work:**
```bash
# These still work (backward compatible)
llmobserve preview my_agent.py
llmobserve instrument my_agent.py --auto-apply
```

**But new commands are better:**
```bash
# Use these instead
llmobserve scan .
llmobserve review
llmobserve apply
```

---

## ⚠️ Known Limitations

1. **Single-file context:** Claude sees one file at a time (batched, but not whole codebase view)
2. **Python/JS/TS only:** Other languages not yet supported
3. **Requires patch command:** Must have `patch` utility installed (standard on Unix)
4. **No git integration:** Doesn't commit changes automatically

---

## 🚀 Best Practices

1. **Review before apply:** Always run `llmobserve review` or `llmobserve diff`
2. **Test after apply:** Run your tests after applying changes
3. **Use version control:** Commit before and after using llmobserve
4. **Custom instructions:** Use `--instruct` to guide Claude's suggestions
5. **Start small:** Try on one directory first before whole codebase

---

## 📞 Troubleshooting

**Q: Scan found no files**  
A: Check you're in the right directory. Try `llmobserve scan . --verbose`

**Q: Syntax validation failed**  
A: Changes were auto-rolled back. Check `.llmobserve/patches/` to see what was attempted.

**Q: Claude suggestions are wrong**  
A: Use `llmobserve review` to reject bad suggestions, or add `--instruct` with guidance.

**Q: How do I undo everything?**  
A: `llmobserve rollback` restores from backup.

**Q: Can I edit patches manually?**  
A: Yes! Patches are in `.llmobserve/patches/`. Edit them, then run `llmobserve apply`.

---

## 🎓 Advanced: Manual Patch Editing

Patches are standard unified diff format. You can edit them:

```bash
# 1. Run scan
llmobserve scan .

# 2. Edit patch manually
nano .llmobserve/patches/research_agent.py.patch

# 3. Apply your edited patches
llmobserve apply
```

---

**This is production-ready. Ship it.** 🚀

