"""Auto-instrumentation for LLM providers."""

from typing import Optional

from llmobserve.storage.repo import SpanRepository
from llmobserve.tracing.enrichers import SpanEnricher
from llmobserve.tracing.instrumentors.base import Instrumentor, InstrumentorRegistry, instrumentor_registry
from llmobserve.tracing.instrumentors.openai_instr import OpenAIInstrumentor
from llmobserve.tracing.instrumentors.genai_instr import GenAIInstrumentor
from llmobserve.tracing.instrumentors.pinecone_instr import PineconeInstrumentor, SimplePineconeInstrumentor
from llmobserve.tracing.instrumentors.anthropic_instr import AnthropicInstrumentor
from llmobserve.tracing.instrumentors.cohere_instr import CohereInstrumentor
from llmobserve.tracing.instrumentors.mistral_instr import MistralInstrumentor
from llmobserve.tracing.instrumentors.gemini_instr import GeminiInstrumentor
from llmobserve.tracing.instrumentors.xai_instr import XAIInstrumentor
from llmobserve.tracing.instrumentors.bedrock_instr import BedrockInstrumentor
from llmobserve.tracing.instrumentors.together_instr import TogetherInstrumentor
from llmobserve.tracing.instrumentors.weaviate_instr import WeaviateInstrumentor
from llmobserve.tracing.instrumentors.qdrant_instr import QdrantInstrumentor
from llmobserve.tracing.instrumentors.generic_instr import GenericInstrumentor

__all__ = [
    "Instrumentor",
    "InstrumentorRegistry",
    "instrumentor_registry",
    "instrument_all",
    "OpenAIInstrumentor",
    "GenAIInstrumentor",
    "PineconeInstrumentor",
    "SimplePineconeInstrumentor",
    "AnthropicInstrumentor",
    "CohereInstrumentor",
    "MistralInstrumentor",
    "GeminiInstrumentor",
    "XAIInstrumentor",
    "BedrockInstrumentor",
    "TogetherInstrumentor",
    "WeaviateInstrumentor",
    "QdrantInstrumentor",
    "GenericInstrumentor",
]


