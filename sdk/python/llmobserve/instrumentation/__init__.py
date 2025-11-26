"""
Modular instrumentation registry for llmobserve.

Provides auto-instrumentation for various LLM and API libraries
with version guards, fail-open safety, and modular design.
"""
import logging
from typing import Optional, List, Dict, Callable

logger = logging.getLogger("llmobserve")

# Registry of available instrumentors
INSTRUMENTOR_REGISTRY: Dict[str, Callable[[], bool]] = {}

# Track which libraries have been instrumented
_instrumented: Dict[str, bool] = {}

# Global initialization guard (prevents double initialization)
_global_initialized = False


def register_instrumentor(name: str, instrumentor_func: Callable[[], bool]) -> None:
    """
    Register an instrumentor function.
    
    Args:
        name: Library name (e.g., "openai", "pinecone")
        instrumentor_func: Function that returns True on success, False on failure
    """
    INSTRUMENTOR_REGISTRY[name] = instrumentor_func


def auto_instrument(libs: Optional[List[str]] = None) -> Dict[str, bool]:
    """
    Auto-instrument specified libraries (or all registered if None).
    
    Idempotent: can be called multiple times safely.
    
    Args:
        libs: List of library names to instrument (e.g., ["openai", "pinecone"]).
              If None, instruments all registered libraries.
    
    Returns:
        Dict mapping library name to success status (True/False)
    
    Example:
        >>> from llmobserve.instrumentation import auto_instrument
        >>> results = auto_instrument(libs=["openai", "pinecone"])
        >>> # {'openai': True, 'pinecone': True}
    """
    global _global_initialized
    
    if libs is None:
        # Instrument all registered libraries
        libs = list(INSTRUMENTOR_REGISTRY.keys())
    
    results = {}
    
    for lib_name in libs:
        if lib_name not in INSTRUMENTOR_REGISTRY:
            logger.warning(
                f"[llmobserve] Unknown library '{lib_name}'. "
                f"Available: {list(INSTRUMENTOR_REGISTRY.keys())}"
            )
            results[lib_name] = False
            continue
        
        if _instrumented.get(lib_name, False):
            logger.debug(f"[llmobserve] {lib_name} already instrumented, skipping")
            results[lib_name] = True
            continue
        
        instrumentor_func = INSTRUMENTOR_REGISTRY[lib_name]
        
        try:
            success = instrumentor_func()
            _instrumented[lib_name] = success
            results[lib_name] = success
            
            if success:
                logger.info(f"[llmobserve] ✓ Successfully instrumented {lib_name}")
            else:
                logger.warning(f"[llmobserve] ✗ Failed to instrument {lib_name} (check logs)")
        except Exception as e:
            logger.error(
                f"[llmobserve] ✗ Error instrumenting {lib_name}: {e}",
                exc_info=True
            )
            results[lib_name] = False
            # Fail-open: continue with other libraries
    
    # Mark as globally initialized
    _global_initialized = True
    
    return results


def is_instrumented(lib_name: str) -> bool:
    """Check if a library has been instrumented."""
    return _instrumented.get(lib_name, False)


def is_initialized() -> bool:
    """Check if instrumentation has been initialized globally."""
    return _global_initialized


# Import and register instrumentors
# NOTE: OpenAI and Pinecone are DISABLED - all API calls route through proxy instead
# This prevents monkey-patching from breaking when SDKs update
# Proxy provides universal coverage without SDK-specific code

# OpenAI and Pinecone removed - use proxy instead
# try:
#     from llmobserve.instrumentation.openai_instrumentor import instrument_openai
#     register_instrumentor("openai", instrument_openai)
# except ImportError:
#     logger.debug("[llmobserve] OpenAI instrumentor not available")

# try:
#     from llmobserve.instrumentation.pinecone_instrumentor import instrument_pinecone
#     register_instrumentor("pinecone", instrument_pinecone)
# except ImportError:
#     logger.debug("[llmobserve] Pinecone instrumentor not available")

# LLM Providers
try:
    from llmobserve.instrumentation.anthropic_instrumentor import instrument_anthropic
    register_instrumentor("anthropic", instrument_anthropic)
except ImportError:
    logger.debug("[llmobserve] Anthropic instrumentor not available")

try:
    from llmobserve.instrumentation.google_instrumentor import instrument_google
    register_instrumentor("google", instrument_google)
except ImportError:
    logger.debug("[llmobserve] Google instrumentor not available")

try:
    from llmobserve.instrumentation.cohere_instrumentor import instrument_cohere
    register_instrumentor("cohere", instrument_cohere)
except ImportError:
    logger.debug("[llmobserve] Cohere instrumentor not available")

# Voice AI - TTS
try:
    from llmobserve.instrumentation.elevenlabs_instrumentor import instrument_elevenlabs
    register_instrumentor("elevenlabs", instrument_elevenlabs)
