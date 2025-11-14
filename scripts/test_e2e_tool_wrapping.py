"""
End-to-end test for tool wrapping architecture.

Tests the complete flow: agent → tools → nested tools → LLM calls.
"""
from unittest.mock import Mock
import asyncio
from llmobserve import (
    observe, agent, tool, wrap_all_tools, wrap_openai_client, 
    context, export_distributed_context, import_distributed_context
)


def create_mock_openai_client():
    """Create a mock OpenAI client for testing."""
    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    
    def mock_create(*args, **kwargs):
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "AI response"
        mock_response.choices[0].message.tool_calls = None
        return mock_response
    
    mock_client.chat.completions.create = Mock(side_effect=mock_create)
    return wrap_openai_client(mock_client)


def test_e2e_basic_flow():
    """Test basic end-to-end flow: agent → tool → LLM."""
    print("\n=== Test: Basic E2E Flow ===")
    
    client = create_mock_openai_client()
    
    @agent("planner")
    def planning_agent(query):
        """Agent that uses tools and LLM."""
        # Verify we're in agent span
        assert "agent:planner" in context.get_section_path()
        
        @tool("research")
        def research_tool(topic):
            # Verify we're in tool span under agent
            path = context.get_section_path()
            assert "agent:planner/tool:research" in path
            
            # Call LLM
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Research {topic}"}]
            )
            
            return response.choices[0].message.content
        
        # Use tool
        result = research_tool(query)
        return result
    
    result = planning_agent("AI agents")
    assert result == "AI response"
    print("✓ Basic E2E flow works: agent → tool → LLM")


def test_e2e_nested_tools():
    """Test nested tool calls."""
    print("\n=== Test: E2E Nested Tools ===")
    
    client = create_mock_openai_client()
    
    @agent("researcher")
    def research_agent():
        """Agent with nested tool calls."""
        
        @tool("search")
        def search_tool():
            path = context.get_section_path()
            assert "agent:researcher/tool:search" in path
            
            @tool("filter")
            def filter_tool():
                path = context.get_section_path()
                assert "tool:search/tool:filter" in path
                
                # Call LLM at the deepest level
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": "Filter results"}]
                )
                return response.choices[0].message.content
            
            return filter_tool()
        
        return search_tool()
    
    result = research_agent()
    assert result == "AI response"
    print("✓ E2E nested tools work correctly")


def test_e2e_with_wrap_all_tools():
    """Test E2E with wrap_all_tools() (framework simulation)."""
    print("\n=== Test: E2E with wrap_all_tools() ===")
    
    client = create_mock_openai_client()
    
    # Define tools as plain functions
    def web_search(query):
        assert "tool:web_search" in context.get_section_path()
        return f"Search results for {query}"
    
    def calculator(expr):
        assert "tool:calculator" in context.get_section_path()
        return eval(expr)
    
    def summarize(text):
        assert "tool:summarize" in context.get_section_path()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": f"Summarize: {text}"}]
        )
        return response.choices[0].message.content
    
    # Wrap all tools (like a framework would)
    tools = wrap_all_tools([web_search, calculator, summarize])
    
    # Agent uses wrapped tools
    @agent("orchestrator")
    def orchestrator():
        # Use each tool
        search_result = tools[0]("AI")
        calc_result = tools[1]("2 + 2")
        summary = tools[2](search_result)
        
        return {
            "search": search_result,
            "calc": calc_result,
            "summary": summary
        }
    
    result = orchestrator()
    assert "Search results" in result["search"]
    assert result["calc"] == 4
    assert result["summary"] == "AI response"
    print("✓ E2E with wrap_all_tools() works correctly")


def test_e2e_distributed_tracing():
    """Test distributed tracing (background workers)."""
    print("\n=== Test: E2E Distributed Tracing ===")
    
    @agent("main_agent")
    def main_agent():
        # Export context
        ctx = export_distributed_context()
        
        # Verify context has trace_id
        assert "trace_id" in ctx
        assert ctx["trace_id"] is not None
        
        return ctx
    
    # Main agent runs
    ctx = main_agent()
    
    # Simulate worker receiving context
    def worker_task(ctx):
        # Import context
        import_distributed_context(ctx)
        
        # Worker's tool
        @tool("background_processor")
        def process_data():
            # Should have same trace_id
            imported_trace = context.get_trace_id()
            assert imported_trace == ctx["trace_id"]
            return "Processed"
        
        return process_data()
    
    result = worker_task(ctx)
    assert result == "Processed"
    print("✓ Distributed tracing maintains trace_id across processes")


async def test_e2e_async_flow():
    """Test async E2E flow."""
    print("\n=== Test: E2E Async Flow ===")
    
    client = create_mock_openai_client()
    
    @agent("async_agent")
    async def async_agent(query):
        assert "agent:async_agent" in context.get_section_path()
        
        @tool("async_tool")
        async def async_tool(data):
            assert "agent:async_agent/tool:async_tool" in context.get_section_path()
            await asyncio.sleep(0.01)
            
            # Call LLM
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": data}]
            )
            return response.choices[0].message.content
        
        result = await async_tool(query)
        return result
    
    result = await async_agent("test")
    assert result == "AI response"
    print("✓ Async E2E flow works correctly")


def test_e2e_expected_tree():
    """Test that the expected tree structure is created."""
    print("\n=== Test: Expected Tree Structure ===")
    
    client = create_mock_openai_client()
    
    @agent("planner")
    def planning_agent():
        path1 = context.get_section_path()
        assert path1 == "agent:planner"
        
        @tool("tool_a")
        def tool_a():
            path2 = context.get_section_path()
            assert path2 == "agent:planner/tool:tool_a"
            
            # Call LLM
            client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Task A"}]
            )
            
            @tool("tool_b")
            def tool_b():
                path3 = context.get_section_path()
                assert path3 == "agent:planner/tool:tool_a/tool:tool_b"
                
                @tool("tool_c")
                def tool_c():
                    path4 = context.get_section_path()
                    assert path4 == "agent:planner/tool:tool_a/tool:tool_b/tool:tool_c"
                    
                    # Call LLM at deepest level
                    client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": "Task C"}]
                    )
                    return "C result"
                
                return tool_c()
            
            return tool_b()
        
        return tool_a()
    
    result = planning_agent()
    assert result == "C result"
    
    # Expected tree:
    # agent:planner
    #   tool:A
    #     llm:openai
    #     tool:B
    #       tool:C
    #         llm:openai
    
    print("✓ Expected tree structure is created correctly")


def run_all_tests():
    """Run all end-to-end tests."""
    print("=" * 60)
    print("End-to-End Tool Wrapping Tests")
    print("=" * 60)
    
    # Initialize SDK
    observe(
        collector_url="http://localhost:8000",
        enable_tool_wrapping=True,
        enable_llm_wrappers=True,
        enable_http_fallback=True
    )
    
    test_e2e_basic_flow()
    test_e2e_nested_tools()
    test_e2e_with_wrap_all_tools()
    test_e2e_distributed_tracing()
    asyncio.run(test_e2e_async_flow())
    test_e2e_expected_tree()
    
    print("\n" + "=" * 60)
    print("✅ All E2E tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()

