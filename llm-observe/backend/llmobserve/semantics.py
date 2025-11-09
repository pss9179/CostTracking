"""OpenTelemetry semantic conventions for LLM observability."""

import hashlib
from typing import Optional

# LLM semantic convention attributes
LLM_PROVIDER = "llm.provider"
LLM_MODEL = "llm.model"
LLM_REQUEST_TYPE = "llm.request.type"
LLM_REQUEST_MODEL = "llm.request.model"
LLM_RESPONSE_MODEL = "llm.response.model"
LLM_USAGE_PROMPT_TOKENS = "llm.usage.prompt_tokens"
LLM_USAGE_COMPLETION_TOKENS = "llm.usage.completion_tokens"
LLM_USAGE_TOTAL_TOKENS = "llm.usage.total_tokens"
LLM_COST_USD = "llm.cost_usd"
LLM_STATUS_CODE = "llm.status_code"
LLM_TEMPERATURE = "llm.temperature"
LLM_MAX_TOKENS = "llm.max_tokens"
LLM_PROMPT_HASH = "llm.prompt.hash"
LLM_RESPONSE_HASH = "llm.response.hash"
LLM_PROMPT_CONTENT = "llm.prompt.content"
LLM_RESPONSE_CONTENT = "llm.response.content"

# Workflow attributes
WORKFLOW_TENANT_ID = "workflow.tenant_id"
WORKFLOW_USER_ID = "workflow.user_id"
WORKFLOW_AGENT_ID = "workflow.agent_id"
WORKFLOW_NAME = "workflow.name"

# Standard OpenTelemetry attributes
ATTR_HTTP_METHOD = "http.method"
ATTR_HTTP_STATUS_CODE = "http.status_code"
ATTR_HTTP_ROUTE = "http.route"
ATTR_SERVICE_NAME = "service.name"
ATTR_SERVICE_VERSION = "service.version"

# API semantic convention attributes (for Pinecone, etc.)
API_PROVIDER = "api.provider"
API_OPERATION = "api.operation"
API_LATENCY_MS = "api.latency_ms"
API_REQUEST_SIZE = "api.request_size"
API_COST_USD = "api.cost_usd"

# Span names
SPAN_NAME_LLM_REQUEST = "llm.request"
SPAN_NAME_AGENT_WORKFLOW = "agent.workflow"
SPAN_NAME_TOOL_CALL = "tool.call"


def hash_content(content: str) -> str:
    """Generate SHA-256 hash of content for privacy."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def hash_prompt(messages: list[dict]) -> str:
    """Hash prompt messages for privacy."""
    # Extract text content from messages
    text_parts = []
    for msg in messages:
        if isinstance(msg, dict):
            role = msg.get("role", "")
            content = msg.get("content", "")
            if content:
                text_parts.append(f"{role}:{content}")
        else:
            text_parts.append(str(msg))
    combined = "|".join(text_parts)
    return hash_content(combined)


def hash_response(content: str) -> str:
    """Hash response content for privacy."""
    return hash_content(content)