except ImportError:
    logger.debug("[llmobserve] ElevenLabs instrumentor not available")

# Voice AI - STT
try:
    from llmobserve.instrumentation.deepgram_instrumentor import instrument_deepgram
    register_instrumentor("deepgram", instrument_deepgram)
except ImportError:
    logger.debug("[llmobserve] Deepgram instrumentor not available")

# Voice AI - Full Platforms
try:
    from llmobserve.instrumentation.retell_instrumentor import instrument_retell
    register_instrumentor("retell", instrument_retell)
except ImportError:
    logger.debug("[llmobserve] Retell instrumentor not available")

try:
    from llmobserve.instrumentation.vapi_instrumentor import instrument_vapi
    register_instrumentor("vapi", instrument_vapi)
except ImportError:
    logger.debug("[llmobserve] Vapi instrumentor not available")

try:
    from llmobserve.instrumentation.livekit_instrumentor import instrument_livekit
    register_instrumentor("livekit", instrument_livekit)
except ImportError:
    logger.debug("[llmobserve] LiveKit instrumentor not available")

try:
    from llmobserve.instrumentation.bland_instrumentor import instrument_bland
    register_instrumentor("bland", instrument_bland)
except ImportError:
    logger.debug("[llmobserve] Bland AI instrumentor not available")

# Voice AI - STT
try:
    from llmobserve.instrumentation.assemblyai_instrumentor import instrument_assemblyai
    register_instrumentor("assemblyai", instrument_assemblyai)
except ImportError:
    logger.debug("[llmobserve] AssemblyAI instrumentor not available")

try:
    from llmobserve.instrumentation.openai_realtime_instrumentor import instrument_openai_realtime
    register_instrumentor("openai_realtime", instrument_openai_realtime)
except ImportError:
    logger.debug("[llmobserve] OpenAI Realtime instrumentor not available")

# Embeddings
try:
    from llmobserve.instrumentation.voyage_instrumentor import instrument_voyage
    register_instrumentor("voyage", instrument_voyage)
except ImportError:
    logger.debug("[llmobserve] Voyage AI instrumentor not available")

# Payment Processing
try:
    from llmobserve.instrumentation.stripe_instrumentor import instrument_stripe
    register_instrumentor("stripe", instrument_stripe)
except ImportError:
    logger.debug("[llmobserve] Stripe instrumentor not available")

# Communication - Telephony
try:
    from llmobserve.instrumentation.twilio_instrumentor import instrument_twilio
    register_instrumentor("twilio", instrument_twilio)
except ImportError:
    logger.debug("[llmobserve] Twilio instrumentor not available")

try:
    from llmobserve.instrumentation.vonage_instrumentor import instrument_vonage
    register_instrumentor("vonage", instrument_vonage)
except ImportError:
    logger.debug("[llmobserve] Vonage instrumentor not available")

try:
    from llmobserve.instrumentation.telnyx_instrumentor import instrument_telnyx
    register_instrumentor("telnyx", instrument_telnyx)
except ImportError:
    logger.debug("[llmobserve] Telnyx instrumentor not available")

# Voice AI - Additional TTS Providers
try:
    from llmobserve.instrumentation.cartesia_instrumentor import instrument_cartesia
    register_instrumentor("cartesia", instrument_cartesia)
except ImportError:
    logger.debug("[llmobserve] Cartesia instrumentor not available")

try:
    from llmobserve.instrumentation.playht_instrumentor import instrument_playht
    register_instrumentor("playht", instrument_playht)
except ImportError:
    logger.debug("[llmobserve] PlayHT instrumentor not available")

try:
    from llmobserve.instrumentation.rime_instrumentor import instrument_rime
    register_instrumentor("rime", instrument_rime)
except ImportError:
    logger.debug("[llmobserve] Rime instrumentor not available")

try:
    from llmobserve.instrumentation.azure_speech_instrumentor import instrument_azure_speech
    register_instrumentor("azure_speech", instrument_azure_speech)
except ImportError:
    logger.debug("[llmobserve] Azure Speech instrumentor not available")

try:
    from llmobserve.instrumentation.gladia_instrumentor import instrument_gladia
    register_instrumentor("gladia", instrument_gladia)
except ImportError:
    logger.debug("[llmobserve] Gladia instrumentor not available")

try:
    from llmobserve.instrumentation.google_stt_instrumentor import instrument_google_stt
    register_instrumentor("google_stt", instrument_google_stt)
except ImportError:
    logger.debug("[llmobserve] Google STT instrumentor not available")

try:
    from llmobserve.instrumentation.speechmatics_instrumentor import instrument_speechmatics
    register_instrumentor("speechmatics", instrument_speechmatics)
except ImportError:
    logger.debug("[llmobserve] Speechmatics instrumentor not available")

