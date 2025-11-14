"""
Testing different strategies for sending codebase to LLM:
1. Full codebase (best context, but expensive)
2. Per-file (good balance)
3. Summaries only (cheap, but loses context)
4. Hybrid (smart chunks with context)
"""

import os
from pathlib import Path
from typing import List, Dict

def estimate_tokens(text: str) -> int:
    """Rough token estimate (1 token ≈ 4 characters)."""
    return len(text) // 4

def get_codebase_size(root: str = ".") -> Dict:
    """Calculate total codebase size."""
    total_files = 0
    total_lines = 0
    total_chars = 0
    files_by_size = []
    
    for py_file in Path(root).rglob("*.py"):
        if any(skip in str(py_file) for skip in ["__pycache__", ".git", "node_modules", ".venv", "venv"]):
            continue
        
        try:
            with open(py_file, 'r') as f:
                content = f.read()
                lines = len(content.splitlines())
                chars = len(content)
                
                total_files += 1
                total_lines += lines
                total_chars += chars
                
                files_by_size.append({
                    "file": str(py_file),
                    "lines": lines,
                    "chars": chars,
                    "tokens": estimate_tokens(content),
                })
        except:
            pass
    
    files_by_size.sort(key=lambda x: x["tokens"], reverse=True)
    
    # Calculate total tokens by reading all files
    total_tokens = 0
    for file_info in files_by_size:
        total_tokens += file_info["tokens"]
    
    return {
        "total_files": total_files,
        "total_lines": total_lines,
        "total_chars": total_chars,
        "total_tokens": total_tokens,
        "files": files_by_size,
    }

def strategy_1_full_codebase(root: str = ".") -> Dict:
    """Strategy 1: Send entire codebase at once."""
    stats = get_codebase_size(root)
    
    # Concatenate all files
    full_code = []
    for file_info in stats["files"]:
        with open(file_info["file"], 'r') as f:
            full_code.append(f"# File: {file_info['file']}\n{f.read()}\n\n")
    
    full_text = "".join(full_code)
    tokens = estimate_tokens(full_text)
    
    return {
        "strategy": "Full Codebase",
        "tokens": tokens,
        "cost_gpt4o": tokens * 0.0000025,  # $2.50 per 1M input tokens
        "cost_claude": tokens * 0.000003,  # $3 per 1M input tokens
        "fits_context": tokens < 128000,  # GPT-4o context window
        "pros": [
            "✅ Full context - LLM sees everything",
            "✅ Understands cross-file relationships",
            "✅ Can suggest consistent naming across files",
            "✅ Understands architecture"
        ],
        "cons": [
            "❌ Expensive ($10-50+ for large codebases)",
            "❌ May exceed context window (128k tokens)",
            "❌ Slow (takes time to process)",
            "❌ Overkill for simple labeling"
        ]
    }

def strategy_2_per_file(root: str = ".") -> Dict:
    """Strategy 2: Send each file separately."""
    stats = get_codebase_size(root)
    
    total_cost = 0
    files_processed = 0
    
    for file_info in stats["files"][:10]:  # Sample first 10
        tokens = file_info["tokens"]
        cost = tokens * 0.0000025  # GPT-4o pricing
        total_cost += cost
        files_processed += 1
    
    avg_cost_per_file = total_cost / files_processed if files_processed > 0 else 0
    estimated_total_cost = avg_cost_per_file * stats["total_files"]
    
    return {
        "strategy": "Per-File Analysis",
        "files": stats["total_files"],
        "avg_tokens_per_file": sum(f["tokens"] for f in stats["files"][:10]) / 10 if stats["files"] else 0,
        "estimated_total_cost": estimated_total_cost,
        "pros": [
            "✅ Fits in context window (each file < 128k)",
            "✅ More affordable ($0.01-0.10 per file)",
            "✅ Can process in parallel",
            "✅ Good balance of context vs cost"
        ],
        "cons": [
            "❌ Loses cross-file context",
            "❌ May miss architectural patterns",
            "❌ Can't suggest consistent naming across files"
        ]
    }

