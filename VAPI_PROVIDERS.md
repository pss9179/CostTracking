# Vapi Supported Providers

Complete list of providers Vapi supports for each component of voice AI agents.

**Important:** Vapi supports **ALL models** from each provider. This means you can use any model available from these providers, not just a limited subset.

## 🎤 STT (Speech-to-Text) Providers

Vapi supports **10 STT providers** with access to all their models:

| Provider | All Models Supported | Notes |
|----------|---------------------|-------|
| **Assembly AI** | ✅ All AssemblyAI models | Full AssemblyAI API access |
| **Azure** | ✅ All Azure Speech models | Microsoft Azure Speech-to-Text |
| **Deepgram** | ✅ All Deepgram models (Nova 3, Nova 2, etc.) | Primary transcription provider |
| **ElevenLabs** | ✅ All Scribe models | ElevenLabs STT (Scribe v1, v2, etc.) |
| **Gladia** | ✅ Fast, Accurate, Solaria | Gladia transcription API |
| **Google** | ✅ Gemini 2.0 Flash, Gemini 2.0 Flash Lite, Gemini 1.5 Pro | Uses Gemini multimodal (NOT Speech-to-Text V1/V2) - audio token pricing |
| **OpenAI** | ✅ All Whisper models | OpenAI Whisper API |
| **Speechmatics** | ✅ All Speechmatics models | Speechmatics transcription |
| **Talkscriber** | ✅ All Talkscriber models | Talkscriber transcription |
| **Cartesia** | ✅ All Ink models | Cartesia Ink STT |

## 🧠 LLM (Language Model) Providers

Vapi supports **16 LLM providers** with access to all their models:

| Provider | All Models Supported | Notes |
|----------|---------------------|-------|
| **OpenAI** | ✅ All OpenAI models | GPT-4, GPT-3.5, GPT-4o, etc. |
| **Azure OpenAI** | ✅ All Azure OpenAI models | Custom rate limits, regional deployments |
| **Anthropic** | ✅ All Claude models | Claude 3.5 Sonnet, Opus, Haiku, etc. |
| **Google** | ✅ All Gemini models | Gemini Pro, Flash, etc. |
| **Custom LLM** | ✅ Any OpenAI-compatible | Bring your own server/endpoint |
| **Groq** | ✅ All Groq models | Fast inference models |
| **Cerebras** | ✅ All Cerebras models | High-performance models |
| **Deep Seek** | ✅ All Deep Seek models | Deep learning models |
| **XAI** | ✅ All xAI models | Grok models |
| **Mistral** | ✅ All Mistral models | Mistral AI models |
| **Perplexity AI** | ✅ All Perplexity models | Perplexity API models |
| **Together AI** | ✅ All Together AI models | Together AI inference |
| **Anyscale** | ✅ All Anyscale models | Anyscale API |
| **OpenRouter** | ✅ 100+ models via OpenRouter | Access to multiple providers |
| **Deepinfra** | ✅ All DeepInfra models | DeepInfra inference |
| **Inflection AI** | ✅ All Inflection models | Inflection Pi models |

## 🔊 TTS (Text-to-Speech) Providers

Vapi supports **13 TTS providers** with access to all their voices:

| Provider | All Voices Supported | Notes |
|----------|---------------------|-------|
| **Vapi** | ✅ All Vapi voices | Vapi's default voice library |
| **Cartesia** | ✅ All Cartesia voices | Sonic voices (all models) |
| **ElevenLabs** | ✅ All ElevenLabs voices | Premium voices, cloning (29+ languages) |
| **Rime AI** | ✅ All Rime voices | Fast, affordable voices |
| **LMNT** | ✅ All LMNT voices | LMNT voice synthesis |
| **Deepgram** | ✅ All Deepgram voices | Aura voices (STT + TTS provider) |
| **OpenAI** | ✅ All OpenAI TTS models | TTS-1, TTS-1-HD, etc. |
| **Azure** | ✅ 400+ Azure voices | Microsoft Azure Speech (140+ languages) |
| **MiniMax** | ✅ All MiniMax voices | MiniMax voice synthesis |
| **Neuphonic** | ✅ All Neuphonic voices | Neuphonic voice library |
| **Smallest AI** | ✅ All Smallest AI voices | Smallest AI voice models |
| **Hume** | ✅ All Hume voices | Hume voice synthesis |
| **Inworld** | ✅ All Inworld voices | Inworld voice library |

## 📞 Telephony Providers

| Provider | Type | Notes |
|----------|------|-------|
| **Twilio** | Programmable Voice | Default telephony (via transport cost) |
| **Vonage** | Voice API | Alternative telephony option |
| **Plivo** | SIP Trunking | SIP integration |
| **Telnyx** | SIP Trunking | SIP integration |
| **Zadarma** | SIP Trunking | SIP integration |
| **Custom SIP** | BYO Trunk | Bring your own SIP infrastructure |

## ☁️ Cloud Storage Providers

| Provider | Use Case | Notes |
|----------|----------|-------|
| **Cloudflare R2** | Default | Vapi's default storage |
| **AWS S3** | Custom storage | Bring your own bucket |
| **Google Cloud Platform** | Custom storage | Bring your own bucket |

## 📊 How Vapi Tracks Costs

Vapi provides a `costBreakdown` object in call responses with:

```json
{
  "stt": 0.0043,              // STT cost (any STT provider)
  "llm": 0.05,                // LLM cost (any LLM provider)
  "tts": 0.02,                // TTS cost (any TTS provider)
  "transport": 0.014,         // Telephony cost (Twilio/Vonage)
  "vapi": 0.01,               // Vapi platform fee
  "total": 0.0983,            // Total cost
  "llmPromptTokens": 150,     // LLM input tokens
  "llmCompletionTokens": 200, // LLM output tokens
  "ttsCharacters": 500        // TTS characters generated
}
```

**Key Point:** Vapi aggregates costs regardless of which specific provider/model you use. The `costBreakdown` shows the total cost for each segment (STT, LLM, TTS, telephony), making it easy to track costs even when mixing providers.

## 🔑 Provider Key Configuration

Users can configure their own API keys for:
- **STT providers**: All 10 providers listed above
- **LLM providers**: All 16 providers listed above (or use Vapi's keys)
- **TTS providers**: All 13 providers listed above
- **Telephony providers**: SIP trunks (Plivo, Telnyx, Zadarma, custom)

Keys are validated through the Vapi Dashboard and then used for cost calculation.

## 📝 Important Notes

- **All Models Supported**: Vapi supports **ALL models** from each provider, not just a subset. This means you can use any model available from OpenAI, Anthropic, Deepgram, etc.

- **Default Telephony**: Vapi uses Twilio/Vonage by default (tracked as "transport" cost)

- **Custom Models**: Any OpenAI-compatible endpoint can be used for LLM via "Custom LLM" option

- **Voice IDs**: Once API keys are validated, any voice ID from the provider can be used

- **Multilingual**: Most providers support multiple languages (check each provider's documentation)

- **Cost Tracking**: Our `vapi_instrumentor.py` extracts the `costBreakdown` from Vapi's API, which automatically includes costs for whichever provider/model you use. No need to track individual providers separately.

## 🎯 Total Provider Count

- **STT Providers**: 10
- **LLM Providers**: 16  
- **TTS Providers**: 13
- **Telephony Providers**: 6
- **Storage Providers**: 3

**Total: 48+ provider integrations** across all categories.
