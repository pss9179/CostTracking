#!/usr/bin/env python3
"""
Test Multi-Language Static Analyzer

Tests agent detection across TypeScript, JavaScript, Go, Python, and more!
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from llmobserve.multi_language_analyzer import preview_multi_language_tree, analyze_multi_language_code


def test_language(name: str, code: str, language: str):
    """Test a language."""
    print(f"\n{'='*70}")
    print(f"TEST: {name} ({language.upper()})")
    print('='*70)
    
    try:
        preview = preview_multi_language_tree(code=code, language=language)
        print(preview)
        print("\n✅ SUCCESS")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run multi-language tests."""
    print("\n" + "="*70)
    print("🌍 MULTI-LANGUAGE STATIC ANALYZER TEST")
    print("="*70)
    
    test_cases = [
        # TypeScript
        ("TypeScript Agent", """
export async function researchAgent(query: string): Promise<string> {
    const results = await webSearchTool(query);
    return results;
}

async function webSearchTool(query: string): Promise<string> {
    const response = await fetch(`https://api.example.com/search?q=${query}`);
    return await response.text();
}
""", "typescript"),
        
        # JavaScript
        ("JavaScript Agent", """
async function researchAgent(query) {
    const results = await webSearchTool(query);
    return results;
}

async function webSearchTool(query) {
    const response = await fetch(`https://api.example.com/search?q=${query}`);
    return await response.text();
}
""", "javascript"),
        
        # TypeScript with class
        ("TypeScript Class Agent", """
class ResearchAgent {
    async run(query: string): Promise<string> {
        const results = await this.webSearchTool(query);
        return results;
    }
    
    private async webSearchTool(query: string): Promise<string> {
        const response = await fetch(`https://api.example.com/search?q=${query}`);
        return await response.text();
    }
}
""", "typescript"),
        
        # Go
        ("Go Agent", """
package main

func researchAgent(query string) string {
    results := webSearchTool(query)
    return results
}

func webSearchTool(query string) string {
    resp, _ := http.Get("https://api.example.com/search?q=" + query)
    return resp.Body
}
""", "go"),
        
        # Java
        ("Java Agent", """
public class ResearchAgent {
    public String researchAgent(String query) {
        String results = webSearchTool(query);
        return results;
    }
    
    private String webSearchTool(String query) {
        // HTTP call
        return "results";
    }
}
""", "java"),
        
        # Python (for comparison)
        ("Python Agent", """
def research_agent(query: str):
    results = web_search_tool(query)
    return results

def web_search_tool(query: str):
    import requests
    return requests.get(f"https://api.example.com/search?q={query}")
""", "python"),
        
        # TypeScript with OpenAI
        ("TypeScript with OpenAI", """
import OpenAI from 'openai';

const client = new OpenAI();

async function researchAgent(query: string) {
    const response = await client.chat.completions.create({
        model: 'gpt-4',
        messages: [{ role: 'user', content: query }]
    });
    return response.choices[0].message.content;
}
""", "typescript"),
        
        # JavaScript with Axios
        ("JavaScript with Axios", """
const axios = require('axios');

async function researchAgent(query) {
    const response = await axios.get(`https://api.example.com/search?q=${query}`);
    return response.data;
}
""", "javascript"),
    ]
    
    passed = 0
    failed = 0
    
    for name, code, language in test_cases:
        success = test_language(name, code, language)
        if success:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*70)
    print("📊 MULTI-LANGUAGE TEST SUMMARY")
    print("="*70)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📝 Total: {len(test_cases)}")
    print("="*70)


if __name__ == "__main__":
    main()

