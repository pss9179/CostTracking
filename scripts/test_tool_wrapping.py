"""
Test tool wrapping system.

Tests for @agent, wrap_tool, @tool decorators, nested tools, async support, and idempotency.
"""
import asyncio
import time
from llmobserve import observe, agent, tool, wrap_tool, context


def test_agent_decorator():
    """Test @agent creates root span."""
    print("\n=== Test: Agent Decorator ===")
    
    @agent("researcher")
    def my_agent(query):
        print(f"Agent processing: {query}")
        # Check span is created
        assert context.get_current_section() == "agent:researcher"
        assert context.get_section_path() == "agent:researcher"
        return "result"
    
    result = my_agent("test query")
    assert result == "result"
    
    # After agent exits, stack should be clear
    assert context.get_section_path() == "default"
    print("✓ Agent decorator creates root span")


def test_tool_decorator():
    """Test @tool creates tool span."""
    print("\n=== Test: Tool Decorator ===")
    
    @tool("web_search")
    def search_web(query):
        print(f"Searching: {query}")
        # Check span is created
        assert context.get_current_section() == "tool:web_search"
        return f"Results for {query}"
    
    result = search_web("AI agents")
    assert "AI agents" in result
    
    # After tool exits, stack should be clear
    assert context.get_section_path() == "default"
    print("✓ Tool decorator creates tool span")


def test_wrap_tool_function():
    """Test wrap_tool() wraps a function."""
    print("\n=== Test: wrap_tool() Function ===")
    
    def calculator(expr):
        return eval(expr)
    
    wrapped_calc = wrap_tool(calculator, name="calculator")
    
    result = wrapped_calc("2 + 2")
    assert result == 4
    print("✓ wrap_tool() wraps functions correctly")


def test_nested_tools():
    """Test nested tool calls maintain parent-child relationships."""
    print("\n=== Test: Nested Tools ===")
    
    @agent("planner")
    def planning_agent():
        print("Agent: Starting planning")
        
        @tool("outer_tool")
        def outer_tool():
            print(f"  Outer tool - Path: {context.get_section_path()}")
            assert "agent:planner/tool:outer_tool" in context.get_section_path()
            
            @tool("inner_tool")
            def inner_tool():
                print(f"    Inner tool - Path: {context.get_section_path()}")
                assert "tool:outer_tool/tool:inner_tool" in context.get_section_path()
                return "inner result"
            
            return inner_tool()
        
        result = outer_tool()
        assert result == "inner result"
        return result
    
    result = planning_agent()
    assert result == "inner result"
    print("✓ Nested tools maintain parent-child relationships")


def test_async_agent():
    """Test async agent decorator."""
    print("\n=== Test: Async Agent ===")
    
    @agent("async_researcher")
    async def async_agent(query):
        await asyncio.sleep(0.01)
        assert context.get_current_section() == "agent:async_researcher"
        return f"Async result for {query}"
    
    result = asyncio.run(async_agent("test"))
    assert "Async result" in result
    print("✓ Async agent decorator works correctly")


def test_async_tool():
    """Test async tool decorator."""
    print("\n=== Test: Async Tool ===")
    
    @tool("async_search")
    async def async_search(query):
        await asyncio.sleep(0.01)
        assert context.get_current_section() == "tool:async_search"
        return f"Async search: {query}"
    
    result = asyncio.run(async_search("AI"))
    assert "Async search" in result
    print("✓ Async tool decorator works correctly")


def test_idempotent_wrapping():
    """Test that double wrapping doesn't occur."""
    print("\n=== Test: Idempotent Wrapping ===")
    
    def simple_func():
        return "result"
    
    wrapped1 = wrap_tool(simple_func, name="func")
    wrapped2 = wrap_tool(wrapped1, name="func")  # Try to wrap again
    
    # Should return the same function (already wrapped)
    assert wrapped1 is wrapped2
    assert hasattr(wrapped1, "__llmobserve_wrapped__")
    print("✓ wrap_tool is idempotent (no double wrapping)")


def test_error_handling():
    """Test that exceptions are captured but re-raised."""
    print("\n=== Test: Error Handling ===")
    
    @agent("error_agent")
    def error_agent():
        raise ValueError("Test error")
    
    try:
        error_agent()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert str(e) == "Test error"
        print("✓ Exceptions are captured and re-raised correctly")


def run_all_tests():
    """Run all tool wrapping tests."""
    print("=" * 60)
    print("Tool Wrapping System Tests")
    print("=" * 60)
    
    # Initialize SDK (in memory, no collector)
    observe(
        collector_url="http://localhost:8000",
        enable_tool_wrapping=True,
        enable_http_fallback=False  # Don't need HTTP for these tests
    )
    
    test_agent_decorator()
    test_tool_decorator()
    test_wrap_tool_function()
    test_nested_tools()
    test_async_agent()
    test_async_tool()
    test_idempotent_wrapping()
    test_error_handling()
    
    print("\n" + "=" * 60)
    print("✅ All tool wrapping tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()

