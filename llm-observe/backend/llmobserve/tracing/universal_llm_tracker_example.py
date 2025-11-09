"""
Example usage of universal_llm_tracker.

This demonstrates how to use track_llm_call() with different providers.
"""

import asyncio
from llmobserve.tracing.universal_llm_tracker import track_llm_call


async def example_openai():
    """Example with OpenAI streaming."""
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI()
        
        result = await track_llm_call(
            provider="openai",
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Write a haiku about startups"}],
            client=client,
            stream=True
        )
        
        print(f"Cost: ${result['cost_usd']:.6f}")
        print(f"Tokens: {result['total_tokens']} ({result['prompt_tokens']} prompt + {result['completion_tokens']} completion)")
        print(f"Error: {result['error']}")
        
    except ImportError:
        print("OpenAI not installed")


async def example_anthropic():
    """Example with Anthropic non-streaming."""
    try:
        from anthropic import AsyncAnthropic
        
        client = AsyncAnthropic()
        
        result = await track_llm_call(
            provider="anthropic",
            model="claude-3-5-sonnet",
            messages=[{"role": "user", "content": "Explain quantum computing"}],
            client=client,
            stream=False
        )
        
        print(f"Cost: ${result['cost_usd']:.6f}")
        print(f"Tokens: {result['total_tokens']}")
        
    except ImportError:
        print("Anthropic not installed")


async def main():
    """Run examples."""
    print("=== OpenAI Example ===")
    await example_openai()
    
    print("\n=== Anthropic Example ===")
    await example_anthropic()


if __name__ == "__main__":
    asyncio.run(main())

