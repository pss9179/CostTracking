"""Tool implementations that call GPT (auto-instrumented)."""

import os
from typing import Optional

from llmobserve.config import settings
from llmobserve.tracing.otel_setup import get_tracer

tracer = get_tracer(__name__)


async def tool_search(query: str) -> str:
    """
    Search tool that calls GPT to simulate search results.
    
    This function calls GPT without manual spans - auto-instrumentation
    should capture it automatically.
    """
    try:
        import openai

        client = openai.OpenAI(api_key=settings.openai_api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a search assistant. Provide concise search results."},
                {"role": "user", "content": f"Search for: {query}"},
            ],
            max_tokens=100,
        )
        
        return response.choices[0].message.content
    except ImportError:
        return f"[Mock search result for: {query}]"
    except Exception as e:
        return f"[Search error: {str(e)}]"


async def tool_reason(question: str, context: str) -> str:
    """
    Reasoning tool that calls GPT to answer questions.
    
    This function calls GPT without manual spans - auto-instrumentation
    should capture it automatically.
    """
    try:
        import openai

        client = openai.OpenAI(api_key=settings.openai_api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a reasoning assistant. Provide clear, logical answers."},
                {"role": "user", "content": f"Question: {question}\n\nContext: {context}"},
            ],
            max_tokens=150,
        )
        
        return response.choices[0].message.content
    except ImportError:
        return f"[Mock reasoning for: {question}]"
    except Exception as e:
        return f"[Reasoning error: {str(e)}]"

