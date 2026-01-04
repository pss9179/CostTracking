"""
Universal provider detection and response parsing.

Supports 37+ AI/API providers with automatic cost calculation.
"""
from typing import Dict, Optional, Any
import json


def detect_provider(url: str) -> str:
    """
    Detect provider from URL - NOW SUPPORTS 37+ APIS!
    
    Args:
        url: The target API URL
    
    Returns:
        Provider name (e.g., "openai", "anthropic", "google")
    """
    url_lower = url.lower()
    
    # LLM Providers (13)
    if "api.openai.com" in url_lower:
        return "openai"
    elif "api.anthropic.com" in url_lower:
        return "anthropic"
    elif "generativelanguage.googleapis.com" in url_lower or "aiplatform.googleapis.com" in url_lower:
        return "google"
    elif "api.cohere.ai" in url_lower or "api.cohere.com" in url_lower:
        return "cohere"
    elif "api.mistral.ai" in url_lower:
        return "mistral"
    elif "api.groq.com" in url_lower:
        return "groq"
    elif "api.ai21.com" in url_lower:
        return "ai21"
    elif "api-inference.huggingface.co" in url_lower:
        return "huggingface"
    elif "api.together.xyz" in url_lower or "together.ai" in url_lower:
        return "together"
    elif "api.replicate.com" in url_lower:
        return "replicate"
    elif "api.perplexity.ai" in url_lower:
        return "perplexity"
    elif "openai.azure.com" in url_lower:
        return "azure_openai"
    elif ("bedrock-runtime" in url_lower or "bedrock" in url_lower) and "amazonaws.com" in url_lower:
        return "aws_bedrock"
    elif "openrouter.ai" in url_lower:
        return "openrouter"
    
    # Voice AI (7)
    elif "api.elevenlabs.io" in url_lower:
        return "elevenlabs"
    elif "api.assemblyai.com" in url_lower:
        return "assemblyai"
    elif "api.deepgram.com" in url_lower:
        return "deepgram"
    elif "play.ht" in url_lower or "api.play.ai" in url_lower:
        return "playht"
    elif "speech.platform.bing.com" in url_lower or ("cognitiveservices.azure.com" in url_lower and "speech" in url_lower):
        return "azure_speech"
    elif "polly" in url_lower and "amazonaws.com" in url_lower:
        return "aws_polly"
    elif "transcribe" in url_lower and "amazonaws.com" in url_lower:
        return "aws_transcribe"
    
    # Embeddings
    elif "api.voyageai.com" in url_lower:
        return "voyage"
    
    # Images/Video (4)
    elif "api.stability.ai" in url_lower:
        return "stability"
    elif "api.runwayml.com" in url_lower:
        return "runway"
    elif "rekognition" in url_lower and "amazonaws.com" in url_lower:
        return "aws_rekognition"
    
    # Vector Databases (8)
    elif "pinecone.io" in url_lower:
        return "pinecone"
    elif "weaviate" in url_lower:
        return "weaviate"
    elif "qdrant" in url_lower:
        return "qdrant"
    elif "milvus" in url_lower or "zilliz" in url_lower:
        return "milvus"
    elif "trychroma.com" in url_lower or "chromadb" in url_lower:
        return "chroma"
    elif ("mongodb.com" in url_lower or "mongodb.net" in url_lower) and ("vector" in url_lower or "search" in url_lower):
        return "mongodb"
    elif "redis" in url_lower and "vector" in url_lower:
        return "redis"
    elif ("elastic" in url_lower or "elasticsearch" in url_lower) and "vector" in url_lower:
        return "elasticsearch"
    
    # Search (1)
    elif "algolia" in url_lower:
        return "algolia"
    
    # Payment Processing (2)
    elif "api.stripe.com" in url_lower:
        return "stripe"
    elif "api.paypal.com" in url_lower or ("paypal.com" in url_lower and "/v1/" in url_lower):
        return "paypal"
    
    # Communication (2)
    elif "api.twilio.com" in url_lower:
        return "twilio"
    elif "api.sendgrid.com" in url_lower:
        return "sendgrid"
    
    # Database/Backend (1)
    elif "supabase.co" in url_lower:
        return "supabase"
    
    else:
        return "unknown"


