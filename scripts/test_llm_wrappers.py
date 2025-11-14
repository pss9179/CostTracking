"""
Test LLM wrappers for tool-calling workflows.

Tests for OpenAI and Anthropic wrappers, tool_calls extraction, and metadata.
"""
from unittest.mock import Mock, MagicMock
from llmobserve import observe, agent, tool, wrap_openai_client, wrap_anthropic_client, context


def test_openai_wrapper_basic():
    """Test OpenAI wrapper wraps client correctly."""
    print("\n=== Test: OpenAI Wrapper Basic ===")
    
    # Create mock OpenAI client
    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    
    # Mock response
    mock_response = Mock()
    mock_response.usage = Mock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.tool_calls = None
    
    mock_client.chat.completions.create = Mock(return_value=mock_response)
    
    # Wrap client
    wrapped_client = wrap_openai_client(mock_client)
    
    # Verify wrapping
    assert hasattr(wrapped_client.chat.completions, "__llmobserve_wrapped__")
    
    # Call wrapped method
    response = wrapped_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello"}]
    )
    
    # Verify response is returned unmodified
    assert response == mock_response
    assert response.usage.prompt_tokens == 100
    
    print("✓ OpenAI wrapper basic functionality works")


def test_openai_wrapper_tool_calls():
    """Test OpenAI wrapper extracts tool_calls."""
    print("\n=== Test: OpenAI Wrapper Tool Calls ===")
    
    # Create mock OpenAI client with tool_calls
    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    
    # Mock tool call
    mock_tool_call = Mock()
    mock_tool_call.id = "call_123"
    mock_tool_call.type = "function"
    mock_tool_call.function = Mock()
    mock_tool_call.function.name = "web_search"
    mock_tool_call.function.arguments = '{"query": "AI"}'
    
    mock_response = Mock()
    mock_response.usage = Mock()
    mock_response.usage.prompt_tokens = 150
    mock_response.usage.completion_tokens = 30
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.tool_calls = [mock_tool_call]
    
    mock_client.chat.completions.create = Mock(return_value=mock_response)
    
    # Wrap and call
    wrapped_client = wrap_openai_client(mock_client)
    
    @agent("test_agent")
    def test_agent():
        response = wrapped_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Search for AI"}],
            tools=[{"type": "function", "function": {"name": "web_search"}}]
        )
        return response
    
    response = test_agent()
    
    # Verify tool_calls are in response
    assert response.choices[0].message.tool_calls is not None
    assert len(response.choices[0].message.tool_calls) == 1
    assert response.choices[0].message.tool_calls[0].function.name == "web_search"
    
    print("✓ OpenAI wrapper extracts tool_calls correctly")


def test_anthropic_wrapper_basic():
    """Test Anthropic wrapper wraps client correctly."""
    print("\n=== Test: Anthropic Wrapper Basic ===")
    
    # Create mock Anthropic client
    mock_client = Mock()
    mock_client.messages = Mock()
    
    # Mock response
    mock_response = Mock()
    mock_response.usage = Mock()
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 50
    mock_response.content = [Mock()]
    mock_response.content[0].type = "text"
    mock_response.content[0].text = "Hello!"
    
    mock_client.messages.create = Mock(return_value=mock_response)
    
    # Wrap client
    wrapped_client = wrap_anthropic_client(mock_client)
    
    # Verify wrapping
    assert hasattr(wrapped_client.messages, "__llmobserve_wrapped__")
    
    # Call wrapped method
    response = wrapped_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": "Hello"}]
    )
    
    # Verify response is returned unmodified
    assert response == mock_response
    assert response.usage.input_tokens == 100
    
    print("✓ Anthropic wrapper basic functionality works")


def test_anthropic_wrapper_tool_use():
    """Test Anthropic wrapper extracts tool_use blocks."""
    print("\n=== Test: Anthropic Wrapper Tool Use ===")
    
    # Create mock Anthropic client with tool_use
    mock_client = Mock()
    mock_client.messages = Mock()
    
    # Mock tool_use block
    mock_tool_use = Mock()
    mock_tool_use.type = "tool_use"
    mock_tool_use.id = "toolu_123"
    mock_tool_use.name = "web_search"
    mock_tool_use.input = {"query": "AI agents"}
    
    mock_response = Mock()
    mock_response.usage = Mock()
    mock_response.usage.input_tokens = 150
    mock_response.usage.output_tokens = 30
    mock_response.content = [mock_tool_use]
    
    mock_client.messages.create = Mock(return_value=mock_response)
    
    # Wrap and call
    wrapped_client = wrap_anthropic_client(mock_client)
    
    @agent("test_agent")
    def test_agent():
        response = wrapped_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{"role": "user", "content": "Search for AI"}],
            tools=[{"name": "web_search", "description": "Search"}]
        )
        return response
    
    response = test_agent()
    
    # Verify tool_use is in response
    assert len(response.content) == 1
    assert response.content[0].type == "tool_use"
    assert response.content[0].name == "web_search"
    
    print("✓ Anthropic wrapper extracts tool_use correctly")


def test_double_wrapping_prevention():
    """Test that wrappers don't double-wrap."""
    print("\n=== Test: Double Wrapping Prevention ===")
    
    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    mock_client.chat.completions.create = Mock()
    
    # Wrap once
    wrapped1 = wrap_openai_client(mock_client)
    
    # Try to wrap again
    wrapped2 = wrap_openai_client(wrapped1)
    
    # Should be the same object (no double wrapping)
    assert wrapped1 is wrapped2
    
    print("✓ LLM wrappers prevent double wrapping")


def run_all_tests():
    """Run all LLM wrapper tests."""
    print("=" * 60)
    print("LLM Wrapper Tests")
    print("=" * 60)
    
    # Initialize SDK
    observe(
        collector_url="http://localhost:8000",
        enable_tool_wrapping=True,
        enable_llm_wrappers=True,
        enable_http_fallback=False
    )
    
    test_openai_wrapper_basic()
    test_openai_wrapper_tool_calls()
    test_anthropic_wrapper_basic()
    test_anthropic_wrapper_tool_use()
    test_double_wrapping_prevention()
    
    print("\n" + "=" * 60)
    print("✅ All LLM wrapper tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()