def instrument_all(span_repo: Optional[SpanRepository] = None) -> None:
    """
    Automatically instrument all available AI/vector SDKs.
    
    This function registers and enables instrumentation for all supported providers
    that are installed. Providers that are not installed are silently skipped.
    
    Args:
        span_repo: Optional SpanRepository for span persistence. If None, spans
                   will still be created but not persisted to database.
    
    Example:
        >>> import llmobserve  # Auto-instruments on import
        >>> # Or manually:
        >>> from llmobserve.tracing.instrumentors import instrument_all
        >>> instrument_all()
    """
    import structlog
    logger = structlog.get_logger()
    
    # Create span enricher (with or without repo)
    span_enricher = SpanEnricher(span_repo=span_repo)
    
    # Get settings to check which instrumentor to use for OpenAI
    from llmobserve.config import settings
    
    # Register instrumentors (check if SDKs are installed before registering)
    instrumentors_registered = []
    
    # OpenAI: Use GenAI instrumentor if enabled, otherwise custom
    try:
        if settings.use_genai_instrumentor:
            genai_instr = GenAIInstrumentor(span_enricher=span_enricher)
            instrumentor_registry.register(genai_instr)
            instrumentors_registered.append("GenAI (OpenAI)")
        else:
            openai_instr = OpenAIInstrumentor(span_enricher=span_enricher)
            instrumentor_registry.register(openai_instr)
            instrumentors_registered.append("OpenAI")
    except Exception as e:
        logger.debug("OpenAI instrumentor not available", error=str(e))
    
    # Anthropic
    try:
        anthropic_instr = AnthropicInstrumentor(span_enricher=span_enricher)
        instrumentor_registry.register(anthropic_instr)
        instrumentors_registered.append("Anthropic")
    except Exception:
        pass
    
    # Cohere
    try:
        cohere_instr = CohereInstrumentor(span_enricher=span_enricher)
        instrumentor_registry.register(cohere_instr)
        instrumentors_registered.append("Cohere")
    except Exception:
        pass
    
    # Mistral
    try:
        mistral_instr = MistralInstrumentor(span_enricher=span_enricher)
        instrumentor_registry.register(mistral_instr)
        instrumentors_registered.append("Mistral")
    except Exception:
        pass
    
    # Gemini
    try:
        gemini_instr = GeminiInstrumentor(span_enricher=span_enricher)
        instrumentor_registry.register(gemini_instr)
        instrumentors_registered.append("Gemini")
    except Exception:
        pass
    
    # xAI
    try:
        xai_instr = XAIInstrumentor(span_enricher=span_enricher)
        instrumentor_registry.register(xai_instr)
        instrumentors_registered.append("xAI")
    except Exception:
        pass
    
    # Bedrock
    try:
        bedrock_instr = BedrockInstrumentor(span_enricher=span_enricher)
        instrumentor_registry.register(bedrock_instr)
        instrumentors_registered.append("Bedrock")
    except Exception:
        pass
    
    # Together.ai
    try:
        together_instr = TogetherInstrumentor(span_enricher=span_enricher)
        instrumentor_registry.register(together_instr)
        instrumentors_registered.append("Together.ai")
    except Exception:
        pass
    
    # Vector Databases
    # Pinecone
    try:
        pinecone_instr = PineconeInstrumentor(span_enricher=span_enricher)
        instrumentor_registry.register(pinecone_instr)
        instrumentors_registered.append("Pinecone")
    except Exception:
        pass
    
    # Weaviate
    try:
        weaviate_instr = WeaviateInstrumentor(span_enricher=span_enricher)
        instrumentor_registry.register(weaviate_instr)
        instrumentors_registered.append("Weaviate")
    except Exception:
        pass
    
    # Qdrant
    try:
        qdrant_instr = QdrantInstrumentor(span_enricher=span_enricher)
        instrumentor_registry.register(qdrant_instr)
        instrumentors_registered.append("Qdrant")
    except Exception:
        pass
    
    # Milvus, Chroma, RedisVector (placeholders for now)
    try:
        from llmobserve.tracing.instrumentors.milvus_instr import MilvusInstrumentor
        milvus_instr = MilvusInstrumentor(span_enricher=span_enricher)
        instrumentor_registry.register(milvus_instr)
        instrumentors_registered.append("Milvus")
    except Exception:
        pass
    
    try:
        from llmobserve.tracing.instrumentors.chroma_instr import ChromaInstrumentor
        chroma_instr = ChromaInstrumentor(span_enricher=span_enricher)
        instrumentor_registry.register(chroma_instr)
        instrumentors_registered.append("Chroma")
    except Exception:
        pass
    
    try:
        from llmobserve.tracing.instrumentors.redisvector_instr import RedisVectorInstrumentor
        redisvector_instr = RedisVectorInstrumentor(span_enricher=span_enricher)
        instrumentor_registry.register(redisvector_instr)
        instrumentors_registered.append("RedisVector")
    except Exception:
        pass
    
    # Embeddings APIs (placeholders)
    try:
        from llmobserve.tracing.instrumentors.jinaai_instr import JinaAIInstrumentor
        jinaai_instr = JinaAIInstrumentor(span_enricher=span_enricher)
        instrumentor_registry.register(jinaai_instr)
        instrumentors_registered.append("JinaAI")
    except Exception:
        pass
    
    try:
        from llmobserve.tracing.instrumentors.voyageai_instr import VoyageAIInstrumentor
        voyageai_instr = VoyageAIInstrumentor(span_enricher=span_enricher)
        instrumentor_registry.register(voyageai_instr)
        instrumentors_registered.append("VoyageAI")
    except Exception:
        pass
    
    # Inference APIs (placeholders)
    try:
        from llmobserve.tracing.instrumentors.replicate_instr import ReplicateInstrumentor
        replicate_instr = ReplicateInstrumentor(span_enricher=span_enricher)
        instrumentor_registry.register(replicate_instr)
        instrumentors_registered.append("Replicate")
    except Exception:
        pass
    
    try:
        from llmobserve.tracing.instrumentors.huggingface_instr import HuggingFaceInstrumentor
        huggingface_instr = HuggingFaceInstrumentor(span_enricher=span_enricher)
        instrumentor_registry.register(huggingface_instr)
        instrumentors_registered.append("HuggingFace")
    except Exception:
        pass
    
    try:
        from llmobserve.tracing.instrumentors.deepgram_instr import DeepgramInstrumentor
        deepgram_instr = DeepgramInstrumentor(span_enricher=span_enricher)
        instrumentor_registry.register(deepgram_instr)
        instrumentors_registered.append("Deepgram")
    except Exception:
        pass
    
    try:
        from llmobserve.tracing.instrumentors.elevenlabs_instr import ElevenLabsInstrumentor
        elevenlabs_instr = ElevenLabsInstrumentor(span_enricher=span_enricher)
        instrumentor_registry.register(elevenlabs_instr)
        instrumentors_registered.append("ElevenLabs")
    except Exception:
        pass
    
    # Generic fallback instrumentor (always register as last resort)
    try:
        generic_instr = GenericInstrumentor(span_enricher=span_enricher)
        instrumentor_registry.register(generic_instr)
        instrumentors_registered.append("Generic (fallback)")
    except Exception:
        pass
    
    # Apply all registered instrumentors
    instrumentor_registry.instrument_all()
    
    logger.info(
        "Auto-instrumentation enabled",
        providers=instrumentors_registered,
        count=len(instrumentors_registered)
    )

