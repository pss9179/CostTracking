"""
Test Agent with Tool Hierarchy for LLMObserve
Creates a simple 3-level hierarchy: Agent → Tool → LLM calls
"""
import os
from dotenv import load_dotenv
from openai import OpenAI
from llmobserve import observe, agent, section

# Load environment variables
load_dotenv()

# Configure LLMObserve
observe(
    collector_url="https://llmobserve-api-production-d791.up.railway.app",
    api_key="llmo_sk_ff9fcd2aa077f4bde74ef615ecde7016875524b88fae64a2",
    flush_interval_ms=500,
    auto_start_proxy=False  # Disable proxy auto-start
)

# Initialize OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("❌ ERROR: OPENAI_API_KEY environment variable not set.")
    print("   Please set it and run again: export OPENAI_API_KEY='your-key'")
    exit(1)

openai_client = OpenAI(api_key=openai_api_key)


@agent("research_assistant")
def research_agent(query: str):
    """
    Main agent that orchestrates research tasks.
    """
    print(f"\n🤖 Research Agent starting: {query}")
    
    # Step 1: Generate search queries
    search_queries = generate_search_queries(query)
    
    # Step 2: Analyze each query
    results = []
    for i, search_query in enumerate(search_queries[:2]):  # Limit to 2 for testing
        print(f"\n🔍 Analyzing query {i+1}: {search_query}")
        analysis = analyze_query(search_query)
        results.append(analysis)
    
    # Step 3: Synthesize results
    synthesis = synthesize_results(query, results)
    
    print(f"\n✅ Research complete!")
    return synthesis


def generate_search_queries(topic: str) -> list:
    """
    Tool: Generate multiple search queries for a topic.
    """
    with section("tool:search_query_generator"):
        print("  → Generating search queries...")
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Generate 3 diverse search queries for the topic."},
                {"role": "user", "content": f"Topic: {topic}"}
            ],
            max_tokens=150
        )
        
        queries_text = response.choices[0].message.content
        queries = [q.strip() for q in queries_text.split("\n") if q.strip() and not q.startswith("#")]
        
        print(f"  ✓ Generated {len(queries)} queries")
        return queries[:3]


def analyze_query(query: str) -> str:
    """
    Tool: Analyze a single search query.
    """
    with section("tool:query_analyzer"):
        print(f"    → Analyzing: {query[:50]}...")
        
        # Step 1: Get initial analysis
        with section("step:initial_analysis"):
            response1 = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Analyze this search query and provide key insights."},
                    {"role": "user", "content": query}
                ],
                max_tokens=100
            )
            initial = response1.choices[0].message.content
        
        # Step 2: Extract keywords
        with section("step:keyword_extraction"):
            response2 = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract 5 key terms from this text."},
                    {"role": "user", "content": initial}
                ],
                max_tokens=50
            )
            keywords = response2.choices[0].message.content
        
        print(f"    ✓ Analysis complete")
        return f"{initial}\n\nKeywords: {keywords}"


def synthesize_results(original_query: str, results: list) -> str:
    """
    Tool: Synthesize all results into a final answer.
    """
    with section("tool:synthesizer"):
        print("  → Synthesizing results...")
        
        combined = "\n\n".join([f"Result {i+1}:\n{r}" for i, r in enumerate(results)])
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Synthesize these research results into a cohesive summary."},
                {"role": "user", "content": f"Original query: {original_query}\n\nResults:\n{combined}"}
            ],
            max_tokens=200
        )
        
        synthesis = response.choices[0].message.content
        print(f"  ✓ Synthesis complete")
        return synthesis


if __name__ == "__main__":
    # Run the agent with a test query
    query = "What are the latest trends in AI agent frameworks?"
    
    print("=" * 60)
    print("🚀 Testing LLMObserve Agent Hierarchy Tracking")
    print("=" * 60)
    
    result = research_agent(query)
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULT:")
    print("=" * 60)
    print(result)
    print("\n" + "=" * 60)
    print("✅ Test complete! Check dashboard at:")
    print("   https://app.llmobserve.com/dashboard")
    print("=" * 60)

