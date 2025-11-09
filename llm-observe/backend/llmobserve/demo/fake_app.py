"""Fake app with GPT calls - no manual spans to validate auto-instrumentation."""

from llmobserve.config import settings


async def run_fake_app() -> None:
    """
    Run fake app with GPT calls that have NO manual spans.
    
    This validates that auto-instrumentation works correctly.
    """
    try:
        import openai

        client = openai.OpenAI(api_key=settings.openai_api_key)
        
        # Call 1: Simple completion
        response1 = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say hello in one sentence."},
            ],
            max_tokens=50,
        )
        
        # Call 2: Another completion
        response2 = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "What is 2+2?"},
            ],
            max_tokens=50,
        )
        
        # These calls should be auto-instrumented and appear in traces
        # without any manual span code
        
    except ImportError:
        # OpenAI not installed - skip
        pass
    except Exception as e:
        # Log but don't fail
        import structlog
        logger = structlog.get_logger()
        logger.error("Fake app error", error=str(e))

