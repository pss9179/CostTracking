"""
Sample agent code for testing AI instrumentation.

This file demonstrates a typical agent workflow that should be instrumented.
"""
import openai
from langchain.agents import AgentExecutor
from langchain.tools import Tool


def web_search(query):
    """Search the web for information."""
    # Simulated web search
    return f"Results for: {query}"


def calculator(expression):
    """Evaluate a mathematical expression."""
    return eval(expression)


def research_agent(topic):
    """Main research agent that orchestrates research workflow."""
    # Initialize OpenAI client
    client = openai.OpenAI()
    
    # Step 1: Generate research questions
    questions_response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a research assistant."},
            {"role": "user", "content": f"Generate 3 research questions about {topic}"}
        ]
    )
    
    questions = questions_response.choices[0].message.content
    
    # Step 2: Search for each question
    search_results = []
    for question in questions.split('\n'):
        if question.strip():
            result = web_search(question)
            search_results.append(result)
    
    # Step 3: Synthesize findings
    synthesis_response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a research synthesizer."},
            {"role": "user", "content": f"Synthesize these findings:\n{' '.join(search_results)}"}
        ]
    )
    
    return synthesis_response.choices[0].message.content


def writer_agent(content):
    """Agent that writes polished content."""
    client = openai.OpenAI()
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional writer."},
            {"role": "user", "content": f"Polish this content:\n{content}"}
        ]
    )
    
    return response.choices[0].message.content


def create_langchain_agent():
    """Create a LangChain agent with tools."""
    from langchain.llms import OpenAI
    
    # Define tools
    tools = [
        Tool(name="Search", func=web_search, description="Search the web"),
        Tool(name="Calculator", func=calculator, description="Calculate math expressions"),
    ]
    
    # Create agent
    llm = OpenAI(temperature=0)
    agent = AgentExecutor(
        tools=tools,
        llm=llm,
        verbose=True
    )
    
    return agent


if __name__ == "__main__":
    # Run research agent
    result = research_agent("artificial intelligence")
    print(result)
    
    # Run writer agent
    polished = writer_agent(result)
    print(polished)

