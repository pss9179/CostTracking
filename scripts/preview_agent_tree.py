#!/usr/bin/env python3
"""
Preview Agent Tree - Analyze code BEFORE running it!

Shows what agents/tools/steps will be called without executing code.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from llmobserve.static_analyzer import preview_agent_tree, analyze_code_file


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python preview_agent_tree.py <python_file>")
        print("\nExample:")
        print("  python preview_agent_tree.py my_agent.py")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🔍 Analyzing code BEFORE execution...")
    print("=" * 60 + "\n")
    
    preview = preview_agent_tree(file_path=file_path)
    print(preview)
    
    print("\n" + "=" * 60)
    print("✅ Preview complete! No code executed - no API costs!")
    print("=" * 60)


if __name__ == "__main__":
    main()

