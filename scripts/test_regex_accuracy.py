#!/usr/bin/env python3
"""
Test Regex Accuracy vs Real Code

Tests how accurate regex-based detection is compared to what would actually happen.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from llmobserve.multi_language_analyzer import analyze_multi_language_code


def test_real_world_cases():
    """Test with real-world code patterns."""
    print("\n" + "="*70)
    print("🧪 REGEX ACCURACY TEST: Real-World Code Patterns")
    print("="*70)
    
    test_cases = [
        # Real TypeScript code patterns
        ("TypeScript: Real API Code", """
export async function researchAgent(query: string): Promise<string> {
    try {
        const searchResults = await webSearchTool(query);
        if (!searchResults) {
            throw new Error('No results');
        }
        const analysis = await analyzeTool(searchResults);
        return analysis;
    } catch (error) {
        console.error(error);
        throw error;
    }
}

async function webSearchTool(query: string): Promise<string> {
    const response = await fetch(`https://api.example.com/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.text();
}

async function analyzeTool(data: string): Promise<string> {
    const response = await fetch('https://api.example.com/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data })
    });
    return await response.json();
}
""", "typescript"),
        
        # Real JavaScript code patterns
        ("JavaScript: Real API Code", """
const researchAgent = async (query) => {
    const searchResults = await webSearchTool(query);
    const analysis = await analyzeTool(searchResults);
    return analysis;
};

const webSearchTool = async (query) => {
    const response = await fetch(`https://api.example.com/search?q=${query}`);
    return await response.text();
};

const analyzeTool = async (data) => {
    const response = await fetch('https://api.example.com/analyze', {
        method: 'POST',
        body: JSON.stringify({ data })
    });
    return await response.json();
};
""", "javascript"),
        
        # Complex TypeScript with classes
        ("TypeScript: Class-based Agent", """
import OpenAI from 'openai';

export class ResearchAgent {
    private client: OpenAI;
    
    constructor() {
        this.client = new OpenAI();
    }
    
    async run(query: string): Promise<string> {
        const searchResults = await this.webSearchTool(query);
        const analysis = await this.analyzeTool(searchResults);
        return analysis;
    }
    
    private async webSearchTool(query: string): Promise<string> {
        const response = await fetch(`https://api.example.com/search?q=${query}`);
        return await response.text();
    }
    
    private async analyzeTool(data: string): Promise<string> {
        const response = await this.client.chat.completions.create({
            model: 'gpt-4',
            messages: [{ role: 'user', content: data }]
        });
        return response.choices[0].message.content || '';
    }
}
""", "typescript"),
        
        # Real Go code
        ("Go: Real API Code", """
package main

import (
    "net/http"
    "io/ioutil"
    "strings"
)

func researchAgent(query string) (string, error) {
    results, err := webSearchTool(query)
    if err != nil {
        return "", err
    }
    analysis, err := analyzeTool(results)
    if err != nil {
        return "", err
    }
    return analysis, nil
}

func webSearchTool(query string) (string, error) {
    resp, err := http.Get("https://api.example.com/search?q=" + query)
    if err != nil {
        return "", err
    }
    defer resp.Body.Close()
    body, err := ioutil.ReadAll(resp.Body)
    return string(body), err
}

func analyzeTool(data string) (string, error) {
    resp, err := http.Post("https://api.example.com/analyze", "application/json", strings.NewReader(data))
    if err != nil {
        return "", err
    }
    defer resp.Body.Close()
    body, err := ioutil.ReadAll(resp.Body)
    return string(body), err
}
""", "go"),
        
        # Edge cases that regex might miss
        ("TypeScript: Dynamic Function Names", """
const agentFunctions = {
    researchAgent: async (query: string) => {
        return await webSearchTool(query);
    },
    planningAgent: async (task: string) => {
        return await planTool(task);
    }
};

async function webSearchTool(query: string) {
    const response = await fetch(`https://api.example.com/search?q=${query}`);
    return await response.text();
}

async function planTool(task: string) {
    const response = await fetch(`https://api.example.com/plan?task=${task}`);
    return await response.json();
}
""", "typescript"),
        
        ("JavaScript: Function Expressions", """
const researchAgent = function(query) {
    return webSearchTool(query);
};

const webSearchTool = function(query) {
    return fetch(`https://api.example.com/search?q=${query}`)
        .then(response => response.text());
};
""", "javascript"),
        
        ("TypeScript: Arrow Functions in Objects", """
const agents = {
    research: async (query: string) => {
        const results = await webSearchTool(query);
        return results;
    },
    planning: async (task: string) => {
        const plan = await planTool(task);
        return plan;
    }
};

const webSearchTool = async (query: string) => {
    const response = await fetch(`https://api.example.com/search?q=${query}`);
    return await response.text();
};

const planTool = async (task: string) => {
    const response = await fetch(`https://api.example.com/plan?task=${task}`);
    return await response.json();
};
""", "typescript"),
        
        # What regex CAN'T detect
        ("TypeScript: String-based Function Calls", """
function researchAgent(query: string) {
    const funcName = 'webSearchTool';
    // Regex can't detect this - it's a string, not a function call
    // eval(funcName)(query);  // Would need to run code to detect
    return query;
}

function webSearchTool(query: string) {
    const response = await fetch(`https://api.example.com/search?q=${query}`);
    return await response.text();
}
""", "typescript"),
        
        ("JavaScript: getattr-style Calls", """
function researchAgent(query) {
    const toolName = 'webSearchTool';
    const tool = window[toolName];  // Dynamic - regex can't detect
    if (tool) {
        return tool(query);
    }
    return null;
}

function webSearchTool(query) {
    return fetch(`https://api.example.com/search?q=${query}`)
        .then(response => response.text());
}
""", "javascript"),
    ]
    
    passed = 0
    failed = 0
    missed = []
    
    for name, code, language in test_cases:
        print(f"\n{'='*70}")
        print(f"TEST: {name}")
        print('='*70)
        
        try:
            result = analyze_multi_language_code(code, language)
            
            agents_found = result["total_agents"]
            tools_found = sum(
                1 for agent in result["agents"]
                for _ in [agent] if agent["type"] == "tool"
            ) + sum(
                len([c for c in agent.get("children", []) if c["type"] == "tool"])
                for agent in result["agents"]
            )
            
            print(f"\n📊 Results:")
            print(f"   Agents detected: {agents_found}")
            print(f"   Tools detected: {tools_found}")
            
            # Check if it detected what we expect
            has_agent = agents_found > 0
            has_tools = tools_found > 0
            
            # For most tests, we expect at least 1 agent
            expected_agent = "researchAgent" in code or "research_agent" in code or "research" in code.lower()
            
            if expected_agent and has_agent:
                print(f"   ✅ Agent detected correctly")
                passed += 1
            elif expected_agent and not has_agent:
                print(f"   ❌ Agent NOT detected (missed!)")
                failed += 1
                missed.append(name)
            elif not expected_agent and not has_agent:
                print(f"   ✅ Correctly didn't detect (no agent)")
                passed += 1
            else:
                print(f"   ⚠️  Unexpected detection")
                failed += 1
        
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print("📊 REGEX ACCURACY SUMMARY")
    print("="*70)
    print(f"✅ Correct Detections: {passed}")
    print(f"❌ Missed/Incorrect: {failed}")
    print(f"📝 Total Tests: {len(test_cases)}")
    accuracy = (passed / len(test_cases)) * 100
    print(f"🎯 Accuracy: {accuracy:.1f}%")
    
    if missed:
        print(f"\n⚠️  Missed Cases:")
        for case in missed:
            print(f"   - {case}")
    
    print("="*70)
    
    print("\n💭 HONEST ASSESSMENT:")
    print("-"*70)
    if accuracy >= 90:
        print("✅ Regex is ACCURATE ENOUGH for most cases")
        print("   Good for previewing structure before execution")
    elif accuracy >= 75:
        print("⚠️  Regex is MODERATELY ACCURATE")
        print("   Works for common patterns, but misses edge cases")
        print("   Consider: Running code for more accuracy")
    else:
        print("❌ Regex is NOT ACCURATE ENOUGH")
        print("   Should run code or use LLM for better accuracy")
    
    print("\n🔍 What Regex CAN'T Detect:")
    print("   ❌ Dynamic function calls (getattr, eval)")
    print("   ❌ String-based function names")
    print("   ❌ Complex control flow")
    print("   ❌ Runtime behavior")
    
    print("\n✅ What Regex CAN Detect:")
    print("   ✅ Function definitions (most patterns)")
    print("   ✅ Direct function calls")
    print("   ✅ API call patterns")
    print("   ✅ Basic call graphs")
    
    print("\n💡 Recommendation:")
    if accuracy >= 85:
        print("   ✅ Regex is GOOD ENOUGH for preview")
        print("   ✅ Use it to preview structure before running")
        print("   ✅ Then run code for actual tracking")
    else:
        print("   ⚠️  Regex has limitations")
        print("   💡 Consider: Run code for accurate detection")
        print("   💡 Or: Use LLM for semantic analysis")


if __name__ == "__main__":
    test_real_world_cases()

