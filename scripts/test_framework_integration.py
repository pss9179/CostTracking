"""
Test framework integration with wrap_all_tools().

Tests for LangChain, CrewAI, AutoGen, LlamaIndex compatibility.
"""
from llmobserve import observe, agent, wrap_all_tools, context


def test_wrap_dict_tools():
    """Test wrap_all_tools() with dict (AutoGen style)."""
    print("\n=== Test: Wrap Dict Tools (AutoGen) ===")
    
    def search(query):
        return f"Search: {query}"
    
    def calc(expr):
        return eval(expr)
    
    tools_dict = {
        "search": search,
        "calc": calc
    }
    
    wrapped = wrap_all_tools(tools_dict)
    
    assert isinstance(wrapped, dict)
    assert "search" in wrapped
    assert "calc" in wrapped
    assert hasattr(wrapped["search"], "__llmobserve_wrapped__")
    assert hasattr(wrapped["calc"], "__llmobserve_wrapped__")
    
    # Test execution
    result = wrapped["search"]("AI")
    assert result == "Search: AI"
    
    print("✓ wrap_all_tools() works with dict")


def test_wrap_list_tools():
    """Test wrap_all_tools() with list (LangChain/CrewAI style)."""
    print("\n=== Test: Wrap List Tools (LangChain/CrewAI) ===")
    
    def tool1(x):
        return x * 2
    
    def tool2(x):
        return x + 10
    
    tools_list = [tool1, tool2]
    wrapped = wrap_all_tools(tools_list)
    
    assert isinstance(wrapped, list)
    assert len(wrapped) == 2
    assert hasattr(wrapped[0], "__llmobserve_wrapped__")
    assert hasattr(wrapped[1], "__llmobserve_wrapped__")
    
    # Test execution
    result1 = wrapped[0](5)
    assert result1 == 10
    
    result2 = wrapped[1](5)
    assert result2 == 15
    
    print("✓ wrap_all_tools() works with list")


def test_wrap_tool_objects():
    """Test wrap_all_tools() with tool objects that have .run() method."""
    print("\n=== Test: Wrap Tool Objects (.run method) ===")
    
    class SearchTool:
        def __init__(self):
            self.name = "search_tool"
        
        def run(self, query):
            return f"Search results for: {query}"
    
    class CalcTool:
        def __init__(self):
            self.name = "calc_tool"
        
        def run(self, expr):
            return eval(expr)
    
    tools = [SearchTool(), CalcTool()]
    wrapped = wrap_all_tools(tools)
    
    assert isinstance(wrapped, list)
    assert len(wrapped) == 2
    
    # .run() method should be wrapped
    assert hasattr(wrapped[0].run, "__llmobserve_wrapped__")
    assert hasattr(wrapped[1].run, "__llmobserve_wrapped__")
    
    # Test execution
    result1 = wrapped[0].run("AI")
    assert "AI" in result1
    
    result2 = wrapped[1].run("3 + 7")
    assert result2 == 10
    
    print("✓ wrap_all_tools() works with tool objects")


def test_nested_framework_tools():
    """Test that tools wrapped with wrap_all_tools() work in nested scenarios."""
    print("\n=== Test: Nested Framework Tools ===")
    
    @agent("framework_agent")
    def framework_agent():
        # Simulate framework calling tools
        def tool_a():
            assert "agent:framework_agent/tool:tool_a" in context.get_section_path()
            
            def tool_b():
                assert "tool:tool_a/tool:tool_b" in context.get_section_path()
                return "tool_b result"
            
            wrapped_b = wrap_all_tools([tool_b])[0]
            return wrapped_b()
        
        wrapped_a = wrap_all_tools([tool_a])[0]
        return wrapped_a()
    
    result = framework_agent()
    assert result == "tool_b result"
    print("✓ Framework tools work in nested scenarios")


def test_mixed_tool_types():
    """Test wrap_all_tools() with mixed types (functions + objects)."""
    print("\n=== Test: Mixed Tool Types ===")
    
    def func_tool(x):
        return x * 2
    
    class ObjectTool:
        name = "obj_tool"
        def run(self, x):
            return x + 10
    
    tools = [func_tool, ObjectTool()]
    wrapped = wrap_all_tools(tools)
    
    assert isinstance(wrapped, list)
    assert len(wrapped) == 2
    
    # Both should be wrapped
    assert hasattr(wrapped[0], "__llmobserve_wrapped__")
    assert hasattr(wrapped[1].run, "__llmobserve_wrapped__")
    
    # Test execution
    result1 = wrapped[0](5)
    assert result1 == 10
    
    result2 = wrapped[1].run(5)
    assert result2 == 15
    
    print("✓ wrap_all_tools() handles mixed types")


def test_empty_tools():
    """Test wrap_all_tools() with empty inputs."""
    print("\n=== Test: Empty Tools ===")
    
    wrapped_dict = wrap_all_tools({})
    assert isinstance(wrapped_dict, dict)
    assert len(wrapped_dict) == 0
    
    wrapped_list = wrap_all_tools([])
    assert isinstance(wrapped_list, list)
    assert len(wrapped_list) == 0
    
    print("✓ wrap_all_tools() handles empty inputs gracefully")


def run_all_tests():
    """Run all framework integration tests."""
    print("=" * 60)
    print("Framework Integration Tests")
    print("=" * 60)
    
    # Initialize SDK
    observe(
        collector_url="http://localhost:8000",
        enable_tool_wrapping=True,
        enable_http_fallback=False
    )
    
    test_wrap_dict_tools()
    test_wrap_list_tools()
    test_wrap_tool_objects()
    test_nested_framework_tools()
    test_mixed_tool_types()
    test_empty_tools()
    
    print("\n" + "=" * 60)
    print("✅ All framework integration tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()

