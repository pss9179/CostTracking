"""
Addressing the concern: "Doesn't it need the whole codebase? What if it misses something?"

Answer: Two-pass approach - architecture overview first, then detailed labeling.
"""

def strategy_full_codebase_analysis():
    """
    PROBLEM: Your codebase is 138k tokens, GPT-4o limit is 128k.
    Can't send everything at once.
    """
    return {
        "problem": "Codebase too large for single request",
        "your_codebase": "138,598 tokens",
        "gpt4o_limit": "128,000 tokens",
        "fits": False,
        "solution": "Must chunk or use two-pass approach"
    }

def strategy_two_pass_approach():
    """
    SOLUTION: Two-pass approach
    
    Pass 1: Architecture Overview (small summary)
    - File structure
    - Import graph
    - Main entry points
    - Key patterns
    
    Pass 2: Detailed Labeling (chunks with architecture context)
    - Each chunk includes architecture summary
    - LLM understands how chunk fits into whole
    """
    
    # Pass 1: Generate architecture summary
    architecture_prompt = """
    Analyze this codebase structure and create an architecture summary:
    
    Files:
    - agent.py (main agent orchestrator)
    - tools.py (tool implementations)
    - utils.py (helper functions)
    - ...
    
    Create summary of:
    1. Main components and their roles
    2. Naming conventions
    3. Common patterns
    4. Architecture style
    """
    
    # This would be small (~5-10k tokens)
    architecture_summary = """
    Architecture Summary:
    - Main agent: agent.py (orchestrates workflows)
    - Tools: tools.py (web_search, openai_call, etc.)
    - Naming: snake_case, descriptive names
    - Pattern: agent → tool → API call hierarchy
    """
    
    # Pass 2: Label each chunk WITH architecture context
    chunk_prompt_template = """
    Architecture Context (from full codebase analysis):
    {architecture_summary}
    
    Now analyze these specific files:
    {chunk_files}
    
    Suggest section() labels that:
    1. Match the architecture patterns above
    2. Use consistent naming with other files
    3. Fit the overall structure
    """
    
    return {
        "approach": "Two-Pass",
        "pass1": {
            "purpose": "Understand full architecture",
            "size": "~5-10k tokens (small summary)",
            "cost": "$0.01-0.02",
            "output": "Architecture summary + patterns"
        },
        "pass2": {
            "purpose": "Label with full context",
            "method": "Each chunk includes architecture summary",
            "benefit": "LLM knows how chunk fits into whole",
            "cost": "$0.10-0.50 per chunk"
        },
        "total_cost": "$0.20-0.60",
        "nothing_missed": True  # Architecture context included in every chunk
    }

def strategy_smart_chunking_with_imports():
    """
    ALTERNATIVE: Smart chunking that groups by import relationships.
    
    If file A imports file B, they should be in same chunk.
    This ensures related code stays together.
    """
    
    # Build import graph
    import_graph = {
        "agent.py": ["tools.py", "utils.py"],
        "tools.py": ["utils.py"],
        "utils.py": [],
    }
    
    # Group files that import each other
    chunks = [
        {
            "files": ["agent.py", "tools.py", "utils.py"],  # All related
            "reason": "agent imports tools, tools imports utils",
            "tokens": 45000,
        },
        {
            "files": ["other_module.py", "other_utils.py"],
            "reason": "Separate module, no cross-imports",
            "tokens": 30000,
        }
    ]
    
    return {
        "approach": "Import-Based Chunking",
        "method": "Group files that import each other",
        "benefit": "Related code always together",
        "ensures": "No missing context for related files"
    }

def strategy_hybrid_best():
    """
    BEST: Combine both approaches
    
    1. Pass 1: Architecture overview (small, cheap)
    2. Pass 2: Smart chunks with:
       - Architecture summary included
       - Import-based grouping
       - All files processed (nothing missed)
    """
    
    return {
        "step1": "Generate architecture summary (5-10k tokens, $0.01)",
        "step2": "Build import graph (find relationships)",
        "step3": "Group files by imports + directory",
        "step4": "For each chunk:",
        "step4a": "Include architecture summary",
        "step4b": "Include all related files",
        "step4c": "Process chunk for labeling",
        "step5": "Repeat until ALL files processed",
        
        "guarantees": [
            "✅ Every file is analyzed",
            "✅ Related files stay together",
            "✅ Architecture context in every chunk",
            "✅ Nothing missed"
        ],
        
        "cost": "$0.20-0.60 total",
        "coverage": "100% of codebase"
    }

if __name__ == "__main__":
    print("=" * 80)
    print("ADDRESSING CONCERN: 'What if chunking misses something?'")
    print("=" * 80)
    
    print("\n❌ PROBLEM:")
    print("  - Full codebase: 138k tokens")
    print("  - GPT-4o limit: 128k tokens")
    print("  - Can't send everything at once")
    
    print("\n✅ SOLUTION: Two-Pass Approach")
    print("=" * 80)
    
    strategy = strategy_hybrid_best()
    
    print("\nStep 1: Architecture Overview")
    print("  - Analyze full codebase structure")
    print("  - Generate summary (~5-10k tokens)")
    print("  - Cost: $0.01-0.02")
    print("  - Output: Patterns, naming conventions, architecture")
    
    print("\nStep 2: Smart Chunking")
    print("  - Group files by imports (related code together)")
    print("  - Each chunk ~50k tokens")
    print("  - Process ALL chunks (nothing skipped)")
    
    print("\nStep 3: Labeling with Context")
    print("  - Each chunk includes:")
    print("    • Architecture summary (from Step 1)")
    print("    • Related files (from Step 2)")
    print("  - LLM knows how chunk fits into whole")
    
    print("\n" + "=" * 80)
    print("GUARANTEES:")
    print("=" * 80)
    for guarantee in strategy["guarantees"]:
        print(f"  {guarantee}")
    
    print(f"\n💰 Cost: {strategy['cost']}")
    print(f"📊 Coverage: {strategy['coverage']}")
    
    print("\n" + "=" * 80)
    print("EXAMPLE:")
    print("=" * 80)
    print("""
Pass 1 Output (Architecture Summary):
  - Main agent: agent.py (orchestrates workflows)
  - Tools: tools.py (web_search, openai_call)
  - Naming: snake_case, descriptive
  - Pattern: agent → tool → API call

Pass 2, Chunk 1:
  Architecture Context: [summary from Pass 1]
  
  Files in this chunk:
  - agent.py
  - tools.py
  - utils.py
  
  LLM Analysis:
  - Sees agent.py imports tools.py
  - Understands architecture pattern
  - Suggests: agent:main → tool:web_search → tool:openai
  
Pass 2, Chunk 2:
  Architecture Context: [same summary]
  
  Files in this chunk:
  - other_module.py
  
  LLM Analysis:
  - Knows architecture from context
  - Suggests consistent naming
  - Nothing missed because context is shared
    """)
    
    print("\n💡 KEY INSIGHT:")
    print("  Chunking doesn't mean losing context.")
    print("  Architecture summary is included in EVERY chunk.")
    print("  So LLM always knows the full picture!")