def strategy_3_smart_chunks(root: str = ".") -> Dict:
    """Strategy 3: Smart chunking with context (BEST)."""
    stats = get_codebase_size(root)
    
    # Group related files (same directory, imports, etc.)
    # For demo, just show concept
    chunks = []
    current_chunk = {"files": [], "tokens": 0}
    max_chunk_tokens = 50000  # Leave room for prompt + response
    
    for file_info in stats["files"]:
        if current_chunk["tokens"] + file_info["tokens"] > max_chunk_tokens:
            chunks.append(current_chunk)
            current_chunk = {"files": [], "tokens": 0}
        
        current_chunk["files"].append(file_info["file"])
        current_chunk["tokens"] += file_info["tokens"]
    
    if current_chunk["files"]:
        chunks.append(current_chunk)
    
    total_cost = sum(chunk["tokens"] * 0.0000025 for chunk in chunks)
    
    return {
        "strategy": "Smart Chunks (Hybrid)",
        "chunks": len(chunks),
        "avg_tokens_per_chunk": sum(c["tokens"] for c in chunks) / len(chunks) if chunks else 0,
        "estimated_total_cost": total_cost,
        "pros": [
            "✅ Best of both worlds",
            "✅ Groups related files (maintains context)",
            "✅ Fits in context window",
            "✅ More affordable than full codebase",
            "✅ Better context than per-file"
        ],
        "cons": [
            "⚠️  More complex to implement",
            "⚠️  Need to detect file relationships"
        ]
    }

def strategy_4_summary_only(root: str = ".") -> Dict:
    """Strategy 4: Just send summaries (API calls, functions, etc.)."""
    # This would be the AST-based summary
    stats = get_codebase_size(root)
    
    # Generate summary (much smaller)
    summary = f"""
    Codebase Summary:
    - {stats['total_files']} Python files
    - {stats['total_lines']} total lines
    - API calls found: [would scan and list]
    - Functions: [would scan and list]
    """
    
    tokens = estimate_tokens(summary)
    
    return {
        "strategy": "Summary Only",
        "tokens": tokens,
        "cost": tokens * 0.0000025,
        "pros": [
            "✅ Very cheap ($0.001-0.01)",
            "✅ Fast",
            "✅ Fits easily in context"
        ],
        "cons": [
            "❌ Loses all semantic context",
            "❌ Can't understand code meaning",
            "❌ Poor label suggestions",
            "❌ Not much better than AST parsing"
        ]
    }

if __name__ == "__main__":
    print("=" * 80)
    print("LLM CODEBASE ANALYSIS STRATEGIES")
    print("=" * 80)
    
    # Analyze current codebase
    stats = get_codebase_size(".")
    print(f"\n📊 Codebase Stats:")
    print(f"  Files: {stats['total_files']}")
    print(f"  Lines: {stats['total_lines']:,}")
    print(f"  Estimated tokens: {stats['total_tokens']:,}")
    print()
    
    # Compare strategies
    strategies = [
        strategy_1_full_codebase("."),
        strategy_2_per_file("."),
        strategy_3_smart_chunks("."),
        strategy_4_summary_only("."),
    ]
    
    for strat in strategies:
        print("=" * 80)
        print(f"📋 {strat['strategy']}")
        print("=" * 80)
        
        if "tokens" in strat:
            print(f"Tokens: {strat['tokens']:,}")
            if "cost" in strat:
                print(f"Cost: ${strat['cost']:.2f}")
            elif "cost_gpt4o" in strat:
                print(f"Cost (GPT-4o): ${strat['cost_gpt4o']:.2f}")
                print(f"Cost (Claude): ${strat['cost_claude']:.2f}")
                print(f"Fits context: {strat['fits_context']}")
        
        if "estimated_total_cost" in strat:
            print(f"Estimated total cost: ${strat['estimated_total_cost']:.2f}")
        
        print("\nPros:")
        for pro in strat['pros']:
            print(f"  {pro}")
        
        print("\nCons:")
        for con in strat['cons']:
            print(f"  {con}")
        print()
    
    print("=" * 80)
    print("🎯 RECOMMENDATION")
    print("=" * 80)
    print("""
BEST APPROACH: Strategy 3 (Smart Chunks) + Per-File Fallback

1. Try to group related files:
   - Same directory
   - Import relationships
   - Related functionality
   
2. Send chunks of ~50k tokens each:
   - Maintains context
   - Fits in context window
   - Affordable ($0.10-0.50 per chunk)
   
3. For very large files, fall back to per-file

4. Use this prompt structure:
   ```
   You are analyzing a codebase for LLM observability labeling.
   
   Here are related files from the same module:
   [File 1: agent.py]
   [code...]
   
   [File 2: tools.py]
   [code...]
   
   Analyze and suggest section() labels for all API calls.
   Consider the architecture and naming conventions.
   ```
   
5. Benefits:
   - LLM sees related code together
   - Understands patterns
   - Suggests consistent names
   - Still affordable
    """)

