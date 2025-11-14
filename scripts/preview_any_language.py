#!/usr/bin/env python3
"""
Preview Agent Tree for ANY Language

Supports TypeScript, JavaScript, Go, Java, Python, and more!
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from llmobserve.multi_language_analyzer import preview_multi_language_tree, analyze_multi_language_file


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python preview_any_language.py <file>")
        print("\nSupported languages:")
        print("  - TypeScript (.ts, .tsx)")
        print("  - JavaScript (.js, .jsx)")
        print("  - Python (.py)")
        print("  - Go (.go)")
        print("  - Java (.java)")
        print("  - Rust (.rs)")
        print("  - Ruby (.rb)")
        print("  - PHP (.php)")
        print("  - C# (.cs)")
        print("  - C++ (.cpp)")
        print("  - C (.c)")
        print("\nExample:")
        print("  python preview_any_language.py my_agent.ts")
        print("  python preview_any_language.py my_agent.js")
        print("  python preview_any_language.py my_agent.go")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("🔍 Analyzing code BEFORE execution...")
    print(f"📁 File: {file_path}")
    print("="*70 + "\n")
    
    preview = preview_multi_language_tree(file_path=file_path)
    print(preview)
    
    print("\n" + "="*70)
    print("✅ Preview complete! No code executed - no API costs!")
    print("="*70)


if __name__ == "__main__":
    main()

