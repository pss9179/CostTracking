"""
Test agent system with multiple agents, tools, and hierarchical tracking.
This will be used to test the full LLMObserve system.
"""
import os
from openai import OpenAI


def web_search(query: str) -> str:
    """Simulated web search tool."""
    # In real scenario, this would call an API
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
    """
    Research agent that finds and synthesizes information.
    Makes multiple LLM calls and uses tools.
    """
    client = OpenAI()
    
    # Step 1: Generate research questions
    questions_response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a research assistant."},
            {"role": "user", "content": f"Generate 3 specific research questions about {topic}"}
        ],
        max_tokens=200
    )
    questions = questions_response.choices[0].message.content
    
    # Step 2: Search for each question
    search_results = []
    for question in questions.split('\n')[:3]:
        if question.strip():
            result = web_search(question)
            search_results.append(result)
    
    # Step 3: Synthesize findings
    synthesis_response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Synthesize research findings."},
            {"role": "user", "content": f"Synthesize: {' | '.join(search_results)}"}
        ],
        max_tokens=300
    )
    
    return {
        "questions": questions,
        "synthesis": synthesis_response.choices[0].message.content
    }


def writer_agent(content: str) -> str:
    """
    Writer agent that polishes and formats content.
    """
    client = OpenAI()
    
    # Polish content
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional writer. Polish this content."},
            {"role": "user", "content": content}
        ],
        max_tokens=500
    )
    
    return response.choices[0].message.content


def analyzer_agent(data: str) -> dict:
    """
    Analyzer agent that extracts insights.
    Uses tools and makes multiple calls.
    """
    client = OpenAI()
    
    # Analyze sentiment
    sentiment_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Analyze sentiment: positive, negative, or neutral."},
            {"role": "user", "content": data}
        ],
        max_tokens=50
    )
    
    # Extract key points
    summary = summarize_text(data)
    
    # Calculate some metrics
    word_count = len(data.split())
    char_count = len(data)
    
    return {
        "sentiment": sentiment_response.choices[0].message.content,
        "summary": summary,
        "word_count": word_count,
        "char_count": char_count
    }


def orchestrator_workflow(topic: str) -> dict:
    """
    Main orchestrator that coordinates multiple agents.
    This creates a hierarchical workflow.
    """
    print(f"Starting workflow for topic: {topic}")
    
    # Step 1: Research
    print("Running research agent...")
    research_results = research_agent(topic)
    
    # Step 2: Write
    print("Running writer agent...")
    polished_content = writer_agent(research_results["synthesis"])
    
    # Step 3: Analyze
    print("Running analyzer agent...")
    analysis = analyzer_agent(polished_content)
    
    return {
        "research": research_results,
        "content": polished_content,
        "analysis": analysis
    }


if __name__ == "__main__":
    # Run the full workflow
    result = orchestrator_workflow("artificial intelligence trends")
    print("\n=== RESULTS ===")
    print(f"Content: {result['content'][:200]}...")
    print(f"Sentiment: {result['analysis']['sentiment']}")
    print(f"Word count: {result['analysis']['word_count']}")