def extract_endpoint(url: str, method: str = "POST") -> str:
    """Extract API endpoint from URL."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = parsed.path
        
        # Check for GraphQL endpoints
        if "graphql" in path.lower() or path.endswith("/graphql") or path.endswith("/gql"):
            return "graphql"
        
        # Extract meaningful endpoint
        if "/v1/" in path:
            endpoint = path.split("/v1/")[1]
        elif "/api/" in path:
            endpoint = path.split("/api/")[1]
        else:
            endpoint = path.strip("/")
        
        # Simplify common endpoints
        if "chat/completions" in endpoint:
            return "chat.completions.create"
        elif "completions" in endpoint:
            return "completions.create"
        elif "embeddings" in endpoint:
            return "embeddings.create"
        elif "messages" in endpoint:
            return "messages.create"
        
        return endpoint or "unknown"
    except:
        return "unknown"


def parse_usage(provider: str, response_body: Dict[str, Any], request_body: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Extract usage information from API response.
    
    Args:
        provider: Provider name (from detect_provider)
        response_body: Parsed JSON response
        request_body: Parsed JSON request (optional, for fallback estimation)
    
    Returns:
        Dict with keys: model, input_tokens, output_tokens, character_count, etc.
    """
    usage = {
        "model": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "cached_tokens": 0,
        "character_count": 0,
        "audio_seconds": 0.0,
        "image_count": 0,
        "operation_count": 0,
        "transaction_amount": 0.0,
    }
    
    try:
        if provider == "openai":
            usage["model"] = response_body.get("model")
            usage_data = response_body.get("usage", {})
            usage["input_tokens"] = usage_data.get("prompt_tokens", 0)
            usage["output_tokens"] = usage_data.get("completion_tokens", 0)
            usage["cached_tokens"] = usage_data.get("prompt_tokens_details", {}).get("cached_tokens", 0)
            # Subtract cached tokens from input tokens (they're counted separately)
            usage["input_tokens"] = usage["input_tokens"] - usage["cached_tokens"]
        
        elif provider == "anthropic":
            usage["model"] = response_body.get("model")
            usage_data = response_body.get("usage", {})
            usage["input_tokens"] = usage_data.get("input_tokens", 0)
            usage["output_tokens"] = usage_data.get("output_tokens", 0)
        
        elif provider == "google":
            usage["model"] = response_body.get("model", "gemini-1.5-flash")
            usage_metadata = response_body.get("usageMetadata", {})
            usage["input_tokens"] = usage_metadata.get("promptTokenCount", 0)
            usage["output_tokens"] = usage_metadata.get("candidatesTokenCount", 0)
        
        elif provider == "cohere":
            usage["model"] = response_body.get("model", "command")
            meta = response_body.get("meta", {})
            billed = meta.get("billed_units", {})
            usage["input_tokens"] = billed.get("input_tokens", 0)
            usage["output_tokens"] = billed.get("output_tokens", 0)
        
        elif provider == "mistral":
            usage["model"] = response_body.get("model")
            usage_data = response_body.get("usage", {})
            usage["input_tokens"] = usage_data.get("prompt_tokens", 0)
            usage["output_tokens"] = usage_data.get("completion_tokens", 0)
        
        elif provider == "groq":
            usage["model"] = response_body.get("model")
            usage_data = response_body.get("usage", {})
            usage["input_tokens"] = usage_data.get("prompt_tokens", 0)
            usage["output_tokens"] = usage_data.get("completion_tokens", 0)
        
        elif provider == "openrouter":
            # OpenRouter uses OpenAI-compatible API format
            usage["model"] = response_body.get("model")
            usage_data = response_body.get("usage", {})
            usage["input_tokens"] = usage_data.get("prompt_tokens", 0)
            usage["output_tokens"] = usage_data.get("completion_tokens", 0)
            # OpenRouter also provides cost in response
            if "cost" in response_body:
                usage["cost_usd"] = response_body.get("cost")
        
        elif provider == "voyage":
            usage["model"] = response_body.get("model", "voyage-2")
            usage["input_tokens"] = response_body.get("total_tokens", 0)
        
        elif provider == "elevenlabs":
            # Estimate from request
            if request_body:
                text = request_body.get("text", "")
                usage["character_count"] = len(text)
            usage["model"] = request_body.get("model_id") if request_body else "eleven_multilingual_v2"
        
        elif provider == "assemblyai":
            usage["audio_seconds"] = response_body.get("audio_duration", 0)
            usage["model"] = "base"  # AssemblyAI model
        
        elif provider == "deepgram":
            metadata = response_body.get("metadata", {})
            usage["audio_seconds"] = metadata.get("duration", 0)
            usage["model"] = request_body.get("model") if request_body else "nova-2"
        
        elif provider == "stripe":
            # Estimate from request
            if request_body:
                amount_cents = request_body.get("amount", 0)
                usage["transaction_amount"] = amount_cents / 100.0
            usage["model"] = "transaction"
        
        elif provider == "twilio":
            # Cost from response
            price = response_body.get("price")
            if price:
                usage["transaction_amount"] = abs(float(price))
            usage["model"] = "sms" if "messages" in str(request_body) else "voice"
        
        elif provider == "pinecone":
            # Count operations based on endpoint type
            # ALWAYS set operation_count to at least 1 (each API call is 1 operation)
            usage["operation_count"] = 1
            
            if request_body:
                # For upsert operations - count vectors
                vectors = request_body.get("vectors", [])
                if isinstance(vectors, list) and len(vectors) > 0:
                    usage["operation_count"] = len(vectors)
                elif isinstance(vectors, dict):
                    vectors_list = vectors.get("vectors", [])
                    if isinstance(vectors_list, list) and len(vectors_list) > 0:
                        usage["operation_count"] = len(vectors_list)
                # For query operations - already set to 1 above
                # For list/fetch operations - already set to 1 above
            
            usage["model"] = "serverless"
        
        elif provider == "weaviate" or provider == "qdrant" or provider == "milvus":
            # Count operations from request
            if request_body:
                if isinstance(request_body, list):
                    usage["operation_count"] = len(request_body)
                elif isinstance(request_body, dict):
                    usage["operation_count"] = len(request_body.get("points", []) or request_body.get("vectors", []))
            usage["model"] = "standard"
        
        # Add more providers as needed...
    
    except Exception as e:
        # Fail silently
        pass
    
    return usage

