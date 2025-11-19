"""
Same test but WITH llmobserve tracking initialized.
This tests that tracking works before CLI labeling.
"""
import os
import llmobserve
from openai import OpenAI

# Initialize LLMObserve tracking
llmobserve.observe(
    collector_url="https://llmobserve-production.up.railway.app",
    api_key=os.getenv("LLMOBSERVE_API_KEY")
)

print("✅ LLMObserve tracking initialized")
print(f"   Collector: https://llmobserve-production.up.railway.app")
print(f"   API Key: {os.getenv('LLMOBSERVE_API_KEY')[:20]}...")
print()


def web_search(query: str) -> str:
    """Simulated web search tool."""
    return f"Search results for: {query}"


def calculator(expression: str) -> float:
    """Calculator tool for math operations."""
    try:
        return eval(expression)
    except Exception as e:
        return f"Error: {e}"


def summarize_text(text: str) -> str:
    """Summarize text using LLM."""
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Summarize the following text in 2 sentences."},
            {"role": "user", "content": text}
        ],
        max_tokens=100
    )
    return response.choices[0].message.content


def research_agent(topic: str) -> dict:
    """Research agent - makes multiple LLM calls."""
    client = OpenAI()
    
    # Generate research questions
    questions_response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Using cheaper model for testing
        messages=[
            {"role": "system", "content": "Generate 2 research questions."},
            {"role": "user", "content": f"About: {topic}"}
        ],
        max_tokens=100
    )
    questions = questions_response.choices[0].message.content
    
    # Search
    search_results = []
    for question in questions.split('\n')[:2]:
        if question.strip():
            result = web_search(question)
            search_results.append(result)
    
    # Synthesize
    synthesis_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Synthesize briefly."},
            {"role": "user", "content": f"Synthesize: {' | '.join(search_results)}"}
        ],
        max_tokens=150
    )
    
    return {
        "questions": questions,
        "synthesis": synthesis_response.choices[0].message.content
    }


def writer_agent(content: str) -> str:
    """Writer agent - polishes content."""
    client = OpenAI()
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Polish this briefly."},
            {"role": "user", "content": content[:200]}  # Limit input
        ],
        max_tokens=200
    )
    
    return response.choices[0].message.content


def analyzer_agent(data: str) -> dict:
    """Analyzer agent - extracts insights."""
    client = OpenAI()
    
    # Analyze sentiment
    sentiment_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Sentiment: positive, negative, or neutral?"},
            {"role": "user", "content": data[:200]}
        ],
        max_tokens=50
    )
    
    # Summarize
    summary = summarize_text(data[:200])
    
    return {
        "sentiment": sentiment_response.choices[0].message.content,
        "summary": summary,
        "word_count": len(data.split())
    }


def orchestrator_workflow(topic: str) -> dict:
    """Main orchestrator coordinating multiple agents."""
    print(f"🔄 Starting workflow for: {topic}")
    
    # Research
    print("   📚 Running research agent...")
    research_results = research_agent(topic)
    
    # Write
    print("   ✍️  Running writer agent...")
    polished_content = writer_agent(research_results["synthesis"])
    
    # Analyze
    print("   📊 Running analyzer agent...")
    analysis = analyzer_agent(polished_content)
    
    print("   ✅ Workflow complete")
    
    return {
        "research": research_results,
        "content": polished_content,
        "analysis": analysis
    }


if __name__ == "__main__":
    print("="*60)
    print("TEST: Multi-Agent Workflow with Cost Tracking")
    print("="*60)
    print()
    
    # Run workflow
    result = orchestrator_workflow("AI trends 2024")
    
    print()
    print("="*60)
    print("RESULTS")
    print("="*60)
    print(f"✅ Workflow completed successfully")
    print(f"📝 Content generated: {len(result['content'])} chars")
    print(f"😊 Sentiment: {result['analysis']['sentiment']}")
    print(f"🔢 Word count: {result['analysis']['word_count']}")
    print()
    print("💰 Check dashboard at: https://llmobserve.com/dashboard")
    print("   Should show 'Untracked' costs")
    print()

