#!/usr/bin/env python3
"""
Test static analysis - preview agent tree without running code!
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from llmobserve.static_analyzer import preview_agent_tree

# Example agent code
example_code = """
from openai import OpenAI
import requests

client = OpenAI()

def research_agent(query: str, max_iterations: int = 3):
    \"\"\"Main research agent with loop\"\"\"
    for i in range(max_iterations):
        # Tool call 1: Search
        search_results = web_search_tool(query)
        
        # Tool call 2: Analyze
        analysis = analyze_tool(search_results)
        
        # LLM call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": analysis}]
        )
        
        if response.choices[0].message.content == "DONE":
            break
    
    return response

def web_search_tool(query: str):
    \"\"\"Web search tool\"\"\"
    response = requests.get(f"https://api.example.com/search?q={query}")
    return response.text

def analyze_tool(data: str):
    \"\"\"Analysis tool\"\"\"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Analyze: {data}"}]
    )
    return response.choices[0].message.content
"""

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🔍 STATIC ANALYSIS: Preview Agent Tree BEFORE Execution")
    print("=" * 70)
    print("\n✅ No code executed - no API costs!")
    print("✅ See agent structure without running!")
    print("\n" + "-" * 70 + "\n")
    
    preview = preview_agent_tree(code=example_code, filename="example_agent.py")
    print(preview)
    
    print("\n" + "=" * 70)
    print("✅ Preview complete! You can see the structure without running code!")
    print("=" * 70)

