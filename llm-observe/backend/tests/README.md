# LLMObserve MVP Tests

Comprehensive pytest tests for the LLMObserve MVP covering the end-to-end pipeline.

## Test Coverage

### TestMiddleware
- ✅ Tenant ID extraction from headers
- ✅ Default tenant ID fallback
- ✅ Workflow ID generation

### TestLangChainHandler
- ✅ LLM end callback records cost events
- ✅ Tool end callback records tool usage
- ✅ Context propagation (tenant_id, workflow_id)

### TestOpenAIWrapper
- ✅ Chat completion cost tracking
- ✅ Embedding cost tracking
- ✅ Duration measurement
- ✅ Token usage extraction

### TestExporter
- ✅ Event batching
- ✅ Error handling

### TestAPIRoutes
- ✅ `/api/costs` endpoint
- ✅ `/api/tenants` aggregation
- ✅ `/api/workflows` aggregation
- ✅ `/api/metrics` endpoint

### TestEndToEnd
- ✅ Full pipeline: LangChain → Exporter → API
- ✅ Full pipeline: OpenAI Wrapper → Exporter → API

## Running Tests

```bash
# Install dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/test_llmobserve_mvp.py -v

# Run specific test class
pytest tests/test_llmobserve_mvp.py::TestLangChainHandler -v

# Run with coverage
pytest tests/test_llmobserve_mvp.py --cov=llmobserve --cov-report=html
```

## Test Features

- **In-memory SQLite**: Each test uses isolated in-memory database
- **Mocks**: OpenAI responses are mocked (no real API calls)
- **Fast**: Tests run quickly with minimal setup
- **Isolated**: Each test is independent with its own database

## Test Data Flow

1. **Setup**: Create in-memory SQLite database
2. **Action**: Trigger cost event (via handler/wrapper)
3. **Export**: Exporter writes to database
4. **Verify**: Query database/API to verify data

